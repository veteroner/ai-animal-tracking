import SwiftUI

struct HomeView: View {
    @StateObject private var apiService = APIService.shared
    @State private var stats: GalleryStats?
    @State private var isLoading = true
    @State private var showLaunchScreen = true
    
    var body: some View {
        ZStack {
            NavigationView {
                ScrollView {
                    VStack(spacing: 20) {
                        // Header with Teknova Logo
                        headerSection
                        
                        // Server Status
                        serverStatusCard
                        
                        // Stats
                        if let stats = stats {
                            statsSection(stats)
                        }
                        
                        // Quick Actions
                        quickActionsSection
                        
                        // Info Card
                        infoCard
                    }
                    .padding()
                }
                .background(TeknovaColors.background)
                .navigationTitle("Teknova Tracker")
                .onAppear {
                    Task {
                        await loadData()
                    }
                }
                .refreshable {
                    await loadData()
                }
            }
            
            // Launch Screen Overlay
            if showLaunchScreen {
                LaunchScreenView()
                    .transition(.opacity)
                    .zIndex(1)
                    .onAppear {
                        DispatchQueue.main.asyncAfter(deadline: .now() + 2.5) {
                            withAnimation(.easeOut(duration: 0.5)) {
                                showLaunchScreen = false
                            }
                        }
                    }
            }
        }
    }
    
    // MARK: - Header
    private var headerSection: some View {
        VStack(spacing: 16) {
            TeknovaLogo(size: 100)
        }
        .padding(.top, 20)
    }
    
    // MARK: - Server Status
    private var serverStatusCard: some View {
        TeknovaCard {
            HStack {
                Circle()
                    .fill(apiService.isConnected ? TeknovaColors.success : TeknovaColors.danger)
                    .frame(width: 12, height: 12)
                
                VStack(alignment: .leading, spacing: 4) {
                    Text("Sunucu Durumu")
                        .font(TeknovaFont.title(16))
                    Text(apiService.isConnected ? "Bağlı" : "Bağlantı yok")
                        .font(TeknovaFont.caption())
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                TeknovaStatusBadge(
                    text: apiService.isConnected ? "Aktif" : "Offline",
                    status: apiService.isConnected ? .success : .danger
                )
            }
        }
    }
    
    // MARK: - Stats Section
    private func statsSection(_ stats: GalleryStats) -> some View {
        VStack(spacing: 16) {
            HStack(spacing: 16) {
                statCard(
                    value: "\(stats.totalAnimals)",
                    label: "Kayıtlı Hayvan",
                    color: TeknovaColors.primary,
                    icon: "pawprint.fill"
                )
                
                statCard(
                    value: "\(stats.byClass.count)",
                    label: "Tür Çeşidi",
                    color: TeknovaColors.secondary,
                    icon: "list.bullet"
                )
            }
            
            // By Class
            if !stats.byClass.isEmpty {
                TeknovaCard {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Türlere Göre Dağılım")
                            .font(TeknovaFont.title(16))
                        
                        ForEach(Array(stats.byClass.keys.sorted()), id: \.self) { className in
                            HStack {
                                Image(systemName: "circle.fill")
                                    .font(.system(size: 8))
                                    .foregroundColor(TeknovaColors.primary)
                                Text(className.capitalized)
                                    .font(TeknovaFont.body(14))
                                    .foregroundColor(.secondary)
                                Spacer()
                                Text("\(stats.byClass[className] ?? 0)")
                                    .font(TeknovaFont.body(14))
                                    .fontWeight(.semibold)
                                    .foregroundColor(TeknovaColors.primary)
                            }
                            .padding(.vertical, 4)
                            
                            if className != stats.byClass.keys.sorted().last {
                                Divider()
                            }
                        }
                    }
                }
            }
        }
    }
    
    private func statCard(value: String, label: String, color: Color, icon: String) -> some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(.white)
            Text(value)
                .font(.system(size: 32, weight: .bold, design: .rounded))
                .foregroundColor(.white)
            Text(label)
                .font(TeknovaFont.caption())
                .foregroundColor(.white.opacity(0.9))
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(
                    LinearGradient(
                        gradient: Gradient(colors: [color, color.opacity(0.7)]),
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .shadow(color: color.opacity(0.3), radius: 8, x: 0, y: 4)
        )
    }
    
    // MARK: - Quick Actions
    private var quickActionsSection: some View {
        TeknovaCard {
            VStack(alignment: .leading, spacing: 12) {
                Text("Hızlı İşlemler")
                    .font(TeknovaFont.title(16))
                
                NavigationLink(destination: CameraView()) {
                    actionButton(icon: "camera.fill", text: "Kamerayı Başlat", color: TeknovaColors.primary)
                }
                
                NavigationLink(destination: GalleryView()) {
                    actionButton(icon: "photo.stack.fill", text: "Hayvan Listesi", color: TeknovaColors.secondary)
                }
            }
        }
    }
    
    private func actionButton(icon: String, text: String, color: Color) -> some View {
        HStack {
            ZStack {
                Circle()
                    .fill(color.opacity(0.15))
                    .frame(width: 40, height: 40)
                Image(systemName: icon)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(color)
            }
            Text(text)
                .font(TeknovaFont.body(15))
                .foregroundColor(.primary)
            Spacer()
            Image(systemName: "chevron.right")
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(.secondary)
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(UIColor.tertiarySystemBackground))
        )
    }
    
    // MARK: - Info Card
    private var infoCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "info.circle.fill")
                    .foregroundColor(TeknovaColors.secondary)
                Text("Nasıl Çalışır?")
                    .font(TeknovaFont.title(16))
            }
            
            VStack(alignment: .leading, spacing: 8) {
                infoRow("1.", "Kamera sekmesine gidin")
                infoRow("2.", "Hayvanları kameraya gösterin")
                infoRow("3.", "Sistem otomatik olarak tespit eder")
                infoRow("4.", "Yeni hayvanlar otomatik kayıt edilir")
                infoRow("5.", "Daha önce görülen hayvanlar tanınır")
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(TeknovaColors.secondary.opacity(0.1))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(TeknovaColors.secondary.opacity(0.3), lineWidth: 1)
        )
    }
    
    private func infoRow(_ number: String, _ text: String) -> some View {
        HStack(alignment: .top, spacing: 8) {
            Text(number)
                .font(TeknovaFont.caption())
                .fontWeight(.bold)
                .foregroundColor(TeknovaColors.secondary)
            Text(text)
                .font(TeknovaFont.caption())
                .foregroundColor(.secondary)
        }
    }
    
    // MARK: - Load Data
    private func loadData() async {
        _ = await apiService.checkHealth()
        
        if let response = await apiService.getGallery() {
            DispatchQueue.main.async {
                self.stats = response.stats
                self.isLoading = false
            }
        }
    }
}

#Preview {
    HomeView()
        .preferredColorScheme(.dark)
}
