'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { 
  HelpCircle, 
  Star, 
  BookOpen, 
  MessageCircle, 
  Mail, 
  Phone, 
  Globe,
  ChevronDown,
  ChevronUp,
  Camera,
  Eye,
  Heart,
  Activity,
  Map,
  BarChart,
  Bell,
  Video,
  Cpu,
  Shield,
  Zap,
  Users,
  CheckCircle2,
  Info
} from 'lucide-react'

interface FAQItem {
  question: string
  answer: string
}

const features = [
  { icon: Camera, title: 'YOLOv8 Tespit', description: 'Gerçek zamanlı hayvan tespiti', color: 'text-blue-500' },
  { icon: Users, title: 'Re-ID Tanıma', description: 'Otomatik hayvan kimlik atama', color: 'text-purple-500' },
  { icon: Heart, title: 'Sağlık İzleme', description: 'Hayvan sağlığı takibi', color: 'text-red-500' },
  { icon: Activity, title: 'Kızgınlık Tespiti', description: 'Üreme döngüsü analizi', color: 'text-pink-500' },
  { icon: Eye, title: 'Davranış Analizi', description: 'Anormal davranış algılama', color: 'text-orange-500' },
  { icon: Video, title: 'IP Kamera Desteği', description: 'RTSP/HTTP stream desteği', color: 'text-green-500' },
  { icon: Map, title: 'Bölge Yönetimi', description: 'Çiftlik harita görünümü', color: 'text-teal-500' },
  { icon: BarChart, title: 'Raporlar', description: 'Detaylı analiz raporları', color: 'text-indigo-500' },
]

const steps = [
  {
    step: 1,
    title: 'Kamera Ekleyin',
    description: 'IP kameranızın RTSP veya HTTP stream URL\'sini girerek sisteme ekleyin. Örnek: rtsp://admin:password@192.168.1.100:554/stream',
    icon: Camera
  },
  {
    step: 2,
    title: 'İzlemeyi Başlatın',
    description: 'Çiftlik İzleme sayfasından "İzlemeyi Başlat" butonuna tıklayın. Sistem tüm kameralardan görüntü almaya başlayacak.',
    icon: Video
  },
  {
    step: 3,
    title: 'Yapay Zeka Çalışsın',
    description: 'YOLOv8 modeli otomatik olarak hayvanları tespit eder ve Re-ID algoritması ile her birine benzersiz ID atar.',
    icon: Cpu
  },
  {
    step: 4,
    title: 'Uyarıları Takip Edin',
    description: 'Sağlık sorunları, kızgınlık belirtileri ve anormal davranışlar için anlık bildirimler alın.',
    icon: Bell
  },
  {
    step: 5,
    title: 'Raporları İnceleyin',
    description: 'Hayvan sağlığı, üreme döngüsü ve performans raporlarını detaylı olarak görüntüleyin ve analiz edin.',
    icon: BarChart
  }
]

const faqs: FAQItem[] = [
  {
    question: 'Hangi kamera türleri destekleniyor?',
    answer: 'RTSP protokolünü destekleyen tüm IP kameralar ve HTTP stream URL\'si olan kameralar kullanılabilir. Ayrıca USB webcam\'ler de test amaçlı kullanılabilir (URL olarak "0" yazın).'
  },
  {
    question: 'Kaç hayvan aynı anda takip edilebilir?',
    answer: 'Sistem, kamera kalitesi ve sunucu kapasitesine bağlı olarak yüzlerce hayvanı aynı anda takip edebilir. Performans, GPU gücü ve ağ bant genişliğine göre değişir.'
  },
  {
    question: 'Kızgınlık tespiti nasıl çalışır?',
    answer: 'Yapay zeka, hayvanların hareket kalıplarını, aktivite seviyelerini, diğer hayvanlarla etkileşimlerini ve davranış değişikliklerini analiz ederek kızgınlık belirtilerini tespit eder.'
  },
  {
    question: 'İnternet bağlantısı koptuğunda ne olur?',
    answer: 'Veriler yerel olarak saklanır ve bağlantı düzeldiğinde otomatik olarak senkronize edilir. Sistem çevrimdışı modda da çalışmaya devam eder.'
  },
  {
    question: 'Desteklenen hayvan türleri nelerdir?',
    answer: 'Sığır (inek, boğa, dana), koyun, keçi, at, eşek, tavuk, hindi, kaz, ördek ve diğer çiftlik hayvanları desteklenmektedir. Özel türler için model eğitimi yapılabilir.'
  },
  {
    question: 'Sistem güvenliği nasıl sağlanıyor?',
    answer: 'Tüm veriler şifreli olarak saklanır. API erişimi token tabanlı kimlik doğrulama ile korunur. Kullanıcı rolleri ve yetkilendirme sistemi mevcuttur.'
  },
  {
    question: 'Mobil uygulama mevcut mu?',
    answer: 'Evet, iOS ve Android için native mobil uygulamalar mevcuttur. Ayrıca Expo tabanlı cross-platform uygulama da kullanılabilir.'
  },
  {
    question: 'Raporlar hangi formatlarda indirilebilir?',
    answer: 'Raporlar PDF, Excel (XLSX), CSV ve JSON formatlarında indirilebilir. Otomatik rapor gönderimi için e-posta entegrasyonu da mevcuttur.'
  }
]

