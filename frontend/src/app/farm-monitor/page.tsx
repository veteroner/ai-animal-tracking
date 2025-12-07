'use client'

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { 
  Camera, 
  Play, 
  Square, 
  Plus, 
  Trash2, 
  Eye,
  AlertTriangle,
  Heart,
  Activity,
  Wifi,
  WifiOff,
  RefreshCw,
  Settings,
  CheckCircle2,
  XCircle
} from 'lucide-react'

interface CameraInfo {
  id: string
  name: string
  url: string
  status: 'active' | 'inactive' | 'error'
  fps: number
  last_frame: string | null
  total_frames: number
  animals_detected: number
  events_count: number
}

interface MonitorStatus {
  is_running: boolean
  cameras_count: number
  active_cameras: number
  total_detections: number
  events_today: number
  uptime_seconds: number
  cameras: CameraInfo[]
}

interface MonitorEvent {
  id: string
  type: 'estrus' | 'health' | 'birth' | 'anomaly' | 'behavior'
  animal_id: string
  camera_id: string
  timestamp: string
  message: string
  severity: 'low' | 'medium' | 'high' | 'critical'
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function FarmMonitorPage() {
  const [status, setStatus] = useState<MonitorStatus | null>(null)
  const [events, setEvents] = useState<MonitorEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [newCameraName, setNewCameraName] = useState('')
  const [newCameraUrl, setNewCameraUrl] = useState('')
  const [addingCamera, setAddingCamera] = useState(false)
  const [showAddForm, setShowAddForm] = useState(false)

  // Fetch monitor status
  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/farm-monitor/status`)
      if (response.ok) {
        const data = await response.json()
        setStatus(data)
      }
    } catch (error) {
      console.error('Error fetching status:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  // Poll status every 5 seconds
  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 5000)
    return () => clearInterval(interval)
  }, [fetchStatus])

  // Add camera
  const handleAddCamera = async () => {
    if (!newCameraName || !newCameraUrl) return

    setAddingCamera(true)
    try {
      const response = await fetch(`${API_BASE}/api/v1/farm-monitor/cameras`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newCameraName,
          url: newCameraUrl,
          auto_start: true
        })
      })

      if (response.ok) {
        setNewCameraName('')
        setNewCameraUrl('')
        setShowAddForm(false)
        fetchStatus()
      }
    } catch (error) {
      console.error('Error adding camera:', error)
    } finally {
      setAddingCamera(false)
    }
  }

  // Remove camera
  const handleRemoveCamera = async (cameraId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/farm-monitor/cameras/${cameraId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        fetchStatus()
      }
    } catch (error) {
      console.error('Error removing camera:', error)
    }
  }

  // Start monitoring
  const handleStartMonitoring = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/farm-monitor/start`, {
        method: 'POST'
      })

