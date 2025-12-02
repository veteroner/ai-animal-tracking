'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import {
  Camera,
  CameraOff,
  RotateCcw,
  Maximize2,
  Minimize2,
  Settings,
  Video,
  Image,
  Wifi,
  WifiOff,
  Play,
  Pause,
  RefreshCw,
} from 'lucide-react';
import { getCameraStreamUrl } from '@/lib/api';

type CameraMode = 'webcam' | 'ip' | 'stream';

interface Detection {
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  confidence: number;
}

export default function CameraPage() {
  const [cameraMode, setCameraMode] = useState<CameraMode>('webcam');
  const [isStreaming, setIsStreaming] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [ipCameraUrl, setIpCameraUrl] = useState('');
  const [detections, setDetections] = useState<Detection[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [frameCount, setFrameCount] = useState(0);
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Start webcam
  const startWebcam = useCallback(async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'environment', // Rear camera on mobile
        },
        audio: false,
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        setIsStreaming(true);
      }
    } catch (err) {
      console.error('Webcam error:', err);
      setError('Kamera erişimi reddedildi veya kamera bulunamadı');
    }
  }, []);

  // Stop webcam
  const stopWebcam = useCallback(() => {
    if (videoRef.current?.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    setIsStreaming(false);
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
      
      const link = document.createElement('a');
      link.download = `snapshot-${Date.now()}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    }
  }, []);

  // Get server stream URL
  const serverStreamUrl = getCameraStreamUrl(0);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Canlı Kamera</h1>
          <p className="text-gray-500 mt-1">Gerçek zamanlı görüntüleme ve tespit</p>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="btn-secondary flex items-center gap-2"
          >
            <Settings className="w-4 h-4" />
            Ayarlar
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">Kamera Ayarları</h3>
          
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

        {/* Detection Boxes */}
        {detections.map((detection, index) => (
          <div
            key={index}
            className="detection-box"
            style={{
              left: `${detection.x}%`,
              top: `${detection.y}%`,
              width: `${detection.width}%`,
              height: `${detection.height}%`,
            }}
          >
            <span className="detection-label">
              {detection.label} ({(detection.confidence * 100).toFixed(0)}%)
            </span>
          </div>
        ))}

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
          <div className="absolute top-4 left-4 right-4 bg-danger-500 text-white px-4 py-2 rounded-lg">
            {error}
          </div>
        )}

        {/* Controls Overlay */}
        {isStreaming && (
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-2 text-white text-sm">
                  <div className="w-2 h-2 rounded-full bg-danger-500 animate-pulse" />
                  <span>CANLI</span>
                </div>
                {cameraMode === 'webcam' && (
                  <span className="text-gray-400 text-sm">Web Kamera</span>
                )}
              </div>
              
              <div className="flex items-center gap-2">
                <button
                  onClick={takeSnapshot}
                  className="p-2 rounded-lg bg-white/20 hover:bg-white/30 text-white transition-colors"
                  title="Ekran Görüntüsü"
                >
                  <Image className="w-5 h-5" />
                </button>
                <button
                  onClick={() => {
                    stopWebcam();
                    setIsStreaming(false);
                  }}
                  className="p-2 rounded-lg bg-white/20 hover:bg-white/30 text-white transition-colors"
                  title="Durdur"
                >
                  <Pause className="w-5 h-5" />
                </button>
                <button
                  onClick={toggleFullscreen}
                  className="p-2 rounded-lg bg-white/20 hover:bg-white/30 text-white transition-colors"
                  title={isFullscreen ? 'Küçült' : 'Tam Ekran'}
                >
                  {isFullscreen ? (
                    <Minimize2 className="w-5 h-5" />
                  ) : (
                    <Maximize2 className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Camera Info Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center gap-3">
            <div className={`p-3 rounded-xl ${isStreaming ? 'bg-success-100' : 'bg-gray-100'}`}>
              {isStreaming ? (
                <Wifi className="w-5 h-5 text-success-600" />
              ) : (
                <WifiOff className="w-5 h-5 text-gray-400" />
              )}
            </div>
            <div>
              <p className="text-sm text-gray-500">Durum</p>
              <p className="font-semibold text-gray-900">
                {isStreaming ? 'Bağlı' : 'Bağlantı Yok'}
              </p>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-primary-100">
              <Camera className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Kamera</p>
              <p className="font-semibold text-gray-900">
                {cameraMode === 'webcam' ? 'Web Kamera' : cameraMode === 'ip' ? 'IP Kamera' : 'Sunucu'}
              </p>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-warning-100">
              <RefreshCw className="w-5 h-5 text-warning-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Tespit</p>
              <p className="font-semibold text-gray-900">{detections.length} nesne</p>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-success-100">
              <Video className="w-5 h-5 text-success-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Çözünürlük</p>
              <p className="font-semibold text-gray-900">1280x720</p>
            </div>
          </div>
        </div>
      </div>

      {/* Instructions */}
      <div className="card bg-primary-50 border-primary-100">
        <h3 className="font-semibold text-primary-900 mb-2">📱 Mobil Kullanım</h3>
        <ul className="text-sm text-primary-700 space-y-1">
          <li>• Telefonunuzdan bu sayfaya erişin</li>
          <li>• &quot;Başlat&quot; butonuna tıklayarak kamerayı açın</li>
          <li>• Arka kamera otomatik olarak seçilecektir</li>
          <li>• Hayvanları kameraya gösterin, AI tespit yapacaktır</li>
        </ul>
      </div>
    </div>
  );
}
