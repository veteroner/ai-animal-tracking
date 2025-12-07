import SwiftUI

struct HealthRecord: Identifiable {
    let id = UUID()
    let animalId: String
    let animalName: String
    let type: String
    let date: Date
    let status: HealthStatus
    let description: String
    let veterinarian: String
}

enum HealthStatus: String {
    case healthy = "Sağlıklı"
    case sick = "Hasta"
    case recovering = "İyileşiyor"
    case critical = "Kritik"
    
    var color: Color {
        switch self {
        case .healthy: return .green
        case .sick: return .red
        case .recovering: return .orange
        case .critical: return .purple
        }
    }
    
    var icon: String {
        switch self {
        case .healthy: return "checkmark.circle.fill"
        case .sick: return "cross.circle.fill"
        case .recovering: return "arrow.up.circle.fill"
        case .critical: return "exclamationmark.triangle.fill"
        }
    }
}

struct HealthView: View {
    @State private var healthRecords: [HealthRecord] = []
    @State private var isLoading = true
    @State private var selectedFilter: HealthStatus? = nil
    @State private var searchText = ""
    
    var filteredRecords: [HealthRecord] {
        var records = healthRecords
        if let filter = selectedFilter {
            records = records.filter { $0.status == filter }
        }
        if !searchText.isEmpty {
            records = records.filter { $0.animalName.localizedCaseInsensitiveContains(searchText) }
        }
        return records
    }
    
    var body: some View {
        NavigationView {
            ZStack {
                Color.black.ignoresSafeArea()
                
                VStack(spacing: 16) {
                    // Stats Cards
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 12) {
                            StatCard(title: "Sağlıklı", value: "\(healthRecords.filter { $0.status == .healthy }.count)", icon: "checkmark.circle.fill", color: .green)
                            StatCard(title: "Hasta", value: "\(healthRecords.filter { $0.status == .sick }.count)", icon: "cross.circle.fill", color: .red)
                            StatCard(title: "İyileşiyor", value: "\(healthRecords.filter { $0.status == .recovering }.count)", icon: "arrow.up.circle.fill", color: .orange)
                            StatCard(title: "Kritik", value: "\(healthRecords.filter { $0.status == .critical }.count)", icon: "exclamationmark.triangle.fill", color: .purple)
                        }
                        .padding(.horizontal)
                    }
                    
                    // Search Bar
                    HStack {
                        Image(systemName: "magnifyingglass")
                            .foregroundColor(.gray)
                        TextField("Hayvan ara...", text: $searchText)
                            .foregroundColor(.white)
                    }
                    .padding()
                    .background(Color.gray.opacity(0.2))
                    .cornerRadius(12)
                    .padding(.horizontal)
                    
                    // Filter Buttons
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            FilterButton(title: "Tümü", isSelected: selectedFilter == nil) {
                                selectedFilter = nil
                            }
                            FilterButton(title: "Sağlıklı", isSelected: selectedFilter == .healthy) {
                                selectedFilter = .healthy
                            }
                            FilterButton(title: "Hasta", isSelected: selectedFilter == .sick) {
                                selectedFilter = .sick
                            }
                            FilterButton(title: "İyileşiyor", isSelected: selectedFilter == .recovering) {
                                selectedFilter = .recovering
                            }
                            FilterButton(title: "Kritik", isSelected: selectedFilter == .critical) {
                                selectedFilter = .critical
                            }
                        }
                        .padding(.horizontal)
                    }
                    
                    // Records List
                    if isLoading {
                        Spacer()
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .green))
                            .scaleEffect(1.5)
                        Spacer()
                    } else if filteredRecords.isEmpty {
                        Spacer()
                        VStack(spacing: 12) {
                            Image(systemName: "heart.text.square")
                                .font(.system(size: 60))
                                .foregroundColor(.gray)
                            Text("Sağlık kaydı bulunamadı")
                                .foregroundColor(.gray)
                        }
                        Spacer()
                    } else {
                        ScrollView {
                            LazyVStack(spacing: 12) {
                                ForEach(filteredRecords) { record in
                                    HealthRecordCard(record: record)
                                }
                            }
                            .padding(.horizontal)
                        }
                    }
                }
                .padding(.top)
            }
            .navigationTitle("🏥 Sağlık Takibi")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { loadData() }) {
                        Image(systemName: "arrow.clockwise")
                            .foregroundColor(.green)
                    }
                }
            }
        }
        .onAppear { loadData() }
    }
    
    func loadData() {
        isLoading = true
        // Simulated data
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
            healthRecords = [
                HealthRecord(animalId: "COW-001", animalName: "Sarıkız", type: "Aşı", date: Date(), status: .healthy, description: "Yıllık aşı yapıldı", veterinarian: "Dr. Mehmet"),
                HealthRecord(animalId: "COW-002", animalName: "Benekli", type: "Muayene", date: Date().addingTimeInterval(-86400), status: .sick, description: "Ateş ve iştahsızlık", veterinarian: "Dr. Ayşe"),
                HealthRecord(animalId: "COW-003", animalName: "Karabaş", type: "Tedavi", date: Date().addingTimeInterval(-172800), status: .recovering, description: "Antibiyotik tedavisi devam ediyor", veterinarian: "Dr. Mehmet"),
                HealthRecord(animalId: "SHEEP-001", animalName: "Pamuk", type: "Acil", date: Date().addingTimeInterval(-3600), status: .critical, description: "Doğum komplikasyonu", veterinarian: "Dr. Ayşe"),
            ]
            isLoading = false
        }
    }
}

struct StatCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: icon)
                    .foregroundColor(color)
                Spacer()
                Text(value)
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundColor(.white)
            }
            Text(title)
                .font(.caption)
                .foregroundColor(.gray)
        }
        .padding()
        .frame(width: 120)
        .background(Color.gray.opacity(0.2))
        .cornerRadius(12)
    }
}

struct FilterButton: View {
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
                .background(isSelected ? Color.green : Color.gray.opacity(0.3))
                .cornerRadius(20)
        }
    }
}

struct HealthRecordCard: View {
    let record: HealthRecord
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: record.status.icon)
                    .foregroundColor(record.status.color)
                    .font(.title2)
                
                VStack(alignment: .leading, spacing: 2) {
                    Text(record.animalName)
                        .font(.headline)
                        .foregroundColor(.white)
                    Text(record.animalId)
                        .font(.caption)
                        .foregroundColor(.gray)
                }
                
                Spacer()
                
                Text(record.status.rawValue)
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundColor(record.status.color)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(record.status.color.opacity(0.2))
                    .cornerRadius(8)
            }
            
            Text(record.description)
                .font(.subheadline)
                .foregroundColor(.gray)
            
            HStack {
                Label(record.type, systemImage: "stethoscope")
                    .font(.caption)
                    .foregroundColor(.gray)
                
                Spacer()
                
                Label(record.veterinarian, systemImage: "person.fill")
                    .font(.caption)
                    .foregroundColor(.gray)
                
                Spacer()
                
                Label(record.date.formatted(date: .abbreviated, time: .omitted), systemImage: "calendar")
                    .font(.caption)
                    .foregroundColor(.gray)
            }
        }
        .padding()
        .background(Color.gray.opacity(0.15))
        .cornerRadius(16)
    }
}

#Preview {
    HealthView()
        .preferredColorScheme(.dark)
}
