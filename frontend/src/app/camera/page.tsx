'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import {
  Camera,
  CameraOff,
  Maximize2,
  Minimize2,
  Settings,
  Wifi,
  WifiOff,
  Play,
  Pause,
  Eye,
  EyeOff,
  Activity,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';

type CameraMode = 'webcam' | 'ip';

interface TrackedAnimal {
  track_id: number;
  animal_id: string;
  class_name: string;
  bbox: number[];
  confidence: number;
  re_id_confidence: number;
  is_identified: boolean;
  velocity: [number, number];
  direction: number;
  health_score: number | null;
  behavior: string | null;
}

interface DetectionResult {
  frame_id: number;
  timestamp: number;
  fps: number;
  animal_count: number;
  animals: TrackedAnimal[];
  frame_size: [number, number];
}

// Sınıf renk paleti
const CLASS_COLORS: Record<string, string> = {
  cow: '#22c55e',
  cattle: '#22c55e',
  sheep: '#f97316',
  goat: '#d946ef',
  horse: '#3b82f6',
  chicken: '#eab308',
  bird: '#eab308',
  dog: '#ef4444',
  cat: '#8b5cf6',
  person: '#06b6d4',
  default: '#06b6d4',
};

export default function CameraPage() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // AI Detection State
  const [aiEnabled, setAiEnabled] = useState(true);
  const [detectionResult, setDetectionResult] = useState<DetectionResult | null>(null);
  const [backendConnected, setBackendConnected] = useState(false);
  const [showLabels, setShowLabels] = useState(true);
  const [showBboxes, setShowBboxes] = useState(true);
  const [processingFps, setProcessingFps] = useState(5);
  const [isProcessing, setIsProcessing] = useState(false);
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const processingRef = useRef<NodeJS.Timeout | null>(null);

  // Backend URL
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'https://ai-animal-tracking-api.onrender.com';

  // Backend bağlantısını kontrol et
  const checkBackend = useCallback(async () => {
    try {
      const response = await fetch(`${backendUrl}/health`, { 
        method: 'GET',
        headers: { 'Accept': 'application/json' }
      });
      if (response.ok) {
        setBackendConnected(true);
        setError(null);
        return true;
      }
    } catch (e) {
      console.log('Backend not available:', e);
    }
    setBackendConnected(false);
    return false;
  }, [backendUrl]);

  // Sayfa yüklendiğinde backend'i kontrol et
  useEffect(() => {
    checkBackend();
  }, [checkBackend]);

  // Frame gönder ve sonuç al (HTTP Polling)
  const processFrame = useCallback(async () => {
    if (!videoRef.current || !canvasRef.current || !aiEnabled || isProcessing) return;
    if (!backendConnected) return;
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    if (!ctx || video.videoWidth === 0) return;
    
    setIsProcessing(true);
    
    try {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.drawImage(video, 0, 0);
      
      const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
      
      const response = await fetch(`${backendUrl}/api/v1/detection/process-frame`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ frame: dataUrl })
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.result) {
          setDetectionResult(data.result as DetectionResult);
        }
      }
    } catch (e) {
      console.error('Frame processing error:', e);
    } finally {
      setIsProcessing(false);
    }
  }, [aiEnabled, backendConnected, backendUrl, isProcessing]);

  // Start webcam
  const startWebcam = useCallback(async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'environment' },
        audio: false,
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        setIsStreaming(true);
        
        const isBackendUp = await checkBackend();
        
        if (aiEnabled && isBackendUp) {
          if (processingRef.current) clearInterval(processingRef.current);
          processingRef.current = setInterval(processFrame, 1000 / processingFps);
        }
      }
    } catch (err) {
      console.error('Webcam error:', err);
      setError('Kamera erişimi reddedildi veya kamera bulunamadı');
    }
  }, [aiEnabled, checkBackend, processFrame, processingFps]);

  // Stop webcam
  const stopWebcam = useCallback(() => {
    if (videoRef.current?.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    
    if (processingRef.current) {
      clearInterval(processingRef.current);
      processingRef.current = null;
    }
    
    setIsStreaming(false);
    setDetectionResult(null);
  }, []);

  // AI toggle
  useEffect(() => {
    if (isStreaming) {
      if (aiEnabled && backendConnected) {
        if (processingRef.current) clearInterval(processingRef.current);
        processingRef.current = setInterval(processFrame, 1000 / processingFps);
      } else {
        if (processingRef.current) {
          clearInterval(processingRef.current);
          processingRef.current = null;
        }
        setDetectionResult(null);
      }
    }
  }, [aiEnabled, isStreaming, backendConnected, processFrame, processingFps]);

  useEffect(() => {
    return () => { stopWebcam(); };
  }, [stopWebcam]);

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  const renderBoundingBoxes = () => {
    if (!detectionResult || !showBboxes) return null;
    const videoEl = videoRef.current;
    if (!videoEl) return null;
    
    const videoRect = videoEl.getBoundingClientRect();
    const scaleX = videoRect.width / (detectionResult.frame_size[0] || 1);
    const scaleY = videoRect.height / (detectionResult.frame_size[1] || 1);
    
    return detectionResult.animals.map((animal) => {
      const [x1, y1, x2, y2] = animal.bbox;
      const color = CLASS_COLORS[animal.class_name.toLowerCase()] || CLASS_COLORS.default;
      
      return (
        <div
          key={animal.track_id}
          className="absolute pointer-events-none"
          style={{
            left: x1 * scaleX,
            top: y1 * scaleY,
            width: (x2 - x1) * scaleX,
            height: (y2 - y1) * scaleY,
            border: `3px solid ${color}`,
            borderRadius: '4px',
          }}
        >
          {showLabels && (
            <div
              className="absolute -top-7 left-0 px-2 py-1 text-xs font-bold text-white rounded-t whitespace-nowrap"
              style={{ backgroundColor: color }}
            >
              {animal.animal_id} | {animal.class_name} | {(animal.confidence * 100).toFixed(0)}%
            </div>
          )}
        </div>
      );
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Canlı Kamera</h1>
          <p className="text-gray-500 mt-1">Gerçek zamanlı AI hayvan tespiti</p>
        </div>
        <div className="flex items-center gap-3">
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${
            backendConnected ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
          }`}>
            {backendConnected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
            <span>{backendConnected ? 'AI Bağlı' : 'AI Bağlı Değil'}</span>
          </div>
          
          <button
            onClick={() => setAiEnabled(!aiEnabled)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              aiEnabled ? 'bg-primary-100 text-primary-700' : 'bg-gray-100 text-gray-600'
            }`}
          >
            {aiEnabled ? <Eye className="w-5 h-5" /> : <EyeOff className="w-5 h-5" />}
            <span className="font-medium">AI {aiEnabled ? 'Açık' : 'Kapalı'}</span>
          </button>
          
          <button onClick={() => setShowSettings(!showSettings)} className="p-2 rounded-lg hover:bg-gray-100">
            <Settings className="w-5 h-5 text-gray-600" />
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <span className="text-red-700">{error}</span>
          <button onClick={() => setError(null)} className="ml-auto text-red-500 hover:text-red-700">✕</button>
        </div>
      )}

      {showSettings && (
        <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
          <h3 className="font-semibold text-gray-900">Ayarlar</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={showBboxes} onChange={(e) => setShowBboxes(e.target.checked)} className="rounded" />
              <span className="text-sm">Kutuları Göster</span>
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={showLabels} onChange={(e) => setShowLabels(e.target.checked)} className="rounded" />
              <span className="text-sm">Etiketleri Göster</span>
            </label>
            <div className="flex items-center gap-2">
              <span className="text-sm">FPS:</span>
              <select value={processingFps} onChange={(e) => setProcessingFps(Number(e.target.value))} className="border rounded px-2 py-1 text-sm">
                <option value={2}>2</option>
                <option value={5}>5</option>
                <option value={10}>10</option>
              </select>
            </div>
            <button onClick={checkBackend} className="flex items-center gap-2 px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm">
              <RefreshCw className="w-4 h-4" />Backend Kontrol
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3">
          <div ref={containerRef} className="relative bg-black rounded-xl overflow-hidden aspect-video">
            <video ref={videoRef} className="w-full h-full object-contain" autoPlay playsInline muted />
            <canvas ref={canvasRef} className="hidden" />
            
            {isStreaming && aiEnabled && detectionResult && (
              <div className="absolute inset-0 pointer-events-none">{renderBoundingBoxes()}</div>
            )}
            
            {!isStreaming && (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-white bg-gray-900">
                <Camera className="w-16 h-16 mb-4 text-gray-500" />
                <p className="text-gray-400 text-lg">Kamera başlatılmadı</p>
                <button onClick={startWebcam} className="mt-4 px-6 py-3 bg-primary-600 hover:bg-primary-700 rounded-lg font-medium flex items-center gap-2">
                  <Play className="w-5 h-5" />Kamerayı Başlat
                </button>
              </div>
            )}
            
            {isStreaming && (
              <>
                <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-3 bg-black/60 backdrop-blur-sm rounded-full px-4 py-2">
                  <button onClick={stopWebcam} className="p-2 rounded-full bg-red-600 hover:bg-red-700 text-white" title="Durdur">
                    <Pause className="w-5 h-5" />
                  </button>
                  <button onClick={toggleFullscreen} className="p-2 rounded-full bg-white/20 hover:bg-white/30 text-white">
                    {isFullscreen ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
                  </button>
                </div>
                
                <div className="absolute top-4 left-4 flex items-center gap-2">
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-black/60 backdrop-blur-sm rounded-full">
                    <div className={`w-2 h-2 rounded-full ${backendConnected && aiEnabled ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'}`} />
                    <span className="text-white text-sm font-medium">{backendConnected && aiEnabled ? 'AI Aktif' : 'Sadece Video'}</span>
                  </div>
                  {detectionResult && (
                    <div className="px-3 py-1.5 bg-black/60 backdrop-blur-sm rounded-full text-white text-sm">
                      {detectionResult.animal_count} hayvan
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5 text-primary-600" />Tespit İstatistikleri
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between"><span className="text-gray-600">Toplam Tespit</span><span className="font-semibold">{detectionResult?.animal_count || 0}</span></div>
              <div className="flex justify-between"><span className="text-gray-600">Frame ID</span><span className="font-semibold">{detectionResult?.frame_id || 0}</span></div>
              <div className="flex justify-between"><span className="text-gray-600">İşleme FPS</span><span className="font-semibold">{detectionResult?.fps?.toFixed(1) || 0}</span></div>
              <div className="flex justify-between"><span className="text-gray-600">Backend</span><span className={`font-semibold ${backendConnected ? 'text-green-600' : 'text-red-600'}`}>{backendConnected ? 'Bağlı' : 'Bağlı Değil'}</span></div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h3 className="font-semibold text-gray-900 mb-4">Tespit Edilen Hayvanlar</h3>
            {detectionResult && detectionResult.animals.length > 0 ? (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {detectionResult.animals.map((animal) => (
                  <div key={animal.track_id} className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: CLASS_COLORS[animal.class_name.toLowerCase()] || CLASS_COLORS.default }} />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 truncate">{animal.animal_id}</p>
                      <p className="text-xs text-gray-500">{animal.class_name} • {(animal.confidence * 100).toFixed(0)}%</p>
                    </div>
                    {animal.is_identified && <CheckCircle2 className="w-4 h-4 text-green-500" />}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm text-center py-4">{isStreaming && aiEnabled ? 'Henüz tespit yok' : 'AI kapalı veya kamera başlatılmadı'}</p>
            )}
          </div>
          
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h3 className="font-semibold text-gray-900 mb-4">Hızlı İşlemler</h3>
            <div className="space-y-2">
              <button onClick={isStreaming ? stopWebcam : startWebcam} className={`w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium ${isStreaming ? 'bg-red-100 text-red-700 hover:bg-red-200' : 'bg-green-100 text-green-700 hover:bg-green-200'}`}>
                {isStreaming ? <><CameraOff className="w-5 h-5" />Kamerayı Durdur</> : <><Camera className="w-5 h-5" />Kamerayı Başlat</>}
              </button>
              <button onClick={() => setAiEnabled(!aiEnabled)} disabled={!backendConnected} className={`w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium ${!backendConnected ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : aiEnabled ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200' : 'bg-blue-100 text-blue-700 hover:bg-blue-200'}`}>
                {aiEnabled ? <><EyeOff className="w-5 h-5" />AI Kapat</> : <><Eye className="w-5 h-5" />AI Aç</>}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
