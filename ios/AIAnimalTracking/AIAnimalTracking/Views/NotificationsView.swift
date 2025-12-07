import SwiftUI

struct AppNotification: Identifiable {
    let id = UUID()
    let title: String
    let message: String
    let type: NotificationType
    let date: Date
    var isRead: Bool
}

enum NotificationType: String {
    case alert = "Uyarı"
    case info = "Bilgi"
    case success = "Başarı"
    case health = "Sağlık"
    case estrus = "Kızgınlık"
    
    var icon: String {
        switch self {
        case .alert: return "exclamationmark.triangle.fill"
        case .info: return "info.circle.fill"
        case .success: return "checkmark.circle.fill"
        case .health: return "heart.fill"
        case .estrus: return "heart.circle.fill"
        }
    }
    
    var color: Color {
        switch self {
        case .alert: return .orange
        case .info: return .blue
        case .success: return .green
        case .health: return .red
        case .estrus: return .pink
        }
    }
}

struct NotificationsView: View {
    @State private var notifications: [AppNotification] = []
    @State private var isLoading = true
    @State private var selectedFilter: NotificationType? = nil
    
    var filteredNotifications: [AppNotification] {
        if let filter = selectedFilter {
            return notifications.filter { $0.type == filter }
        }
        return notifications
    }
    
    var unreadCount: Int {
        notifications.filter { !$0.isRead }.count
    }
    
    var body: some View {
        NavigationView {
            ZStack {
                Color.black.ignoresSafeArea()
                
                VStack(spacing: 16) {
                    // Stats
                    HStack(spacing: 12) {
                        NotificationStatCard(title: "Toplam", value: "\(notifications.count)", icon: "bell.fill", color: .blue)
                        NotificationStatCard(title: "Okunmamış", value: "\(unreadCount)", icon: "bell.badge.fill", color: .red)
                        NotificationStatCard(title: "Bugün", value: "\(notifications.filter { Calendar.current.isDateInToday($0.date) }.count)", icon: "calendar", color: .green)
                    }
                    .padding(.horizontal)
                    
                    // Filter
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            NotificationFilterButton(title: "Tümü", isSelected: selectedFilter == nil) {
                                selectedFilter = nil
                            }
                            NotificationFilterButton(title: "Uyarı", isSelected: selectedFilter == .alert) {
                                selectedFilter = .alert
                            }
                            NotificationFilterButton(title: "Sağlık", isSelected: selectedFilter == .health) {
                                selectedFilter = .health
                            }
                            NotificationFilterButton(title: "Kızgınlık", isSelected: selectedFilter == .estrus) {
                                selectedFilter = .estrus
                            }
                            NotificationFilterButton(title: "Bilgi", isSelected: selectedFilter == .info) {
                                selectedFilter = .info
                            }
                        }
                        .padding(.horizontal)
                    }
                    
                    // Notifications List
                    if isLoading {
                        Spacer()
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .blue))
                            .scaleEffect(1.5)
                        Spacer()
                    } else if filteredNotifications.isEmpty {
                        Spacer()
                        VStack(spacing: 12) {
                            Image(systemName: "bell.slash")
                                .font(.system(size: 60))
                                .foregroundColor(.gray)
                            Text("Bildirim yok")
                                .foregroundColor(.gray)
                        }
                        Spacer()
                    } else {
                        ScrollView {
                            LazyVStack(spacing: 12) {
                                ForEach(filteredNotifications) { notification in
                                    NotificationCard(notification: notification) {
                                        markAsRead(notification)
                                    }
                                }
                            }
                            .padding(.horizontal)
                        }
                    }
                    
