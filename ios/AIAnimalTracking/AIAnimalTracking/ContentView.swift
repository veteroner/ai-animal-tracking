import SwiftUI

struct ContentView: View {
    @State private var selectedTab = 0
    @State private var showMoreMenu = false
    
    var body: some View {
        TabView(selection: $selectedTab) {
            // Tab 1: Ana Sayfa
            HomeView()
                .tabItem {
                    Image(systemName: "house.fill")
                    Text("Ana Sayfa")
                }
                .tag(0)
            
            // Tab 2: İzleme
            FarmMonitorView()
                .tabItem {
                    Image(systemName: "video.fill")
                    Text("İzleme")
                }
                .tag(1)
            
            // Tab 3: Sağlık
            HealthView()
                .tabItem {
                    Image(systemName: "heart.fill")
                    Text("Sağlık")
                }
                .tag(2)
            
            // Tab 4: Üreme
            ReproductionView()
                .tabItem {
                    Image(systemName: "heart.circle.fill")
                    Text("Üreme")
                }
                .tag(3)
            
            // Tab 5: Daha Fazla
            MoreMenuView()
                .tabItem {
                    Image(systemName: "ellipsis.circle.fill")
                    Text("Daha Fazla")
                }
                .tag(4)
        }
        .accentColor(.green)
    }
}

// Daha Fazla Menüsü
struct MoreMenuView: View {
    var body: some View {
        NavigationView {
            ZStack {
                Color.black.ignoresSafeArea()
                
                ScrollView {
                    VStack(spacing: 12) {
                        // Hayvanlar
                        NavigationLink(destination: GalleryView()) {
                            MoreMenuItem(icon: "pawprint.fill", title: "Hayvanlar", subtitle: "Tüm hayvanları görüntüle", color: .blue)
                        }
                        
                        // Kanatlı
                        NavigationLink(destination: PoultryView()) {
                            MoreMenuItem(icon: "bird.fill", title: "Kanatlı Takibi", subtitle: "Kümes ve yumurta yönetimi", color: .yellow)
                        }
                        
                        // Bölgeler
                        NavigationLink(destination: ZonesView()) {
                            MoreMenuItem(icon: "map.fill", title: "Bölge Haritası", subtitle: "Çiftlik bölgelerini görüntüle", color: .green)
                        }
                        
                        // Kamera
                        NavigationLink(destination: CameraView()) {
                            MoreMenuItem(icon: "camera.fill", title: "Kamera", subtitle: "Hayvan fotoğrafı çek", color: .purple)
                        }
                        
                        // Raporlar
                        NavigationLink(destination: ReportsView()) {
                            MoreMenuItem(icon: "chart.bar.fill", title: "Raporlar", subtitle: "Analiz ve istatistikler", color: .orange)
                        }
                        
                        // Bildirimler
                        NavigationLink(destination: NotificationsView()) {
                            MoreMenuItem(icon: "bell.fill", title: "Bildirimler", subtitle: "Tüm bildirimler", color: .red)
                        }
                        
                        // Uyarılar
                        NavigationLink(destination: AlertsView()) {
                            MoreMenuItem(icon: "exclamationmark.triangle.fill", title: "Uyarılar", subtitle: "Sistem uyarıları", color: .orange)
                        }
                        
                        // Yardım
                        NavigationLink(destination: HelpView()) {
                            MoreMenuItem(icon: "questionmark.circle.fill", title: "Yardım", subtitle: "Kullanım kılavuzu ve SSS", color: .cyan)
                        }
                        
                        // Ayarlar
                        NavigationLink(destination: SettingsView()) {
                            MoreMenuItem(icon: "gearshape.fill", title: "Ayarlar", subtitle: "Uygulama ayarları", color: .gray)
                        }
                    }
                    .padding()
                }
            }
            .navigationTitle("Daha Fazla")
            .navigationBarTitleDisplayMode(.large)
        }
    }
}

struct MoreMenuItem: View {
    let icon: String
    let title: String
    let subtitle: String
    let color: Color
    
    var body: some View {
        HStack(spacing: 16) {
            ZStack {
                Circle()
                    .fill(color.opacity(0.2))
                    .frame(width: 50, height: 50)
                Image(systemName: icon)
                    .foregroundColor(color)
                    .font(.title2)
            }
            
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.headline)
                    .foregroundColor(.white)
                Text(subtitle)
                    .font(.caption)
                    .foregroundColor(.gray)
            }
            
            Spacer()
            
            Image(systemName: "chevron.right")
                .foregroundColor(.gray)
        }
        .padding()
        .background(Color.gray.opacity(0.15))
        .cornerRadius(16)
    }
}

#Preview {
    ContentView()
        .preferredColorScheme(.dark)
}
