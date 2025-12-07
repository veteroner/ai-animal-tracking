import SwiftUI

// MARK: - Dashboard Models
struct DashboardStats {
    var totalAnimals: Int = 0
    var activeAlerts: Int = 0
    var todayDetections: Int = 0
    var healthyAnimals: Int = 0
    var activeCameras: Int = 0
    var estrusCount: Int = 0
}

struct RecentActivity: Identifiable {
    let id = UUID()
    let icon: String
    let iconColor: Color
    let title: String
    let subtitle: String
    let time: String
}

struct HomeView: View {
    @StateObject private var apiService = APIService.shared
    @State private var stats: GalleryStats?
    @State private var dashboardStats = DashboardStats()
    @State private var recentActivities: [RecentActivity] = []
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
                        
                        // Dashboard Stats Grid
                        dashboardStatsGrid
                        
                        // Quick Status Cards
                        quickStatusCards
                        
                        // Recent Activities
                        recentActivitiesSection
                        
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
                        await loadDashboardData()
                    }
                }
                .refreshable {
                    await loadData()
                    await loadDashboardData()
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
    
    // MARK: - Dashboard Stats Grid
    private var dashboardStatsGrid: some View {
        LazyVGrid(columns: [
            GridItem(.flexible(), spacing: 12),
            GridItem(.flexible(), spacing: 12)
        ], spacing: 12) {
            DashboardStatCard(
                value: "\(dashboardStats.totalAnimals)",
                label: "Toplam Hayvan",
                icon: "pawprint.fill",
                color: .blue
            )
            
            DashboardStatCard(
                value: "\(dashboardStats.activeAlerts)",
                label: "Aktif Uyarı",
                icon: "exclamationmark.triangle.fill",
                color: dashboardStats.activeAlerts > 0 ? .orange : .green
            )
            
            DashboardStatCard(
                value: "\(dashboardStats.todayDetections)",
                label: "Bugün Tespit",
                icon: "eye.fill",
                color: .purple
            )
            
            DashboardStatCard(
                value: "\(dashboardStats.healthyAnimals)",
                label: "Sağlıklı",
                icon: "heart.fill",
                color: .green
            )
        }
    }
    
    // MARK: - Quick Status Cards
    private var quickStatusCards: some View {
        VStack(spacing: 12) {
            // Kamera Durumu
            HStack(spacing: 12) {
                StatusMiniCard(
                    icon: "video.fill",
                    title: "Kameralar",
                    value: "\(dashboardStats.activeCameras) Aktif",
                    color: dashboardStats.activeCameras > 0 ? .green : .gray
                )
                
                StatusMiniCard(
                    icon: "heart.circle.fill",
                    title: "Üreme",
                    value: "\(dashboardStats.estrusCount) Kızgınlık",
                    color: dashboardStats.estrusCount > 0 ? .pink : .gray
                )
            }
        }
    }
    
    // MARK: - Recent Activities
    private var recentActivitiesSection: some View {
        TeknovaCard {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Image(systemName: "clock.arrow.circlepath")
                        .foregroundColor(TeknovaColors.primary)
                    Text("Son Aktiviteler")
                        .font(TeknovaFont.title(16))
                    Spacer()
                    NavigationLink(destination: NotificationsView()) {
                        Text("Tümü")
                            .font(TeknovaFont.caption())
                            .foregroundColor(TeknovaColors.primary)
                    }
                }
                
                if recentActivities.isEmpty {
                    HStack {
                        Spacer()
                        VStack(spacing: 8) {
                            Image(systemName: "tray")
                                .font(.title)
                                .foregroundColor(.secondary)
                            Text("Henüz aktivite yok")
                                .font(TeknovaFont.caption())
                                .foregroundColor(.secondary)
                        }
                        .padding(.vertical, 20)
                        Spacer()
                    }
                } else {
                    ForEach(recentActivities.prefix(5)) { activity in
                        ActivityRow(activity: activity)
                        if activity.id != recentActivities.prefix(5).last?.id {
                            Divider()
                        }
                    }
                }
            }
        }
    }
    
    // MARK: - Load Dashboard Data
    private func loadDashboardData() async {
        // Simüle edilmiş veriler - gerçek API'den alınabilir
        dashboardStats = DashboardStats(
            totalAnimals: stats?.totalAnimals ?? 0,
            activeAlerts: Int.random(in: 0...3),
            todayDetections: Int.random(in: 10...50),
            healthyAnimals: max(0, (stats?.totalAnimals ?? 0) - Int.random(in: 0...2)),
            activeCameras: Int.random(in: 0...2),
            estrusCount: Int.random(in: 0...3)
        )
        
        // Son aktiviteler
        recentActivities = [
            RecentActivity(
                icon: "pawprint.fill",
                iconColor: .blue,
                title: "Yeni hayvan tespit edildi",
                subtitle: "İnek #42 sisteme eklendi",
                time: "5 dk önce"
            ),
            RecentActivity(
                icon: "heart.fill",
                iconColor: .pink,
                title: "Kızgınlık tespiti",
                subtitle: "İnek #15 kızgınlık belirtisi gösteriyor",
                time: "1 saat önce"
            ),
            RecentActivity(
                icon: "exclamationmark.triangle.fill",
                iconColor: .orange,
                title: "Sağlık uyarısı",
                subtitle: "Koyun #7 düşük aktivite",
                time: "2 saat önce"
            ),
            RecentActivity(
                icon: "video.fill",
                iconColor: .green,
                title: "Kamera bağlandı",
                subtitle: "Ahır Kamerası 1 aktif",
                time: "3 saat önce"
            )
        ]
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
    
    // MARK: - Quick Actions
    private var quickActionsSection: some View {
        TeknovaCard {
            VStack(alignment: .leading, spacing: 12) {
                Text("Hızlı İşlemler")
                    .font(TeknovaFont.title(16))
                
                // İlk satır - Ana işlemler
                NavigationLink(destination: CameraView()) {
                    actionButton(icon: "camera.fill", text: "Kamerayı Başlat", color: TeknovaColors.primary)
                }
                
                NavigationLink(destination: GalleryView()) {
                    actionButton(icon: "photo.stack.fill", text: "Hayvan Listesi", color: TeknovaColors.secondary)
                }
                
                // İkinci satır - Grid butonlar
                LazyVGrid(columns: [
                    GridItem(.flexible(), spacing: 8),
                    GridItem(.flexible(), spacing: 8)
                ], spacing: 8) {
                    NavigationLink(destination: HealthView()) {
                        quickActionMini(icon: "heart.text.square.fill", text: "Sağlık", color: .red)
                    }
                    
                    NavigationLink(destination: ReproductionView()) {
                        quickActionMini(icon: "heart.circle.fill", text: "Üreme", color: .pink)
                    }
                    
                    NavigationLink(destination: ZonesView()) {
                        quickActionMini(icon: "map.fill", text: "Bölgeler", color: .green)
                    }
                    
                    NavigationLink(destination: ReportsView()) {
                        quickActionMini(icon: "chart.bar.fill", text: "Raporlar", color: .purple)
                    }
                }
            }
        }
    }
    
    private func quickActionMini(icon: String, text: String, color: Color) -> some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 22, weight: .semibold))
                .foregroundColor(color)
            Text(text)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(.primary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 16)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(color.opacity(0.1))
        )
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