                    // Actions
                    if !notifications.isEmpty {
                        HStack(spacing: 12) {
                            Button(action: markAllAsRead) {
                                HStack {
                                    Image(systemName: "checkmark.circle")
                                    Text("Tümünü Okundu İşaretle")
                                }
                                .font(.subheadline)
                                .foregroundColor(.blue)
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.blue.opacity(0.15))
                                .cornerRadius(12)
                            }
                            
                            Button(action: clearAll) {
                                HStack {
                                    Image(systemName: "trash")
                                    Text("Temizle")
                                }
                                .font(.subheadline)
                                .foregroundColor(.red)
                                .padding()
                                .background(Color.red.opacity(0.15))
                                .cornerRadius(12)
                            }
                        }
                        .padding(.horizontal)
                        .padding(.bottom)
                    }
                }
                .padding(.top)
            }
            .navigationTitle("🔔 Bildirimler")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { loadData() }) {
                        Image(systemName: "arrow.clockwise")
                            .foregroundColor(.blue)
                    }
                }
            }
        }
        .onAppear { loadData() }
    }
    
    func loadData() {
        isLoading = true
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
            notifications = [
                AppNotification(title: "Kızgınlık Tespit Edildi", message: "COW-001 (Sarıkız) kızgınlık belirtisi gösteriyor. Tohumlama için ideal zaman!", type: .estrus, date: Date(), isRead: false),
                AppNotification(title: "Sağlık Uyarısı", message: "COW-003 (Karabaş) için veteriner kontrolü gerekiyor.", type: .health, date: Date().addingTimeInterval(-3600), isRead: false),
                AppNotification(title: "Yüksek Sıcaklık", message: "Kümes 2'de sıcaklık 28°C'ye ulaştı.", type: .alert, date: Date().addingTimeInterval(-7200), isRead: true),
                AppNotification(title: "Günlük Rapor Hazır", message: "6 Aralık 2025 günlük raporu indirilmeye hazır.", type: .success, date: Date().addingTimeInterval(-86400), isRead: true),
                AppNotification(title: "Yeni Hayvan Kaydedildi", message: "SHEEP-015 sisteme başarıyla eklendi.", type: .info, date: Date().addingTimeInterval(-172800), isRead: true),
            ]
            isLoading = false
        }
    }
    
    func markAsRead(_ notification: AppNotification) {
        if let index = notifications.firstIndex(where: { $0.id == notification.id }) {
            notifications[index].isRead = true
        }
    }
    
    func markAllAsRead() {
        for index in notifications.indices {
            notifications[index].isRead = true
        }
    }
    
    func clearAll() {
        notifications.removeAll()
    }
}

struct NotificationStatCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(color)
            Text(value)
                .font(.title)
                .fontWeight(.bold)
                .foregroundColor(.white)
            Text(title)
                .font(.caption)
                .foregroundColor(.gray)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(Color.gray.opacity(0.2))
        .cornerRadius(12)
    }
}

struct NotificationFilterButton: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.subheadline)
                .fontWeight(isSelected ? .semibold : .regular)
                .foregroundColor(isSelected ? .black : .white)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(isSelected ? Color.blue : Color.gray.opacity(0.3))
                .cornerRadius(20)
        }
    }
}

struct NotificationCard: View {
    let notification: AppNotification
    let onTap: () -> Void
    
    var body: some View {
        Button(action: onTap) {
            HStack(alignment: .top, spacing: 12) {
                ZStack {
                    Circle()
                        .fill(notification.type.color.opacity(0.2))
                        .frame(width: 44, height: 44)
                    Image(systemName: notification.type.icon)
                        .foregroundColor(notification.type.color)
                        .font(.title3)
                }
                
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(notification.title)
                            .font(.headline)
                            .foregroundColor(.white)
                        
                        if !notification.isRead {
                            Circle()
                                .fill(Color.blue)
                                .frame(width: 8, height: 8)
                        }
                    }
                    
                    Text(notification.message)
                        .font(.subheadline)
                        .foregroundColor(.gray)
                        .multilineTextAlignment(.leading)
                    
                    Text(notification.date.formatted(date: .abbreviated, time: .shortened))
                        .font(.caption)
                        .foregroundColor(.gray.opacity(0.7))
                }
                
                Spacer()
            }
            .padding()
            .background(notification.isRead ? Color.gray.opacity(0.1) : Color.gray.opacity(0.2))
            .cornerRadius(16)
        }
    }
}

#Preview {
    NotificationsView()
        .preferredColorScheme(.dark)
}
