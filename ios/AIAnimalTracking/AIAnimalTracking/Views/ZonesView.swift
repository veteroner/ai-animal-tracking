import SwiftUI
import MapKit

struct Zone: Identifiable {
    let id = UUID()
    let name: String
    let type: ZoneType
    let animalCount: Int
    let capacity: Int
    let coordinate: CLLocationCoordinate2D
}

enum ZoneType: String {
    case barn = "Ahır"
    case pasture = "Otlak"
    case coop = "Kümes"
    case milking = "Sağım"
    case quarantine = "Karantina"
    
    var color: Color {
        switch self {
        case .barn: return .brown
        case .pasture: return .green
        case .coop: return .yellow
        case .milking: return .blue
        case .quarantine: return .red
        }
    }
    
    var icon: String {
        switch self {
        case .barn: return "house.fill"
        case .pasture: return "leaf.fill"
        case .coop: return "bird.fill"
        case .milking: return "drop.fill"
        case .quarantine: return "exclamationmark.triangle.fill"
        }
    }
}

struct ZonesView: View {
    @State private var zones: [Zone] = []
    @State private var isLoading = true
    @State private var region = MKCoordinateRegion(
        center: CLLocationCoordinate2D(latitude: 39.9334, longitude: 32.8597),
        span: MKCoordinateSpan(latitudeDelta: 0.01, longitudeDelta: 0.01)
    )
    @State private var selectedView = 0
    
    var body: some View {
        NavigationView {
            ZStack {
                Color.black.ignoresSafeArea()
                
                VStack(spacing: 16) {
                    // Stats
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 12) {
                            ZoneStatCard(title: "Toplam Bölge", value: "\(zones.count)", icon: "map.fill", color: .blue)
                            ZoneStatCard(title: "Toplam Hayvan", value: "\(zones.reduce(0) { $0 + $1.animalCount })", icon: "pawprint.fill", color: .green)
                            ZoneStatCard(title: "Kapasite", value: "\(zones.reduce(0) { $0 + $1.capacity })", icon: "person.3.fill", color: .orange)
                        }
                        .padding(.horizontal)
                    }
                    
                    // View Picker
                    Picker("", selection: $selectedView) {
                        Text("Liste").tag(0)
                        Text("Harita").tag(1)
                    }
                    .pickerStyle(SegmentedPickerStyle())
                    .padding(.horizontal)
                    
                    if isLoading {
                        Spacer()
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .green))
                            .scaleEffect(1.5)
                        Spacer()
                    } else if selectedView == 0 {
                        // List View
                        ScrollView {
                            LazyVStack(spacing: 12) {
                                ForEach(zones) { zone in
                                    ZoneCard(zone: zone)
                                }
                            }
                            .padding(.horizontal)
                        }
                    } else {
                        // Map View
                        Map(coordinateRegion: $region, annotationItems: zones) { zone in
                            MapAnnotation(coordinate: zone.coordinate) {
                                VStack {
                                    ZStack {
                                        Circle()
                                            .fill(zone.type.color)
                                            .frame(width: 40, height: 40)
                                        Image(systemName: zone.type.icon)
                                            .foregroundColor(.white)
                                    }
                                    Text(zone.name)
                                        .font(.caption2)
                                        .foregroundColor(.white)
                                        .padding(4)
                                        .background(Color.black.opacity(0.7))
                                        .cornerRadius(4)
                                }
                            }
                        }
                        .cornerRadius(16)
                        .padding(.horizontal)
                    }
                }
                .padding(.top)
            }
            .navigationTitle("🗺️ Bölge Haritası")
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
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
            zones = [
                Zone(name: "Ana Ahır", type: .barn, animalCount: 45, capacity: 50, coordinate: CLLocationCoordinate2D(latitude: 39.9334, longitude: 32.8597)),
                Zone(name: "Kuzey Otlak", type: .pasture, animalCount: 30, capacity: 100, coordinate: CLLocationCoordinate2D(latitude: 39.9354, longitude: 32.8617)),
                Zone(name: "Tavuk Kümesi", type: .coop, animalCount: 200, capacity: 250, coordinate: CLLocationCoordinate2D(latitude: 39.9324, longitude: 32.8577)),
                Zone(name: "Sağım Ünitesi", type: .milking, animalCount: 12, capacity: 20, coordinate: CLLocationCoordinate2D(latitude: 39.9344, longitude: 32.8607)),
                Zone(name: "Karantina", type: .quarantine, animalCount: 3, capacity: 10, coordinate: CLLocationCoordinate2D(latitude: 39.9314, longitude: 32.8587)),
            ]
            
            // Center map on first zone
            if let firstZone = zones.first {
                region.center = firstZone.coordinate
            }
            isLoading = false
        }
    }
}

struct ZoneStatCard: View {
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
        .frame(width: 130)
        .background(Color.gray.opacity(0.2))
        .cornerRadius(12)
    }
}

struct ZoneCard: View {
    let zone: Zone
    
    var occupancyPercentage: Double {
        guard zone.capacity > 0 else { return 0 }
        return Double(zone.animalCount) / Double(zone.capacity)
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                ZStack {
                    Circle()
                        .fill(zone.type.color.opacity(0.2))
                        .frame(width: 44, height: 44)
                    Image(systemName: zone.type.icon)
                        .foregroundColor(zone.type.color)
                        .font(.title3)
                }
                
                VStack(alignment: .leading, spacing: 2) {
                    Text(zone.name)
                        .font(.headline)
                        .foregroundColor(.white)
                    Text(zone.type.rawValue)
                        .font(.caption)
                        .foregroundColor(.gray)
                }
                
                Spacer()
                
                VStack(alignment: .trailing, spacing: 2) {
                    Text("\(zone.animalCount)/\(zone.capacity)")
                        .font(.subheadline)
                        .fontWeight(.semibold)
                        .foregroundColor(.white)
                    Text("Doluluk")
                        .font(.caption2)
                        .foregroundColor(.gray)
                }
            }
            
            // Occupancy bar
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    Rectangle()
                        .fill(Color.gray.opacity(0.3))
                        .frame(height: 8)
                        .cornerRadius(4)
                    
                    Rectangle()
                        .fill(occupancyPercentage > 0.9 ? Color.red : (occupancyPercentage > 0.7 ? Color.orange : Color.green))
                        .frame(width: geo.size.width * occupancyPercentage, height: 8)
                        .cornerRadius(4)
                }
            }
            .frame(height: 8)
        }
        .padding()
        .background(Color.gray.opacity(0.15))
        .cornerRadius(16)
    }
}

#Preview {
    ZonesView()
        .preferredColorScheme(.dark)
}