export default function HelpPage() {
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null)

  return (
    <div className="container mx-auto p-6 space-y-8 max-w-5xl">
      {/* Header */}
      <div className="text-center space-y-4">
        <div className="flex justify-center">
          <div className="w-24 h-24 rounded-full bg-gradient-to-br from-teal-500 to-blue-600 flex items-center justify-center">
            <Eye className="w-12 h-12 text-white" />
          </div>
        </div>
        <h1 className="text-4xl font-bold">Teknova AI Animal Tracking</h1>
        <p className="text-xl text-gray-500">
          Yapay zeka destekli hayvan takip ve izleme sistemi
        </p>
      </div>

      {/* About */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Info className="w-5 h-5 text-blue-500" />
            Hakkında
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600 leading-relaxed">
            Teknova AI Animal Tracking, çiftliklerinizde hayvanlarınızı yapay zeka ile otomatik olarak takip etmenizi 
            sağlayan yenilikçi bir sistemdir. YOLOv8 nesne algılama ve Re-ID (yeniden tanımlama) teknolojileri ile 
            hayvanlarınızı tespit eder, tanır ve sağlık durumlarını izler. 7/24 kesintisiz izleme, anlık uyarılar 
            ve detaylı raporlama özellikleri ile çiftlik yönetiminizi kolaylaştırır.
          </p>
        </CardContent>
      </Card>

      {/* Features */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Star className="w-5 h-5 text-yellow-500" />
            Özellikler
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {features.map((feature, index) => (
              <div key={index} className="text-center p-4 rounded-lg bg-gray-50 hover:bg-gray-100 transition">
                <div className={`mx-auto w-12 h-12 rounded-full bg-white shadow flex items-center justify-center mb-3`}>
                  <feature.icon className={`w-6 h-6 ${feature.color}`} />
                </div>
                <h3 className="font-medium text-sm">{feature.title}</h3>
                <p className="text-xs text-gray-500 mt-1">{feature.description}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* How to Use */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-green-500" />
            Nasıl Kullanılır?
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {steps.map((step, index) => (
              <div key={index} className="flex gap-4">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 rounded-full bg-teal-500 text-white flex items-center justify-center font-bold">
                    {step.step}
                  </div>
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <step.icon className="w-4 h-4 text-teal-500" />
                    <h3 className="font-semibold">{step.title}</h3>
                  </div>
                  <p className="text-gray-600 text-sm">{step.description}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* FAQ */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <HelpCircle className="w-5 h-5 text-orange-500" />
            Sıkça Sorulan Sorular
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {faqs.map((faq, index) => (
              <div 
                key={index} 
                className="border rounded-lg overflow-hidden"
              >
                <button
                  className="w-full p-4 text-left flex items-center justify-between hover:bg-gray-50 transition"
                  onClick={() => setExpandedFaq(expandedFaq === index ? null : index)}
                >
                  <span className="font-medium pr-4">{faq.question}</span>
                  {expandedFaq === index ? (
                    <ChevronUp className="w-5 h-5 text-gray-400 flex-shrink-0" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" />
                  )}
                </button>
                {expandedFaq === index && (
                  <div className="px-4 pb-4 text-gray-600 text-sm border-t bg-gray-50">
                    <p className="pt-3">{faq.answer}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Contact */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageCircle className="w-5 h-5 text-blue-500" />
            İletişim & Destek
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center gap-3 p-3 rounded-lg bg-gray-50">
              <Mail className="w-5 h-5 text-blue-500" />
              <div>
                <p className="text-xs text-gray-500">E-posta</p>
                <p className="font-medium">destek@teknova.com.tr</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-lg bg-gray-50">
              <Phone className="w-5 h-5 text-green-500" />
              <div>
                <p className="text-xs text-gray-500">Telefon</p>
                <p className="font-medium">+90 555 123 4567</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-lg bg-gray-50">
              <Globe className="w-5 h-5 text-purple-500" />
              <div>
                <p className="text-xs text-gray-500">Web Sitesi</p>
                <p className="font-medium">www.teknova.com.tr</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-lg bg-gray-50">
              <BookOpen className="w-5 h-5 text-orange-500" />
              <div>
                <p className="text-xs text-gray-500">Dokümantasyon</p>
                <p className="font-medium">docs.teknova.com.tr</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Version */}
      <div className="text-center text-gray-400 text-sm space-y-1 py-8">
        <p>Versiyon 1.0.0</p>
        <p>© 2025 Teknova. Tüm hakları saklıdır.</p>
      </div>
    </div>
  )
}
