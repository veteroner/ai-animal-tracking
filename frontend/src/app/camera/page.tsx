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
} from 'lucide-react';

type CameraMode = 'webcam' | 'ip' | 'stream';

interface TrackedAnimal {
  track_id: number;
  animal_id: string;       // Benzersiz ID: BOV_0001
  class_name: string;      // inek, koyun vb.
  bbox: number[];          // [x1, y1, x2, y2]
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
  cow: '#22c55e',      // Yeşil
  cattle: '#22c55e',
  inek: '#22c55e',
  sheep: '#f97316',    // Turuncu
  koyun: '#f97316',
  goat: '#d946ef',     // Mor
  keçi: '#d946ef',
  horse: '#3b82f6',    // Mavi
  at: '#3b82f6',
  chicken: '#eab308',  // Sarı
  tavuk: '#eab308',
  dog: '#ef4444',      // Kırmızı
  köpek: '#ef4444',
  cat: '#8b5cf6',      // Mor
  kedi: '#8b5cf6',
  default: '#06b6d4',  // Cyan
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
  const [showLabels, setShowLabels] = useState(true);
  const [showBboxes, setShowBboxes] = useState(true);
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // WebSocket bağlantısı
  const connectWebSocket = useCallback(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/detection';
    
    try {
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('WebSocket bağlandı');
        setWsConnected(true);
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const data: DetectionResult = JSON.parse(event.data);
          setDetectionResult(data);
        } catch (e) {
          console.error('WebSocket mesaj hatası:', e);
        }
      };
      
      wsRef.current.onclose = () => {
        console.log('WebSocket bağlantısı kapandı');
        setWsConnected(false);
        // Yeniden bağlan
        setTimeout(connectWebSocket, 3000);
      };
      
