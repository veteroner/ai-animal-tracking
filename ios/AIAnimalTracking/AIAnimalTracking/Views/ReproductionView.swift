import SwiftUI

struct ReproductionRecord: Identifiable {
    let id = UUID()
    let animalId: String
    let animalName: String
    let status: ReproductionStatus
    let lastEstrus: Date?
    let nextEstrus: Date?
    let pregnancyDay: Int?
    let expectedBirth: Date?
}

enum ReproductionStatus: String {
    case open = "Boşta"
    case estrus = "Kızgınlık"
    case pregnant = "Gebe"
    case lactating = "Laktasyon"
    
    var color: Color {
        switch self {
        case .open: return .gray
        case .estrus: return .pink
        case .pregnant: return .blue
        case .lactating: return .purple
        }
    }
    
    var icon: String {
        switch self {
        case .open: return "circle"
        case .estrus: return "heart.fill"
        case .pregnant: return "person.crop.circle.badge.clock"
        case .lactating: return "drop.fill"
        }
    }
}

struct ReproductionView: View {
    @State private var records: [ReproductionRecord] = []
    @State private var isLoading = true
    @State private var selectedTab = 0
    
    var body: some View {
        NavigationView {
            ZStack {
                Color.black.ignoresSafeArea()
                
                VStack(spacing: 16) {
                    // Stats Overview
                    HStack(spacing: 12) {
                        ReproStatCard(title: "Kızgınlık", count: records.filter { $0.status == .estrus }.count, icon: "heart.fill", color: .pink)
                        ReproStatCard(title: "Gebe", count: records.filter { $0.status == .pregnant }.count, icon: "person.crop.circle.badge.clock", color: .blue)
                        ReproStatCard(title: "Laktasyon", count: records.filter { $0.status == .lactating }.count, icon: "drop.fill", color: .purple)
                    }
                    .padding(.horizontal)
                    
                    // Segment Control
                    Picker("", selection: $selectedTab) {
                        Text("Kızgınlık").tag(0)
                        Text("Gebelik").tag(1)
                        Text("Tümü").tag(2)
                    }
                    .pickerStyle(SegmentedPickerStyle())
                    .padding(.horizontal)
                    
                    // Content
                    if isLoading {
                        Spacer()
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .pink))
                            .scaleEffect(1.5)
                        Spacer()
                    } else {
                        ScrollView {
                            LazyVStack(spacing: 12) {
                                ForEach(filteredRecords) { record in
                                    ReproductionCard(record: record)
                                }
                            }
                            .padding(.horizontal)
                        }
                    }
                }
                .padding(.top)
            }
            .navigationTitle("💕 Üreme Takibi")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { loadData() }) {
                        Image(systemName: "arrow.clockwise")
                            .foregroundColor(.pink)
                    }
                }
            }
        }
        .onAppear { loadData() }
    }
    
    var filteredRecords: [ReproductionRecord] {
        switch selectedTab {
        case 0: return records.filter { $0.status == .estrus }
        case 1: return records.filter { $0.status == .pregnant }
        default: return records
        }
    }
    
    func loadData() {
        isLoading = true
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
            records = [
                ReproductionRecord(animalId: "COW-001", animalName: "Sarıkız", status: .estrus, lastEstrus: Date(), nextEstrus: Date().addingTimeInterval(21*86400), pregnancyDay: nil, expectedBirth: nil),
                ReproductionRecord(animalId: "COW-002", animalName: "Benekli", status: .pregnant, lastEstrus: Date().addingTimeInterval(-60*86400), nextEstrus: nil, pregnancyDay: 120, expectedBirth: Date().addingTimeInterval(160*86400)),
                ReproductionRecord(animalId: "COW-003", animalName: "Karabaş", status: .lactating, lastEstrus: nil, nextEstrus: Date().addingTimeInterval(45*86400), pregnancyDay: nil, expectedBirth: nil),
                ReproductionRecord(animalId: "COW-004", animalName: "Alaca", status: .open, lastEstrus: Date().addingTimeInterval(-10*86400), nextEstrus: Date().addingTimeInterval(11*86400), pregnancyDay: nil, expectedBirth: nil),
                ReproductionRecord(animalId: "COW-005", animalName: "Boncuk", status: .estrus, lastEstrus: Date().addingTimeInterval(-1*86400), nextEstrus: Date().addingTimeInterval(20*86400), pregnancyDay: nil, expectedBirth: nil),
            ]
            isLoading = false
        }
    }
}

struct ReproStatCard: View {
    let title: String
    let count: Int
    let icon: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(color)
            Text("\(count)")
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

struct ReproductionCard: View {
    let record: ReproductionRecord
    
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
            
            Divider().background(Color.gray.opacity(0.3))
            
            if record.status == .pregnant, let day = record.pregnancyDay {
                HStack {
                    VStack(alignment: .leading) {
                        Text("Gebelik Günü")
                            .font(.caption)
                            .foregroundColor(.gray)
                        Text("\(day). gün")
                            .font(.subheadline)
                            .fontWeight(.semibold)
                            .foregroundColor(.blue)
                    }
                    
                    Spacer()
                    
                    if let expected = record.expectedBirth {
                        VStack(alignment: .trailing) {
                            Text("Tahmini Doğum")
                                .font(.caption)
                                .foregroundColor(.gray)
                            Text(expected.formatted(date: .abbreviated, time: .omitted))
                                .font(.subheadline)
                                .fontWeight(.semibold)
                                .foregroundColor(.green)
                        }
                    }
                }
                
                // Progress bar
                GeometryReader { geo in
                    ZStack(alignment: .leading) {
                        Rectangle()
                            .fill(Color.gray.opacity(0.3))
                            .frame(height: 8)
                            .cornerRadius(4)
                        
                        Rectangle()
                            .fill(Color.blue)
                            .frame(width: geo.size.width * CGFloat(day) / 280, height: 8)
                            .cornerRadius(4)
                    }
                }
                .frame(height: 8)
            }
            
            if record.status == .estrus {
                HStack {
                    Image(systemName: "exclamationmark.circle.fill")
                        .foregroundColor(.pink)
                    Text("Tohumlama için ideal zaman!")
                        .font(.subheadline)
                        .foregroundColor(.pink)
                }
            }
            
            if let nextEstrus = record.nextEstrus, record.status != .pregnant {
                HStack {
                    Image(systemName: "calendar")
                        .foregroundColor(.gray)
                    Text("Sonraki kızgınlık: \(nextEstrus.formatted(date: .abbreviated, time: .omitted))")
                        .font(.caption)
                        .foregroundColor(.gray)
                }
            }
        }
        .padding()
        .background(Color.gray.opacity(0.15))
        .cornerRadius(16)
    }
}

#Preview {
    ReproductionView()
        .preferredColorScheme(.dark)
}