      if (response.ok) {
        fetchStatus()
      }
    } catch (error) {
      console.error('Error starting monitor:', error)
    }
  }

  // Stop monitoring
  const handleStopMonitoring = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/farm-monitor/stop`, {
        method: 'POST'
      })

      if (response.ok) {
        fetchStatus()
      }
    } catch (error) {
      console.error('Error stopping monitor:', error)
    }
  }

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}s ${minutes}d`
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500'
      case 'inactive': return 'bg-gray-500'
      case 'error': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-50'
      case 'high': return 'text-orange-600 bg-orange-50'
      case 'medium': return 'text-yellow-600 bg-yellow-50'
      case 'low': return 'text-green-600 bg-green-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'estrus': return <Heart className="w-4 h-4 text-pink-500" />
      case 'health': return <Activity className="w-4 h-4 text-red-500" />
      case 'birth': return <CheckCircle2 className="w-4 h-4 text-blue-500" />
      case 'anomaly': return <AlertTriangle className="w-4 h-4 text-yellow-500" />
      case 'behavior': return <Eye className="w-4 h-4 text-purple-500" />
      default: return <Activity className="w-4 h-4" />
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Camera className="w-8 h-8 text-blue-500" />
            🏠 Çiftlik İzleme Sistemi
          </h1>
          <p className="text-gray-500 mt-1">
            IP kameralarınızı ekleyin ve yapay zeka ile çiftliğinizi 7/24 izleyin
          </p>
        </div>
        
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={fetchStatus}
            className="gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Yenile
          </Button>
          
          {status?.is_running ? (
            <Button
              variant="destructive"
              onClick={handleStopMonitoring}
              className="gap-2"
            >
              <Square className="w-4 h-4" />
              İzlemeyi Durdur
            </Button>
          ) : (
            <Button
              onClick={handleStartMonitoring}
              className="gap-2 bg-green-600 hover:bg-green-700"
            >
              <Play className="w-4 h-4" />
              İzlemeyi Başlat
            </Button>
          )}
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-full ${status?.is_running ? 'bg-green-100' : 'bg-gray-100'}`}>
                {status?.is_running ? (
                  <Wifi className="w-6 h-6 text-green-600" />
                ) : (
                  <WifiOff className="w-6 h-6 text-gray-400" />
                )}
              </div>
              <div>
                <p className="text-sm text-gray-500">Sistem Durumu</p>
                <p className="text-xl font-bold">
                  {status?.is_running ? 'Çalışıyor' : 'Durduruldu'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-full bg-blue-100">
                <Camera className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Aktif Kameralar</p>
                <p className="text-xl font-bold">
                  {status?.active_cameras || 0} / {status?.cameras_count || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-full bg-purple-100">
                <Eye className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Toplam Tespit</p>
                <p className="text-xl font-bold">
                  {status?.total_detections?.toLocaleString() || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-full bg-orange-100">
                <AlertTriangle className="w-6 h-6 text-orange-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Bugünkü Olaylar</p>
                <p className="text-xl font-bold">
                  {status?.events_today || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Camera List */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Camera className="w-5 h-5" />
                Kameralar
              </CardTitle>
              <Button
                size="sm"
                onClick={() => setShowAddForm(!showAddForm)}
                className="gap-2"
              >
                <Plus className="w-4 h-4" />
                Kamera Ekle
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Add Camera Form */}
              {showAddForm && (
                <div className="p-4 bg-gray-50 rounded-lg space-y-3">
                  <div>
                    <label className="text-sm font-medium">Kamera Adı</label>
                    <Input
                      placeholder="Örn: Ahır Kamerası 1"
                      value={newCameraName}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewCameraName(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Kamera URL (RTSP/HTTP)</label>
                    <Input
                      placeholder="rtsp://kullanici:sifre@192.168.1.100:554/stream"
                      value={newCameraUrl}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewCameraUrl(e.target.value)}
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button
                      onClick={handleAddCamera}
                      disabled={addingCamera || !newCameraName || !newCameraUrl}
                      className="gap-2"
                    >
                      {addingCamera ? (
                        <RefreshCw className="w-4 h-4 animate-spin" />
                      ) : (
                        <Plus className="w-4 h-4" />
                      )}
                      Ekle
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => setShowAddForm(false)}
                    >
                      İptal
                    </Button>
                  </div>
                </div>
              )}

              {/* Camera List */}
              {status?.cameras && status.cameras.length > 0 ? (
                <div className="space-y-3">
                  {status.cameras.map((camera) => (
                    <div
                      key={camera.id}
                      className="p-4 border rounded-lg hover:bg-gray-50 transition"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                          <div className={`w-3 h-3 rounded-full mt-1.5 ${getStatusColor(camera.status)}`} />
                          <div>
                            <h3 className="font-medium">{camera.name}</h3>
                            <p className="text-sm text-gray-500 truncate max-w-md">
                              {camera.url}
                            </p>
                            <div className="flex gap-4 mt-2 text-sm text-gray-500">
                              <span>FPS: {camera.fps}</span>
                              <span>Kare: {camera.total_frames.toLocaleString()}</span>
                              <span>Hayvan: {camera.animals_detected}</span>
                              <span>Olay: {camera.events_count}</span>
                            </div>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRemoveCamera(camera.id)}
                          className="text-red-500 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <Camera className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Henüz kamera eklenmemiş</p>
                  <p className="text-sm">Yukarıdaki "Kamera Ekle" butonunu kullanarak başlayın</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* How it works */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5" />
                Nasıl Çalışır?
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl mb-2">📷</div>
                  <h3 className="font-medium">1. Kamera Ekle</h3>
                  <p className="text-sm text-gray-600">
                    IP kameranızın RTSP veya HTTP stream URL'sini girin
                  </p>
                </div>
                <div className="p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl mb-2">🤖</div>
                  <h3 className="font-medium">2. Yapay Zeka İzler</h3>
                  <p className="text-sm text-gray-600">
                    YOLOv8 ile hayvanları tespit eder, her birine ID atar
                  </p>
                </div>
                <div className="p-4 bg-purple-50 rounded-lg">
                  <div className="text-2xl mb-2">📊</div>
                  <h3 className="font-medium">3. Otomatik Analiz</h3>
                  <p className="text-sm text-gray-600">
                    Davranış, sağlık ve kızgınlık tespiti otomatik yapılır
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Events Panel */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5" />
                Son Olaylar
              </CardTitle>
            </CardHeader>
            <CardContent>
              {events.length > 0 ? (
                <div className="space-y-3">
                  {events.map((event) => (
                    <div
                      key={event.id}
                      className={`p-3 rounded-lg ${getSeverityColor(event.severity)}`}
                    >
                      <div className="flex items-start gap-2">
                        {getEventIcon(event.type)}
                        <div className="flex-1">
                          <p className="text-sm font-medium">{event.message}</p>
                          <p className="text-xs opacity-75">
                            {event.animal_id} • {new Date(event.timestamp).toLocaleTimeString('tr-TR')}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <CheckCircle2 className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Henüz olay yok</p>
                  <p className="text-sm">Kamera ekleyip izlemeyi başlatın</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* AI Features */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                🧠 Yapay Zeka Özellikleri
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center gap-3 p-2 bg-green-50 rounded">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
                <span className="text-sm">Hayvan Tespiti (YOLOv8)</span>
              </div>
              <div className="flex items-center gap-3 p-2 bg-green-50 rounded">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
                <span className="text-sm">Otomatik ID Atama (Re-ID)</span>
              </div>
              <div className="flex items-center gap-3 p-2 bg-green-50 rounded">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
                <span className="text-sm">Davranış Analizi</span>
              </div>
              <div className="flex items-center gap-3 p-2 bg-green-50 rounded">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
                <span className="text-sm">Sağlık İzleme</span>
              </div>
              <div className="flex items-center gap-3 p-2 bg-green-50 rounded">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
                <span className="text-sm">Kızgınlık Tespiti</span>
              </div>
              <div className="flex items-center gap-3 p-2 bg-green-50 rounded">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
                <span className="text-sm">Doğum Algılama</span>
              </div>
            </CardContent>
          </Card>

          {/* Sample URLs */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">📌 Örnek URL Formatları</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-xs text-gray-600">
              <div>
                <p className="font-medium">RTSP (IP Kamera)</p>
                <code className="block bg-gray-100 p-2 rounded mt-1 break-all">
                  rtsp://admin:password@192.168.1.100:554/stream1
                </code>
              </div>
              <div>
                <p className="font-medium">HTTP Stream</p>
                <code className="block bg-gray-100 p-2 rounded mt-1 break-all">
                  http://192.168.1.100:8080/video
                </code>
              </div>
              <div>
                <p className="font-medium">Webcam (Test)</p>
                <code className="block bg-gray-100 p-2 rounded mt-1">
                  0 (birincil webcam)
                </code>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
