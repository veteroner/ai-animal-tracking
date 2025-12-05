import SwiftUI

struct AlertsView: View {
    @State private var alerts: [AlertItem] = demoAlerts
    
    private var unreadCount: Int {
        alerts.filter { !$0.isRead }.count
    }
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Header Stats
                headerStats
                
                // Alert List
                if alerts.isEmpty {
                    emptyView
                } else {
                    alertList
                }
            }
            .navigationTitle("Uyarılar")
        }
    }
    
    // MARK: - Header Stats
    private var headerStats: some View {
        HStack {
            VStack(spacing: 2) {
                Text("\(alerts.count)")
                    .font(.title2)
                    .fontWeight(.bold)
                Text("Toplam")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            
            Divider().frame(height: 40)
            
            VStack(spacing: 2) {
                Text("\(unreadCount)")
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundColor(.red)
                Text("Okunmamış")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            Button("Tümünü Okundu İşaretle") {
                markAllAsRead()
            }
            .font(.caption)
            .foregroundColor(.blue)
        }
        .padding()
        .background(Color(UIColor.secondarySystemBackground))
    }
    
    // MARK: - Alert List
    private var alertList: some View {
        List {
            ForEach(alerts) { alert in
                AlertRowView(alert: alert) {
                    markAsRead(alert.id)
                }
            }
        }
        .listStyle(.plain)
    }
    
    // MARK: - Empty View
    private var emptyView: some View {
        VStack(spacing: 16) {
            Spacer()
            Text("🔔")
                .font(.system(size: 60))
            Text("Uyarı yok")
                .font(.headline)
            Text("Yeni uyarılar burada görünecek")
                .font(.subheadline)
                .foregroundColor(.secondary)
            Spacer()
        }
    }
    
    // MARK: - Actions
    private func markAsRead(_ id: UUID) {
        if let index = alerts.firstIndex(where: { $0.id == id }) {
            alerts[index].isRead = true
        }
    }
    
    private func markAllAsRead() {
        alerts = alerts.map { alert in
            var mutableAlert = alert
            mutableAlert.isRead = true
            return mutableAlert
        }
    }
}

// MARK: - Alert Row View
struct AlertRowView: View {
    let alert: AlertItem
    let onTap: () -> Void
    
    var body: some View {
        Button(action: onTap) {
            HStack(alignment: .top, spacing: 12) {
                // Icon
                Image(systemName: alert.type.icon)
                    .font(.title2)
                    .foregroundColor(alert.severity.color)
                    .frame(width: 30)
                
                VStack(alignment: .leading, spacing: 4) {
                    // Title & Time
                    HStack {
                        Text(alert.title)
                            .font(.subheadline)
                            .fontWeight(.semibold)
                            .foregroundColor(.primary)
                        
                        Spacer()
                        
                        Text(timeAgo(alert.createdAt))
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                    
                    // Message
                    Text(alert.message)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .lineLimit(2)
                }
                
                // Severity Badge
                VStack {
                    Text(alert.severity.rawValue)
                        .font(.system(size: 9))
                        .fontWeight(.bold)
                        .textCase(.uppercase)
                        .foregroundColor(.white)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 3)
                        .background(alert.severity.color)
                        .cornerRadius(4)
                    
                    Spacer()
                }
            }
            .padding()
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(alert.isRead ? Color(UIColor.secondarySystemBackground) : Color.blue.opacity(0.1))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(alert.severity.color, lineWidth: 2)
                    .opacity(0.3)
            )
            .overlay(
                Group {
                    if !alert.isRead {
                        Circle()
                            .fill(Color.blue)
                            .frame(width: 8, height: 8)
                            .position(x: 8, y: 8)
                    }
                }
            )
        }
        .buttonStyle(.plain)
        .listRowSeparator(.hidden)
        .listRowBackground(Color.clear)
        .listRowInsets(EdgeInsets(top: 6, leading: 16, bottom: 6, trailing: 16))
    }
    
    private func timeAgo(_ date: Date) -> String {
        let diff = Date().timeIntervalSince(date)
        
        if diff < 60 {
            return "Az önce"
        } else if diff < 3600 {
            return "\(Int(diff / 60)) dk önce"
        } else if diff < 86400 {
            return "\(Int(diff / 3600)) saat önce"
        } else {
            let formatter = DateFormatter()
            formatter.dateFormat = "dd.MM HH:mm"
            return formatter.string(from: date)
        }
    }
}

// MARK: - Demo Data
private let demoAlerts: [AlertItem] = [
    AlertItem(
        type: .activity,
        severity: .medium,
        title: "Yeni Hayvan Tespit Edildi",
        message: "INEK_0001 sisteme kaydedildi",
        createdAt: Date(),
        isRead: false
    ),
    AlertItem(
        type: .system,
        severity: .low,
        title: "Sistem Başlatıldı",
        message: "AI Hayvan Takip sistemi aktif",
        createdAt: Date().addingTimeInterval(-3600),
        isRead: true
    ),
    AlertItem(
        type: .security,
        severity: .high,
        title: "Bölge İhlali",
        message: "Bir hayvan belirlenen bölgenin dışına çıktı",
        createdAt: Date().addingTimeInterval(-7200),
        isRead: false
    ),
    AlertItem(
        type: .health,
        severity: .critical,
        title: "Acil Sağlık Uyarısı",
        message: "Bir hayvanın durumu kritik olabilir",
        createdAt: Date().addingTimeInterval(-14400),
        isRead: false
    ),
]

#Preview {
    AlertsView()
        .preferredColorScheme(.dark)
}
