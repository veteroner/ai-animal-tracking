import SwiftUI

struct Coop: Identifiable {
    let id = UUID()
    let name: String
    let chickenCount: Int
    let todayEggs: Int
    let weeklyEggs: Int
    let temperature: Double
    let humidity: Double
    let status: CoopStatus
}

enum CoopStatus: String {
    case normal = "Normal"
    case warning = "Uyarı"
    case critical = "Kritik"
    
    var color: Color {
        switch self {
        case .normal: return .green
        case .warning: return .orange
        case .critical: return .red
        }
    }
}

struct PoultryView: View {
    @State private var coops: [Coop] = []
    @State private var isLoading = true
    @State private var totalEggsToday = 0
    @State private var totalChickens = 0
    
    var body: some View {
        NavigationView {
            ZStack {
                Color.black.ignoresSafeArea()
                
                VStack(spacing: 16) {
                    // Overview Stats
                    HStack(spacing: 12) {
                        PoultryStatCard(
                            title: "Bugün Yumurta",
                            value: "\(totalEggsToday)",
                            icon: "circle.fill",
                            color: .orange
                        )
                        PoultryStatCard(
                            title: "Toplam Tavuk",
                            value: "\(totalChickens)",
                            icon: "bird.fill",
                            color: .yellow
                        )
                        PoultryStatCard(
                            title: "Kümes",
                            value: "\(coops.count)",
                            icon: "house.fill",
                            color: .blue
                        )
                    }
                    .padding(.horizontal)
                    
                    // Coops List
                    if isLoading {
                        Spacer()
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .orange))
                            .scaleEffect(1.5)
                        Spacer()
                    } else {
                        ScrollView {
                            LazyVStack(spacing: 12) {
                                ForEach(coops) { coop in
                                    CoopCard(coop: coop)
                                }
                            }
                            .padding(.horizontal)
                        }
                    }
                }
                .padding(.top)
            }
            .navigationTitle("🐔 Kanatlı Takibi")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { loadData() }) {
                        Image(systemName: "arrow.clockwise")
                            .foregroundColor(.orange)
                    }
                }
            }
        }
        .onAppear { loadData() }
    }
    
    func loadData() {
        isLoading = true
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
            coops = [
                Coop(name: "Kümes 1 - Yumurtacı", chickenCount: 150, todayEggs: 142, weeklyEggs: 980, temperature: 22.5, humidity: 65, status: .normal),
                Coop(name: "Kümes 2 - Yumurtacı", chickenCount: 120, todayEggs: 98, weeklyEggs: 750, temperature: 24.8, humidity: 72, status: .warning),
                Coop(name: "Kümes 3 - Etlik", chickenCount: 200, todayEggs: 0, weeklyEggs: 0, temperature: 21.2, humidity: 60, status: .normal),
                Coop(name: "Kümes 4 - Civciv", chickenCount: 80, todayEggs: 0, weeklyEggs: 0, temperature: 32.0, humidity: 55, status: .normal),
            ]
            totalEggsToday = coops.reduce(0) { $0 + $1.todayEggs }
            totalChickens = coops.reduce(0) { $0 + $1.chickenCount }
            isLoading = false
        }
    }
}

struct PoultryStatCard: View {
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
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(Color.gray.opacity(0.2))
        .cornerRadius(12)
    }
}

struct CoopCard: View {
    let coop: Coop
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "house.fill")
                    .foregroundColor(.yellow)
                    .font(.title2)
                
                Text(coop.name)
                    .font(.headline)
                    .foregroundColor(.white)
                
                Spacer()
                
                Text(coop.status.rawValue)
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundColor(coop.status.color)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(coop.status.color.opacity(0.2))
                    .cornerRadius(8)
            }
            
            Divider().background(Color.gray.opacity(0.3))
            
            HStack(spacing: 20) {
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Image(systemName: "bird.fill")
                            .foregroundColor(.yellow)
                            .font(.caption)
                        Text("\(coop.chickenCount)")
                            .fontWeight(.semibold)
                            .foregroundColor(.white)
                    }
                    Text("Tavuk")
                        .font(.caption2)
                        .foregroundColor(.gray)
                }
                
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text("🥚")
                            .font(.caption)
                        Text("\(coop.todayEggs)")
                            .fontWeight(.semibold)
                            .foregroundColor(.orange)
                    }
                    Text("Bugün")
                        .font(.caption2)
                        .foregroundColor(.gray)
                }
                
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text("🥚")
                            .font(.caption)
                        Text("\(coop.weeklyEggs)")
                            .fontWeight(.semibold)
                            .foregroundColor(.white)
                    }
                    Text("Haftalık")
                        .font(.caption2)
                        .foregroundColor(.gray)
                }
            }
            
            Divider().background(Color.gray.opacity(0.3))
            
            HStack {
                HStack(spacing: 4) {
                    Image(systemName: "thermometer")
                        .foregroundColor(coop.temperature > 25 ? .red : .green)
                        .font(.caption)
                    Text(String(format: "%.1f°C", coop.temperature))
                        .font(.subheadline)
                        .foregroundColor(coop.temperature > 25 ? .red : .white)
                }
                
                Spacer()
                
                HStack(spacing: 4) {
                    Image(systemName: "humidity.fill")
                        .foregroundColor(coop.humidity > 70 ? .orange : .blue)
                        .font(.caption)
                    Text(String(format: "%.0f%%", coop.humidity))
                        .font(.subheadline)
                        .foregroundColor(coop.humidity > 70 ? .orange : .white)
                }
            }
            
            if coop.todayEggs > 0 {
                // Egg production bar
                VStack(alignment: .leading, spacing: 4) {
                    Text("Verimlilik")
                        .font(.caption)
                        .foregroundColor(.gray)
                    GeometryReader { geo in
                        ZStack(alignment: .leading) {
                            Rectangle()
                                .fill(Color.gray.opacity(0.3))
                                .frame(height: 6)
                                .cornerRadius(3)
                            
                            Rectangle()
                                .fill(Color.orange)
                                .frame(width: geo.size.width * CGFloat(coop.todayEggs) / CGFloat(coop.chickenCount), height: 6)
                                .cornerRadius(3)
                        }
                    }
                    .frame(height: 6)
                }
            }
        }
        .padding()
        .background(Color.gray.opacity(0.15))
        .cornerRadius(16)
    }
}

#Preview {
    PoultryView()
        .preferredColorScheme(.dark)
}