// MARK: - Dashboard Stat Card
struct DashboardStatCard: View {
    let value: String
    let label: String
    let icon: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 8) {
            HStack {
                Image(systemName: icon)
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(color)
                Spacer()
            }
            
            HStack {
                Text(value)
                    .font(.system(size: 28, weight: .bold, design: .rounded))
                    .foregroundColor(.primary)
                Spacer()
            }
            
            HStack {
                Text(label)
                    .font(.system(size: 12))
                    .foregroundColor(.secondary)
                Spacer()
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(Color(UIColor.secondarySystemBackground))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(color.opacity(0.3), lineWidth: 1)
        )
    }
}

// MARK: - Status Mini Card
struct StatusMiniCard: View {
    let icon: String
    let title: String
    let value: String
    let color: Color
    
    var body: some View {
        HStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(color.opacity(0.15))
                    .frame(width: 40, height: 40)
                Image(systemName: icon)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(color)
            }
            
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.system(size: 12))
                    .foregroundColor(.secondary)
                Text(value)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.primary)
            }
            
            Spacer()
        }
        .padding(12)
        .frame(maxWidth: .infinity)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(UIColor.secondarySystemBackground))
        )
    }
}

// MARK: - Activity Row
struct ActivityRow: View {
    let activity: RecentActivity
    
    var body: some View {
        HStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(activity.iconColor.opacity(0.15))
                    .frame(width: 36, height: 36)
                Image(systemName: activity.icon)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(activity.iconColor)
            }
            
            VStack(alignment: .leading, spacing: 2) {
                Text(activity.title)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.primary)
                Text(activity.subtitle)
                    .font(.system(size: 12))
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            Text(activity.time)
                .font(.system(size: 11))
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    HomeView()
        .preferredColorScheme(.dark)
}
