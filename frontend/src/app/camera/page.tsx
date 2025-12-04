'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import {
  Camera,
  CameraOff,
  Maximize2,
  Minimize2,
  Settings,
  Video,
  Image,
  Wifi,
  Play,
  Pause,
  Eye,
  EyeOff,
  Activity,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';

type CameraMode = 'webcam' | 'ip' | 'server';

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
  const [cameraMode, setCameraMode] = useState<CameraMode>('webcam');
  const [isStreaming, setIsStreaming] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [ipCameraUrl, setIpCameraUrl] = useState('');
  const [error, setError] = useState<string | null>(null);
  
  // AI Detection State
  const [aiEnabled, setAiEnabled] = useState(true);
  const [detectionResult, setDetectionResult] = useState<DetectionResult | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [wsStatus, setWsStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected');
  const [showLabels, setShowLabels] = useState(true);
  const [showBboxes, setShowBboxes] = useState(true);
  const [processingFps, setProcessingFps] = useState(10); // Frame gönderim hızı
  
  // Gallery info
  const [galleryCount, setGalleryCount] = useState(0);
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const sendIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Backend URL - Production: Render.com
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'https://ai-animal-tracking-api.onrender.com';
  const wsUrl = backendUrl.replace('http', 'ws') + '/api/v1/detection/ws';

  // WebSocket bağlantısı
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }
    
    setWsStatus('connecting');
    setError(null);
    
    try {
      console.log('Connecting to WebSocket:', wsUrl);
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setWsConnected(true);
        setWsStatus('connected');
        setError(null);
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'connected') {
            console.log('Detection service ready');
          } else if (data.type === 'pong' || data.type === 'heartbeat') {
            // Heartbeat - galeri bilgisini güncelle
            if (data.gallery_size !== undefined) {
              setGalleryCount(data.gallery_size);
            }
          } else if (data.type === 'error') {
            console.error('Server error:', data.message);
            setError(data.message);
          } else if (data.frame_id !== undefined) {
            // Detection result
            setDetectionResult(data as DetectionResult);
          } else if (data.type === 'gallery') {
            setGalleryCount(data.count || 0);
          }
        } catch (e) {
          console.error('WebSocket message parse error:', e);
        }
      };
      
      wsRef.current.onclose = () => {
        console.log('WebSocket closed');
        setWsConnected(false);
        setWsStatus('disconnected');
        
        // Yeniden bağlan (3 saniye sonra)
        if (isStreaming && aiEnabled) {
          setTimeout(connectWebSocket, 3000);
        }
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setWsConnected(false);
        setWsStatus('disconnected');
        setError('Backend bağlantısı kurulamadı. Backend çalışıyor mu?');
      };
    } catch (e) {
      console.error('WebSocket connection error:', e);
      setError('WebSocket bağlantı hatası');
    }
  }, [wsUrl, isStreaming, aiEnabled]);

  // Frame gönder (webcam modunda)
  const sendFrame = useCallback(() => {
    if (!videoRef.current || !canvasRef.current || !wsRef.current) return;
    if (wsRef.current.readyState !== WebSocket.OPEN) return;
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    if (!ctx || video.videoWidth === 0) return;
    
    // Canvas boyutunu ayarla
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Frame'i canvas'a çiz
    ctx.drawImage(video, 0, 0);
    
    // JPEG olarak encode et
    const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
    
    // WebSocket'e gönder
    try {
      wsRef.current.send(JSON.stringify({
        type: 'frame',
        data: dataUrl
      }));
    } catch (e) {
      console.error('Frame send error:', e);
    }
  }, []);

  // Start webcam
  const startWebcam = useCallback(async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'environment',
        },
        audio: false,
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        setIsStreaming(true);
        
        // AI aktifse WebSocket bağlan
        if (aiEnabled) {
          connectWebSocket();
          
          // Frame gönderim döngüsü başlat
          if (sendIntervalRef.current) {
            clearInterval(sendIntervalRef.current);
          }
          sendIntervalRef.current = setInterval(sendFrame, 1000 / processingFps);
        }
      }
    } catch (err) {
      console.error('Webcam error:', err);
      setError('Kamera erişimi reddedildi veya kamera bulunamadı');
    }
  }, [aiEnabled, connectWebSocket, sendFrame, processingFps]);

  // Stop webcam
  const stopWebcam = useCallback(() => {
    // Video stream durdur
    if (videoRef.current?.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    
    // Frame gönderimini durdur
    if (sendIntervalRef.current) {
      clearInterval(sendIntervalRef.current);
      sendIntervalRef.current = null;
    }
    
    // WebSocket kapat
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsStreaming(false);
    setDetectionResult(null);
    setWsConnected(false);
    setWsStatus('disconnected');
  }, []);

  // Toggle fullscreen
  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement && containerRef.current) {
      containerRef.current.requestFullscreen();
      setIsFullscreen(true);
    } else if (document.fullscreenElement) {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  }, []);

  // Handle fullscreen change
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  // AI toggle edildiğinde
  useEffect(() => {
    if (isStreaming) {
      if (aiEnabled && !wsConnected) {
        connectWebSocket();
        if (!sendIntervalRef.current) {
          sendIntervalRef.current = setInterval(sendFrame, 1000 / processingFps);
        }
      } else if (!aiEnabled) {
        if (sendIntervalRef.current) {
          clearInterval(sendIntervalRef.current);
          sendIntervalRef.current = null;
        }
        setDetectionResult(null);
      }
    }
  }, [aiEnabled, isStreaming, wsConnected, connectWebSocket, sendFrame, processingFps]);

  // FPS değiştiğinde interval'i güncelle
  useEffect(() => {
    if (isStreaming && aiEnabled && sendIntervalRef.current) {
      clearInterval(sendIntervalRef.current);
      sendIntervalRef.current = setInterval(sendFrame, 1000 / processingFps);
    }
  }, [processingFps, isStreaming, aiEnabled, sendFrame]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopWebcam();
    };
  }, [stopWebcam]);

  // Galeri sıfırla
  const resetGallery = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'reset' }));
      setGalleryCount(0);
    }
  }, []);

  // Take snapshot
  const takeSnapshot = useCallback(() => {
    if (!videoRef.current) return;
    
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.drawImage(videoRef.current, 0, 0);
      
      // Tespitleri de çiz
      if (detectionResult && showBboxes) {
        const scaleX = canvas.width / (detectionResult.frame_size?.[0] || canvas.width);
        const scaleY = canvas.height / (detectionResult.frame_size?.[1] || canvas.height);
        
        detectionResult.animals.forEach(animal => {
          const [x1, y1, x2, y2] = animal.bbox;
          const color = CLASS_COLORS[animal.class_name.toLowerCase()] || CLASS_COLORS.default;
          
          ctx.strokeStyle = color;
          ctx.lineWidth = 3;
          ctx.strokeRect(x1 * scaleX, y1 * scaleY, (x2 - x1) * scaleX, (y2 - y1) * scaleY);
          
          if (showLabels) {
            ctx.fillStyle = color;
            ctx.fillRect(x1 * scaleX, y1 * scaleY - 30, 150, 30);
            ctx.fillStyle = '#000';
            ctx.font = 'bold 16px sans-serif';
            ctx.fillText(animal.animal_id, x1 * scaleX + 5, y1 * scaleY - 10);
          }
        });
      }
      
      const link = document.createElement('a');
      link.download = `snapshot-${Date.now()}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    }
  }, [detectionResult, showBboxes, showLabels]);

  // Renk al
  const getColor = (className: string) => {
    return CLASS_COLORS[className.toLowerCase()] || CLASS_COLORS.default;
  };

  return (
    <div className="space-y-6">
      {/* Hidden canvas for frame capture */}
      <canvas ref={canvasRef} className="hidden" />
      
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">🎥 Gerçek Zamanlı AI Tespit</h1>
          <p className="text-gray-500 mt-1">YOLOv8 + ByteTrack + Re-ID ile hayvan tanıma</p>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Connection Status */}
          <div className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm ${
            wsStatus === 'connected' ? 'bg-green-100 text-green-800' :
            wsStatus === 'connecting' ? 'bg-yellow-100 text-yellow-800' :
            'bg-gray-100 text-gray-600'
          }`}>
            {wsStatus === 'connected' ? (
              <><CheckCircle2 className="w-4 h-4" /> Backend Bağlı</>
            ) : wsStatus === 'connecting' ? (
              <><RefreshCw className="w-4 h-4 animate-spin" /> Bağlanıyor...</>
            ) : (
              <><AlertCircle className="w-4 h-4" /> Bağlı Değil</>
            )}
          </div>
          
          {/* AI Toggle */}
          <button
            onClick={() => setAiEnabled(!aiEnabled)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              aiEnabled 
                ? 'bg-green-600 text-white' 
                : 'bg-gray-200 text-gray-700'
            }`}
          >
            {aiEnabled ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
            AI {aiEnabled ? 'Açık' : 'Kapalı'}
          </button>
          
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="btn-secondary flex items-center gap-2"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* AI Stats Bar */}
      {aiEnabled && wsConnected && detectionResult && (
        <div className="bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-xl p-4">
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold">{detectionResult.animal_count}</div>
              <div className="text-sm opacity-80">Tespit</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{detectionResult.fps?.toFixed(1) || '0'}</div>
              <div className="text-sm opacity-80">AI FPS</div>
            </div>
            <div>
              <div className="text-2xl font-bold">
                {detectionResult.animals.filter(a => a.is_identified).length}
              </div>
              <div className="text-sm opacity-80">Tanınan</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{galleryCount}</div>
              <div className="text-sm opacity-80">Galeri</div>
            </div>
            <div>
              <div className="text-2xl font-bold">
                {detectionResult.animals.length > 0 
                  ? Math.round(detectionResult.animals.reduce((a, b) => a + b.confidence, 0) / detectionResult.animals.length * 100)
                  : 0}%
              </div>
              <div className="text-sm opacity-80">Güven</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-200">🟢 Canlı</div>
              <div className="text-sm opacity-80">Mod</div>
            </div>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <div className="font-medium">Bağlantı Hatası</div>
            <div className="text-sm mt-1">{error}</div>
            <div className="text-sm mt-2 text-red-600">
              Backend&apos;i başlatmak için: <code className="bg-red-100 px-2 py-0.5 rounded">python -m uvicorn src.api.main:app --reload</code>
            </div>
          </div>
        </div>
      )}

      {/* Settings Panel */}
      {showSettings && (
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">Ayarlar</h3>
          
          {/* Camera Mode Selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Kamera Kaynağı
            </label>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => {
                  setCameraMode('webcam');
                  stopWebcam();
                }}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  cameraMode === 'webcam'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Video className="w-4 h-4 inline mr-2" />
                Web Kamera
              </button>
              <button
                onClick={() => {
                  setCameraMode('ip');
                  stopWebcam();
                }}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  cameraMode === 'ip'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Wifi className="w-4 h-4 inline mr-2" />
                IP Kamera
              </button>
              <button
                onClick={() => {
                  setCameraMode('server');
                  stopWebcam();
                }}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  cameraMode === 'server'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Camera className="w-4 h-4 inline mr-2" />
                Sunucu Kamera
              </button>
            </div>
          </div>

          {/* IP Camera URL */}
          {cameraMode === 'ip' && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                IP Kamera URL
              </label>
              <input
                type="text"
                value={ipCameraUrl}
                onChange={(e) => setIpCameraUrl(e.target.value)}
                placeholder="http://192.168.1.100:8080/video"
                className="input"
              />
            </div>
          )}

          {/* Processing FPS */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              İşlem Hızı: {processingFps} FPS
            </label>
            <input
              type="range"
              min="1"
              max="30"
              value={processingFps}
              onChange={(e) => setProcessingFps(Number(e.target.value))}
              className="w-full"
            />
            <p className="text-xs text-gray-500 mt-1">
              Düşük FPS = Daha az CPU kullanımı, Yüksek FPS = Daha akıcı tespit
            </p>
          </div>

          {/* AI Settings */}
          <div className="border-t pt-4 mt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Görüntüleme</h4>
            <div className="flex flex-wrap gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showBboxes}
                  onChange={(e) => setShowBboxes(e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700">Bounding Box</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showLabels}
                  onChange={(e) => setShowLabels(e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700">ID Etiketleri</span>
              </label>
            </div>
          </div>

          {/* Reset Gallery */}
          <div className="border-t pt-4 mt-4">
            <button
              onClick={resetGallery}
              className="btn-secondary flex items-center gap-2"
              disabled={!wsConnected}
            >
              <RefreshCw className="w-4 h-4" />
              Galeriyi Sıfırla ({galleryCount} hayvan)
            </button>
            <p className="text-xs text-gray-500 mt-2">
              Tüm tanınan hayvanları sıfırlar, yeni ID&apos;ler atanır.
            </p>
          </div>
        </div>
      )}

      {/* Camera View */}
      <div 
        ref={containerRef}
        className={`relative bg-gray-900 rounded-xl overflow-hidden ${
          isFullscreen ? 'fixed inset-0 z-50 rounded-none' : 'aspect-video'
        }`}
      >
        {/* Video Element */}
        <video
          ref={videoRef}
          className="w-full h-full object-contain"
          autoPlay
          playsInline
          muted
        />

        {/* AI Detection Overlay */}
        {aiEnabled && showBboxes && detectionResult && detectionResult.animals.map((animal) => {
          const [x1, y1, x2, y2] = animal.bbox;
          const frameW = detectionResult.frame_size?.[0] || 1280;
          const frameH = detectionResult.frame_size?.[1] || 720;
          
          const left = (x1 / frameW) * 100;
          const top = (y1 / frameH) * 100;
          const width = ((x2 - x1) / frameW) * 100;
          const height = ((y2 - y1) / frameH) * 100;
          const color = getColor(animal.class_name);
          
          return (
            <div
              key={`${animal.track_id}-${animal.animal_id}`}
              className="absolute pointer-events-none transition-all duration-100"
              style={{
                left: `${left}%`,
                top: `${top}%`,
                width: `${width}%`,
                height: `${height}%`,
                border: `3px solid ${color}`,
                boxShadow: `0 0 15px ${color}60`,
              }}
            >
              {/* ID Label - Üst */}
              {showLabels && (
                <div
                  className="absolute -top-8 left-0 px-2 py-1 text-sm font-bold text-black whitespace-nowrap rounded shadow-lg"
                  style={{ backgroundColor: color }}
                >
                  {animal.animal_id}
                  {animal.is_identified && ' ✓'}
                </div>
              )}
              
              {/* Class + Confidence - Alt */}
              {showLabels && (
                <div
                  className="absolute -bottom-6 left-0 px-2 py-0.5 text-xs font-medium text-white bg-black/80 rounded whitespace-nowrap"
                >
                  {animal.class_name} • {Math.round(animal.confidence * 100)}%
                </div>
              )}
              
              {/* Corner indicators */}
              <div className="absolute top-0 left-0 w-4 h-4 border-t-3 border-l-3" style={{ borderColor: color }} />
              <div className="absolute top-0 right-0 w-4 h-4 border-t-3 border-r-3" style={{ borderColor: color }} />
              <div className="absolute bottom-0 left-0 w-4 h-4 border-b-3 border-l-3" style={{ borderColor: color }} />
              <div className="absolute bottom-0 right-0 w-4 h-4 border-b-3 border-r-3" style={{ borderColor: color }} />
            </div>
          );
        })}

        {/* Overlay when not streaming */}
        {!isStreaming && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900/90">
            <CameraOff className="w-16 h-16 text-gray-600 mb-4" />
            <p className="text-gray-400 mb-2">Kamera aktif değil</p>
            <p className="text-gray-500 text-sm mb-4">
              {cameraMode === 'webcam' && 'Web kameranızı kullanarak gerçek zamanlı tespit yapın'}
              {cameraMode === 'ip' && 'IP kamera URL\'si girin'}
              {cameraMode === 'server' && 'Sunucu kamerasından stream alın'}
            </p>
            <button
              onClick={startWebcam}
              className="btn-primary flex items-center gap-2"
            >
              <Play className="w-5 h-5" />
              Kamerayı Başlat
            </button>
          </div>
        )}

        {/* Controls Overlay */}
        {isStreaming && (
          <div className="absolute bottom-4 left-4 right-4 flex justify-between items-center">
            <div className="flex gap-2">
              <button
                onClick={stopWebcam}
                className="bg-red-600 hover:bg-red-700 text-white p-3 rounded-full shadow-lg"
                title="Durdur"
              >
                <Pause className="w-5 h-5" />
              </button>
              <button
                onClick={takeSnapshot}
                className="bg-white/90 hover:bg-white text-gray-900 p-3 rounded-full shadow-lg"
                title="Ekran Görüntüsü"
              >
                <Image className="w-5 h-5" />
              </button>
            </div>
            
            <button
              onClick={toggleFullscreen}
              className="bg-white/90 hover:bg-white text-gray-900 p-3 rounded-full shadow-lg"
              title={isFullscreen ? 'Küçült' : 'Tam Ekran'}
            >
              {isFullscreen ? (
                <Minimize2 className="w-5 h-5" />
              ) : (
                <Maximize2 className="w-5 h-5" />
              )}
            </button>
          </div>
        )}
      </div>

      {/* Detection List */}
      {aiEnabled && detectionResult && detectionResult.animals.length > 0 && (
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-green-600" />
            Tespit Edilen Hayvanlar ({detectionResult.animal_count})
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {detectionResult.animals.map((animal) => (
              <div
                key={`list-${animal.track_id}-${animal.animal_id}`}
                className="bg-gray-50 rounded-lg p-3 border-l-4"
                style={{ borderLeftColor: getColor(animal.class_name) }}
              >
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <span className="font-bold text-gray-900">{animal.animal_id}</span>
                    <span className="ml-2 text-sm text-gray-500">{animal.class_name}</span>
                  </div>
                  {animal.is_identified ? (
                    <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                      Tanındı
                    </span>
                  ) : (
                    <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                      Yeni
                    </span>
                  )}
                </div>
                
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-gray-500">Güven:</span>
                    <span className="ml-1 font-medium">{Math.round(animal.confidence * 100)}%</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Re-ID:</span>
                    <span className="ml-1 font-medium">{Math.round(animal.re_id_confidence * 100)}%</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Track:</span>
                    <span className="ml-1 font-medium">#{animal.track_id}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Usage Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 mb-2">🔧 Kullanım</h4>
        <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
          <li>Backend&apos;i başlatın: <code className="bg-blue-100 px-1 rounded">cd ai_goruntu_isleme && source venv/bin/activate && python -m uvicorn src.api.main:app --reload</code></li>
          <li>&quot;Kamerayı Başlat&quot; butonuna tıklayın</li>
          <li>Kamera önüne hayvan/nesne getirin</li>
          <li>AI otomatik tespit edip benzersiz ID atayacak</li>
        </ol>
        <div className="mt-3 pt-3 border-t border-blue-200">
          <h5 className="font-medium text-blue-900 mb-1">Desteklenen Sınıflar:</h5>
          <div className="flex flex-wrap gap-2">
            {Object.entries(CLASS_COLORS).filter(([k]) => k !== 'default').map(([cls, color]) => (
              <span key={cls} className="px-2 py-1 rounded text-xs text-white" style={{ backgroundColor: color }}>
                {cls}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