      wsRef.current.onerror = () => {
        console.error('WebSocket hatası');
        setWsConnected(false);
      };
    } catch (e) {
      console.error('WebSocket bağlantı hatası:', e);
    }
  }, []);

  // Demo mod: Simüle edilmiş tespitler
  const simulateDetections = useCallback(() => {
    // Demo hayvan verileri
    const demoAnimals: TrackedAnimal[] = [
      {
        track_id: 1,
        animal_id: 'BOV_0001',
        class_name: 'cow',
        bbox: [120, 150, 380, 420],
        confidence: 0.94,
        re_id_confidence: 0.87,
        is_identified: true,
        velocity: [2.3, -1.1],
        direction: 45,
        health_score: 0.92,
        behavior: 'grazing'
      },
      {
        track_id: 2,
        animal_id: 'BOV_0002',
        class_name: 'cow',
        bbox: [450, 200, 680, 450],
        confidence: 0.89,
        re_id_confidence: 0.91,
        is_identified: true,
        velocity: [-1.5, 0.8],
        direction: 120,
        health_score: 0.88,
        behavior: 'walking'
      },
      {
        track_id: 3,
        animal_id: 'SHP_0001',
        class_name: 'sheep',
        bbox: [700, 300, 850, 480],
        confidence: 0.85,
        re_id_confidence: 0.78,
        is_identified: true,
        velocity: [0.5, 0.2],
        direction: 30,
        health_score: 0.95,
        behavior: 'resting'
      }
    ];

    // Animasyon için pozisyonları biraz değiştir
    const animatedAnimals = demoAnimals.map(animal => ({
      ...animal,
      bbox: animal.bbox.map((v, i) => 
        v + Math.sin(Date.now() / 1000 + animal.track_id) * (i % 2 === 0 ? 5 : 3)
      )
    }));

    setDetectionResult({
      frame_id: Math.floor(Date.now() / 33),
      timestamp: Date.now() / 1000,
      fps: 30.2,
      animal_count: animatedAnimals.length,
      animals: animatedAnimals,
      frame_size: [1280, 720]
    });
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
        
        // AI tespiti başlat
        if (aiEnabled && !wsConnected) {
          connectWebSocket();
        }
      }
    } catch (err) {
      console.error('Webcam error:', err);
      setError('Kamera erişimi reddedildi veya kamera bulunamadı');
    }
  }, [aiEnabled, wsConnected, connectWebSocket]);

  // Stop webcam
  const stopWebcam = useCallback(() => {
    if (videoRef.current?.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    setIsStreaming(false);
    setDetectionResult(null);
    
    // WebSocket kapat
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
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

  // Demo modu: WebSocket yoksa simülasyon
  useEffect(() => {
    if (isStreaming && aiEnabled && !wsConnected) {
      const interval = setInterval(simulateDetections, 100);
      return () => clearInterval(interval);
    }
  }, [isStreaming, aiEnabled, wsConnected, simulateDetections]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopWebcam();
    };
  }, [stopWebcam]);

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
        const scaleX = canvas.width / (detectionResult.frame_size?.[0] || 1280);
        const scaleY = canvas.height / (detectionResult.frame_size?.[1] || 720);
        
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

  // Server stream URL
  const serverStreamUrl = '/api/stream/0';

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">🎥 Canlı Kamera + AI</h1>
          <p className="text-gray-500 mt-1">Gerçek zamanlı hayvan tespiti ve benzersiz ID takibi</p>
        </div>
        
        <div className="flex items-center gap-2">
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
            Ayarlar
          </button>
        </div>
      </div>

      {/* AI Stats Bar */}
      {aiEnabled && detectionResult && (
        <div className="bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-xl p-4">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold">{detectionResult.animal_count}</div>
              <div className="text-sm opacity-80">Hayvan</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{detectionResult.fps?.toFixed(1) || '0'}</div>
              <div className="text-sm opacity-80">FPS</div>
            </div>
            <div>
              <div className="text-2xl font-bold">
                {detectionResult.animals.filter(a => a.is_identified).length}
              </div>
              <div className="text-sm opacity-80">Tanınan</div>
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
              <div className={`text-2xl font-bold ${wsConnected ? 'text-green-200' : 'text-yellow-200'}`}>
                {wsConnected ? '🟢' : '🟡'} {wsConnected ? 'Canlı' : 'Demo'}
              </div>
              <div className="text-sm opacity-80">Mod</div>
            </div>
          </div>
        </div>
      )}

      {/* Settings Panel */}
      {showSettings && (
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">Kamera ve AI Ayarları</h3>
          
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
                  setCameraMode('stream');
                  stopWebcam();
                }}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  cameraMode === 'stream'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Camera className="w-4 h-4 inline mr-2" />
                Sunucu Stream
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
                placeholder="rtsp://192.168.1.100:554/stream"
                className="input"
              />
              <p className="text-xs text-gray-500 mt-1">
                RTSP, HTTP veya MJPEG stream URL&apos;si girin
              </p>
            </div>
          )}

          {/* AI Settings */}
          <div className="border-t pt-4 mt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-3">AI Görüntüleme</h4>
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
        {cameraMode === 'webcam' && (
          <video
            ref={videoRef}
            className="w-full h-full object-contain"
            autoPlay
            playsInline
            muted
          />
        )}

        {/* Server Stream (MJPEG) */}
        {cameraMode === 'stream' && isStreaming && (
          <img
            src={serverStreamUrl}
            alt="Kamera Stream"
            className="w-full h-full object-contain"
          />
        )}

        {/* IP Camera (MJPEG) */}
        {cameraMode === 'ip' && isStreaming && ipCameraUrl && (
          <img
            src={ipCameraUrl}
            alt="IP Kamera"
            className="w-full h-full object-contain"
            onError={() => setError('IP kamera bağlantısı kurulamadı')}
          />
        )}

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
              key={animal.track_id}
              className="absolute pointer-events-none transition-all duration-75"
              style={{
                left: `${left}%`,
                top: `${top}%`,
                width: `${width}%`,
                height: `${height}%`,
                border: `3px solid ${color}`,
                boxShadow: `0 0 10px ${color}40`,
              }}
            >
              {/* ID Label - Üst */}
              {showLabels && (
                <div
                  className="absolute -top-8 left-0 px-2 py-1 text-sm font-bold text-black whitespace-nowrap rounded"
                  style={{ backgroundColor: color }}
                >
                  {animal.animal_id}
                </div>
              )}
              
              {/* Class + Confidence - Alt */}
              {showLabels && (
                <div
                  className="absolute -bottom-6 left-0 px-2 py-0.5 text-xs font-medium text-white bg-black/70 rounded whitespace-nowrap"
                >
                  {animal.class_name} • {Math.round(animal.confidence * 100)}%
                  {animal.is_identified && ' ✓'}
                </div>
              )}
              
              {/* Corner indicators */}
              <div className="absolute top-0 left-0 w-3 h-3 border-t-2 border-l-2" style={{ borderColor: color }} />
              <div className="absolute top-0 right-0 w-3 h-3 border-t-2 border-r-2" style={{ borderColor: color }} />
              <div className="absolute bottom-0 left-0 w-3 h-3 border-b-2 border-l-2" style={{ borderColor: color }} />
              <div className="absolute bottom-0 right-0 w-3 h-3 border-b-2 border-r-2" style={{ borderColor: color }} />
            </div>
          );
        })}

        {/* Overlay when not streaming */}
        {!isStreaming && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900/90">
            <CameraOff className="w-16 h-16 text-gray-600 mb-4" />
            <p className="text-gray-400 mb-4">Kamera aktif değil</p>
            <button
              onClick={() => {
                if (cameraMode === 'webcam') {
                  startWebcam();
                } else {
                  setIsStreaming(true);
                }
              }}
              className="btn-primary flex items-center gap-2"
            >
              <Play className="w-5 h-5" />
              Başlat
            </button>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="absolute top-4 left-4 right-4 bg-red-600 text-white px-4 py-2 rounded-lg">
            {error}
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
                key={animal.track_id}
                className="bg-gray-50 rounded-lg p-3 border-l-4"
                style={{ borderLeftColor: getColor(animal.class_name) }}
              >
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <span className="font-bold text-gray-900">{animal.animal_id}</span>
                    <span className="ml-2 text-sm text-gray-500">{animal.class_name}</span>
                  </div>
                  {animal.is_identified && (
                    <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                      Tanındı
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
                  {animal.behavior && (
                    <div className="col-span-2">
                      <span className="text-gray-500">Davranış:</span>
                      <span className="ml-1 font-medium capitalize">{animal.behavior}</span>
                    </div>
                  )}
                  {animal.health_score && (
                    <div className="col-span-2">
                      <span className="text-gray-500">Sağlık:</span>
                      <span className={`ml-1 font-medium ${
                        animal.health_score > 0.8 ? 'text-green-600' : 
                        animal.health_score > 0.5 ? 'text-yellow-600' : 'text-red-600'
                      }`}>
                        {Math.round(animal.health_score * 100)}%
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Usage Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 mb-2">💡 AI Hayvan Takip Sistemi</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Her hayvan benzersiz bir ID alır (BOV_0001, SHP_0001 gibi)</li>
          <li>• Re-ID sistemi hayvanları vücut özelliklerinden tanır</li>
          <li>• Kamera önünden geçen hayvanlar otomatik eşleştirilir</li>
          <li>• Sınıf tespiti: inek, koyun, keçi, at, tavuk ve daha fazlası</li>
          <li>• Demo modda simüle edilmiş tespitler gösterilir</li>
        </ul>
      </div>
    </div>
  );
}
