import SwiftUI

struct HelpView: View {
    @State private var expandedSection: String? = nil
    
    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // Header
                headerSection
                
                // About Section
                aboutSection
                
                // Features Section
                featuresSection
                
                // How to Use Section
                howToUseSection
                
                // FAQ Section
                faqSection
                
                // Contact Section
                contactSection
                
                // Version Info
                versionInfo
            }
            .padding()
        }
        .background(TeknovaColors.background)
        .navigationTitle("Yardım")
        .navigationBarTitleDisplayMode(.large)
    }
    
    // MARK: - Header
    private var headerSection: some View {
        VStack(spacing: 16) {
            TeknovaLogo(size: 80)
            
            Text("Teknova AI Animal Tracking")
                .font(.title2)
                .fontWeight(.bold)
            
            Text("Yapay zeka destekli hayvan takip ve izleme sistemi")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding(.vertical, 20)
    }
    
    // MARK: - About
    private var aboutSection: some View {
        TeknovaCard {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Image(systemName: "info.circle.fill")
                        .foregroundColor(.blue)
                        .font(.title3)
                    Text("Hakkında")
                        .font(.headline)
                }
                
                Text("Teknova AI Animal Tracking, çiftliklerinizde hayvanlarınızı yapay zeka ile otomatik olarak takip etmenizi sağlayan yenilikçi bir sistemdir. YOLOv8 ve Re-ID teknolojileri ile hayvanlarınızı tespit eder, tanır ve sağlık durumlarını izler.")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .lineSpacing(4)
            }
        }
    }
    
    // MARK: - Features
    private var featuresSection: some View {
        TeknovaCard {
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    Image(systemName: "star.fill")
                        .foregroundColor(.yellow)
                        .font(.title3)
                    Text("Özellikler")
                        .font(.headline)
                }
                
                LazyVGrid(columns: [
                    GridItem(.flexible()),
                    GridItem(.flexible())
                ], spacing: 12) {
                    FeatureItem(icon: "camera.viewfinder", title: "YOLOv8 Tespit", color: .blue)
                    FeatureItem(icon: "person.crop.rectangle.stack", title: "Re-ID Tanıma", color: .purple)
                    FeatureItem(icon: "heart.text.square", title: "Sağlık İzleme", color: .red)
                    FeatureItem(icon: "heart.circle", title: "Kızgınlık Tespiti", color: .pink)
                    FeatureItem(icon: "figure.walk", title: "Davranış Analizi", color: .orange)
                    FeatureItem(icon: "video", title: "IP Kamera Desteği", color: .green)
                    FeatureItem(icon: "map", title: "Bölge Yönetimi", color: .teal)
                    FeatureItem(icon: "chart.bar", title: "Raporlar", color: .indigo)
                }
            }
        }
    }
    
    // MARK: - How to Use
    private var howToUseSection: some View {
        TeknovaCard {
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    Image(systemName: "book.fill")
                        .foregroundColor(.green)
                        .font(.title3)
                    Text("Nasıl Kullanılır?")
                        .font(.headline)
                }
                
                VStack(alignment: .leading, spacing: 16) {
                    StepItem(
                        step: 1,
                        title: "Kamera Ekleyin",
                        description: "IP kameranızın RTSP veya HTTP stream URL'sini girerek sisteme ekleyin.",
                        icon: "camera.fill"
                    )
                    
                    StepItem(
                        step: 2,
                        title: "İzlemeyi Başlatın",
                        description: "Çiftlik İzleme sayfasından 'İzlemeyi Başlat' butonuna tıklayın.",
                        icon: "play.fill"
                    )
                    
                    StepItem(
                        step: 3,
                        title: "Yapay Zeka Çalışsın",
                        description: "Sistem otomatik olarak hayvanları tespit edip, her birine benzersiz ID atar.",
                        icon: "cpu"
                    )
                    
                    StepItem(
                        step: 4,
                        title: "Uyarıları Takip Edin",
                        description: "Sağlık sorunları, kızgınlık belirtileri ve anormal davranışlar için bildirim alın.",
                        icon: "bell.fill"
                    )
                    
                    StepItem(
                        step: 5,
                        title: "Raporları İnceleyin",
                        description: "Hayvan sağlığı, üreme ve performans raporlarını görüntüleyin.",
                        icon: "doc.text.fill"
                    )
                }
            }
        }
    }
    
    // MARK: - FAQ
    private var faqSection: some View {
        TeknovaCard {
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    Image(systemName: "questionmark.circle.fill")
                        .foregroundColor(.orange)
                        .font(.title3)
                    Text("Sıkça Sorulan Sorular")
                        .font(.headline)
                }
                
                VStack(spacing: 12) {
                    FAQItem(
                        question: "Hangi kamera türleri destekleniyor?",
                        answer: "RTSP protokolünü destekleyen tüm IP kameralar ve HTTP stream URL'si olan kameralar kullanılabilir."
                    )
                    
                    FAQItem(
                        question: "Kaç hayvan aynı anda takip edilebilir?",
                        answer: "Sistem, kamera kalitesi ve sunucu kapasitesine bağlı olarak yüzlerce hayvanı aynı anda takip edebilir."
                    )
                    
                    FAQItem(
                        question: "Kızgınlık tespiti nasıl çalışır?",
                        answer: "Yapay zeka, hayvanların hareket kalıplarını, aktivite seviyelerini ve davranış değişikliklerini analiz ederek kızgınlık belirtilerini tespit eder."
                    )
                    
                    FAQItem(
                        question: "İnternet bağlantısı koptuğunda ne olur?",
                        answer: "Veriler yerel olarak saklanır ve bağlantı düzeldiğinde otomatik olarak senkronize edilir."
                    )
                    
                    FAQItem(
                        question: "Desteklenen hayvan türleri nelerdir?",
                        answer: "Sığır, koyun, keçi, at, tavuk ve diğer çiftlik hayvanları desteklenmektedir."
                    )
                }
            }
        }
    }
    
    // MARK: - Contact
    private var contactSection: some View {
        TeknovaCard {
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    Image(systemName: "envelope.fill")
                        .foregroundColor(.blue)
                        .font(.title3)
                    Text("İletişim & Destek")
                        .font(.headline)
                }
                
                VStack(spacing: 12) {
                    ContactItem(icon: "envelope", title: "E-posta", value: "destek@teknova.com.tr")
                    ContactItem(icon: "phone", title: "Telefon", value: "+90 555 123 4567")
                    ContactItem(icon: "globe", title: "Web Sitesi", value: "www.teknova.com.tr")
                    ContactItem(icon: "doc.text", title: "Dokümantasyon", value: "docs.teknova.com.tr")
                }
            }
        }
    }
    
    // MARK: - Version
    private var versionInfo: some View {
        VStack(spacing: 8) {
            Text("Versiyon 1.0.0")
                .font(.caption)
                .foregroundColor(.secondary)
            
            Text("© 2025 Teknova. Tüm hakları saklıdır.")
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 20)
    }
}

