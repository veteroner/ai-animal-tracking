import SwiftUI

struct Report: Identifiable {
    let id = UUID()
    let title: String
    let type: ReportType
    let date: Date
    let status: ReportStatus
    let summary: String
}

enum ReportType: String {
    case daily = "Günlük"
    case weekly = "Haftalık"
    case monthly = "Aylık"
    case health = "Sağlık"
    case production = "Üretim"
    
    var icon: String {
        switch self {
        case .daily: return "calendar.day.timeline.left"
        case .weekly: return "calendar"
        case .monthly: return "calendar.badge.clock"
        case .health: return "heart.text.square"
        case .production: return "chart.bar.fill"
        }
    }
    
    var color: Color {
        switch self {
        case .daily: return .blue
        case .weekly: return .green
        case .monthly: return .purple
        case .health: return .red
        case .production: return .orange
        }
    }
}

enum ReportStatus: String {
    case ready = "Hazır"
    case generating = "Oluşturuluyor"
    case error = "Hata"
    
    var color: Color {
        switch self {
        case .ready: return .green
        case .generating: return .orange
        case .error: return .red
        }
    }
}

struct ReportsView: View {
    @State private var reports: [Report] = []
    @State private var isLoading = true
    @State private var selectedType: ReportType? = nil
    
    var filteredReports: [Report] {
        if let type = selectedType {
            return reports.filter { $0.type == type }
        }
        return reports
    }
    
    var body: some View {
        NavigationView {
            ZStack {
                Color.black.ignoresSafeArea()
                
                VStack(spacing: 16) {
                    // Quick Stats
                    HStack(spacing: 12) {
                        ReportStatCard(title: "Toplam", value: "\(reports.count)", icon: "doc.fill", color: .blue)
                        ReportStatCard(title: "Bu Hafta", value: "\(reports.filter { Calendar.current.isDate($0.date, equalTo: Date(), toGranularity: .weekOfYear) }.count)", icon: "calendar", color: .green)
                        ReportStatCard(title: "Hazır", value: "\(reports.filter { $0.status == .ready }.count)", icon: "checkmark.circle.fill", color: .purple)
                    }
                    .padding(.horizontal)
                    
                    // Filter
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            ReportFilterButton(title: "Tümü", isSelected: selectedType == nil) {
                                selectedType = nil
                            }
                            ReportFilterButton(title: "Günlük", isSelected: selectedType == .daily) {
                                selectedType = .daily
                            }
                            ReportFilterButton(title: "Haftalık", isSelected: selectedType == .weekly) {
                                selectedType = .weekly
                            }
                            ReportFilterButton(title: "Aylık", isSelected: selectedType == .monthly) {
                                selectedType = .monthly
                            }
                            ReportFilterButton(title: "Sağlık", isSelected: selectedType == .health) {
                                selectedType = .health
                            }
                            ReportFilterButton(title: "Üretim", isSelected: selectedType == .production) {
                                selectedType = .production
                            }
                        }
                        .padding(.horizontal)
                    }
                    
                    // Reports List
                    if isLoading {
                        Spacer()
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .blue))
                            .scaleEffect(1.5)
                        Spacer()
                    } else if filteredReports.isEmpty {
                        Spacer()
                        VStack(spacing: 12) {
                            Image(systemName: "doc.text.magnifyingglass")
                                .font(.system(size: 60))
                                .foregroundColor(.gray)
                            Text("Rapor bulunamadı")
                                .foregroundColor(.gray)
                        }
                        Spacer()
                    } else {
                        ScrollView {
                            LazyVStack(spacing: 12) {
                                ForEach(filteredReports) { report in
                                    ReportCard(report: report)
                                }
                            }
                            .padding(.horizontal)
                        }
                    }
                    
                    // Generate Report Button
                    Button(action: { generateReport() }) {
                        HStack {
                            Image(systemName: "plus.circle.fill")
                            Text("Yeni Rapor Oluştur")
                        }
                        .font(.headline)
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.blue)
                        .cornerRadius(12)
                    }
                    .padding(.horizontal)
                    .padding(.bottom)
                }
                .padding(.top)
            }
            .navigationTitle("📊 Raporlar")
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
            reports = [
                Report(title: "Günlük Özet - 7 Aralık", type: .daily, date: Date(), status: .ready, summary: "Toplam 45 hayvan izlendi, 3 sağlık uyarısı"),
                Report(title: "Haftalık Üretim Raporu", type: .weekly, date: Date().addingTimeInterval(-86400), status: .ready, summary: "980 yumurta üretildi, verimlilik %94"),
                Report(title: "Aylık Sağlık Raporu", type: .health, date: Date().addingTimeInterval(-172800), status: .ready, summary: "12 aşı yapıldı, 2 tedavi tamamlandı"),
                Report(title: "Süt Üretim Analizi", type: .production, date: Date().addingTimeInterval(-259200), status: .ready, summary: "Günlük ortalama 450L süt"),
                Report(title: "Kasım Ayı Raporu", type: .monthly, date: Date().addingTimeInterval(-604800), status: .ready, summary: "Detaylı aylık performans analizi"),
            ]
            isLoading = false
        }
    }
    
    func generateReport() {
        // Add generating report
        let newReport = Report(title: "Yeni Rapor", type: .daily, date: Date(), status: .generating, summary: "Rapor oluşturuluyor...")
        reports.insert(newReport, at: 0)
    }
}

struct ReportStatCard: View {
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

struct ReportFilterButton: View {
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

struct ReportCard: View {
    let report: Report
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                ZStack {
                    Circle()
                        .fill(report.type.color.opacity(0.2))
                        .frame(width: 44, height: 44)
                    Image(systemName: report.type.icon)
                        .foregroundColor(report.type.color)
                        .font(.title3)
                }
                
                VStack(alignment: .leading, spacing: 2) {
                    Text(report.title)
                        .font(.headline)
                        .foregroundColor(.white)
                    Text(report.type.rawValue)
                        .font(.caption)
                        .foregroundColor(.gray)
                }
                
                Spacer()
                
                Text(report.status.rawValue)
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundColor(report.status.color)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(report.status.color.opacity(0.2))
                    .cornerRadius(8)
            }
            
            Text(report.summary)
                .font(.subheadline)
                .foregroundColor(.gray)
            
            HStack {
                Image(systemName: "calendar")
                    .foregroundColor(.gray)
                    .font(.caption)
                Text(report.date.formatted(date: .abbreviated, time: .shortened))
                    .font(.caption)
                    .foregroundColor(.gray)
                
                Spacer()
                
                if report.status == .ready {
                    Button(action: {}) {
                        HStack(spacing: 4) {
                            Image(systemName: "square.and.arrow.down")
                            Text("İndir")
                        }
                        .font(.caption)
                        .foregroundColor(.blue)
                    }
                }
            }
        }
        .padding()
        .background(Color.gray.opacity(0.15))
        .cornerRadius(16)
    }
}

#Preview {
    ReportsView()
        .preferredColorScheme(.dark)
}