// MARK: - Supporting Views
struct FeatureItem: View {
    let icon: String
    let title: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 8) {
            ZStack {
                Circle()
                    .fill(color.opacity(0.15))
                    .frame(width: 44, height: 44)
                Image(systemName: icon)
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(color)
            }
            
            Text(title)
                .font(.caption)
                .fontWeight(.medium)
                .multilineTextAlignment(.center)
                .foregroundColor(.primary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 8)
    }
}

struct StepItem: View {
    let step: Int
    let title: String
    let description: String
    let icon: String
    
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            ZStack {
                Circle()
                    .fill(TeknovaColors.primary)
                    .frame(width: 32, height: 32)
                Text("\(step)")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(.white)
            }
            
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Image(systemName: icon)
                        .font(.system(size: 12))
                        .foregroundColor(TeknovaColors.primary)
                    Text(title)
                        .font(.subheadline)
                        .fontWeight(.semibold)
                }
                
                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineSpacing(2)
            }
        }
    }
}

struct FAQItem: View {
    let question: String
    let answer: String
    @State private var isExpanded = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Button(action: {
                withAnimation(.easeInOut(duration: 0.2)) {
                    isExpanded.toggle()
                }
            }) {
                HStack {
                    Text(question)
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(.primary)
                        .multilineTextAlignment(.leading)
                    
                    Spacer()
                    
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            if isExpanded {
                Text(answer)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineSpacing(2)
                    .padding(.top, 4)
            }
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 10)
                .fill(Color(UIColor.tertiarySystemBackground))
        )
    }
}

struct ContactItem: View {
    let icon: String
    let title: String
    let value: String
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 16))
                .foregroundColor(TeknovaColors.primary)
                .frame(width: 24)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.caption)
                    .foregroundColor(.secondary)
                Text(value)
                    .font(.subheadline)
                    .foregroundColor(.primary)
            }
            
            Spacer()
        }
    }
}

#Preview {
    NavigationView {
        HelpView()
    }
    .preferredColorScheme(.dark)
}
