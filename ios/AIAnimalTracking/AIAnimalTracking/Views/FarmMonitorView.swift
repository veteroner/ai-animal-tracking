import SwiftUI

struct CameraFeed: Identifiable {
    let id = UUID()
    let name: String
    let url: String
    let status: CameraStatus
    let fps: Int
    let animalsDetected: Int
    let eventsCount: Int
}

enum CameraStatus: String {
    case active = "Aktif"
    case inactive = "Pasif"
    case error = "Hata"
    
    var color: Color {
        switch self {
        case .active: return .green
        case .inactive: return .gray
        case .error: return .red
        }
    }
}

struct FarmMonitorView: View {
    @State private var isMonitoring = false
    @State private var cameras: [CameraFeed] = []
    @State private var isLoading = true
    @State private var showAddCamera = false
    @State private var newCameraName = ""
    @State private var newCameraUrl = ""
    @State private var totalDetections = 0
    @State private var eventsToday = 0
    
    var body: some View {
        NavigationView {
            ZStack {
                Color.black.ignoresSafeArea()
                
                VStack(spacing: 16) {
                    // Status Bar
                    HStack {
                        HStack(spacing: 8) {
                            Circle()
                                .fill(isMonitoring ? Color.green : Color.gray)
                                .frame(width: 12, height: 12)
                            Text(isMonitoring ? "Çalışıyor" : "Durduruldu")
                                .font(.subheadline)
                                .foregroundColor(isMonitoring ? .green : .gray)
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(Color.gray.opacity(0.2))
                        .cornerRadius(20)
                        
                        Spacer()
                        
                        Button(action: { isMonitoring.toggle() }) {
                            HStack {
                                Image(systemName: isMonitoring ? "stop.fill" : "play.fill")
                                Text(isMonitoring ? "Durdur" : "Başlat")
                            }
                            .font(.subheadline)
                            .fontWeight(.semibold)
                            .foregroundColor(.white)
                            .padding(.horizontal, 16)
                            .padding(.vertical, 8)
                            .background(isMonitoring ? Color.red : Color.green)
                            .cornerRadius(20)
                        }
                    }
                    .padding(.horizontal)
                    
                    // Stats
                    HStack(spacing: 12) {
                        MonitorStatCard(title: "Kameralar", value: "\(cameras.filter { $0.status == .active }.count)/\(cameras.count)", icon: "video.fill", color: .blue)
                        MonitorStatCard(title: "Tespit", value: "\(totalDetections)", icon: "eye.fill", color: .purple)
                        MonitorStatCard(title: "Olay", value: "\(eventsToday)", icon: "exclamationmark.triangle.fill", color: .orange)
                    }
                    .padding(.horizontal)
                    
                    // Camera List
                    if isLoading {
                        Spacer()
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .green))
                            .scaleEffect(1.5)
                        Spacer()
                    } else if cameras.isEmpty {
                        Spacer()
                        VStack(spacing: 16) {
                            Image(systemName: "video.slash")
                                .font(.system(size: 60))
                                .foregroundColor(.gray)
                            Text("Henüz kamera eklenmemiş")
                                .foregroundColor(.gray)
                            Button(action: { showAddCamera = true }) {
                                HStack {
                                    Image(systemName: "plus.circle.fill")
                                    Text("Kamera Ekle")
                                }
                                .foregroundColor(.green)
                            }
                        }
                        Spacer()
                    } else {
                        ScrollView {
                            LazyVStack(spacing: 12) {
                                ForEach(cameras) { camera in
                                    CameraCard(camera: camera, onDelete: { deleteCamera(camera) })
                                }
                            }
                            .padding(.horizontal)
                        }
                    }
                    
                    // How it works
                    if !cameras.isEmpty {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("🤖 Yapay Zeka Özellikleri")
                                .font(.headline)
                                .foregroundColor(.white)
                            
                            HStack(spacing: 8) {
                                FeatureTag(text: "YOLOv8", color: .green)
                                FeatureTag(text: "Re-ID", color: .blue)
                                FeatureTag(text: "Davranış", color: .purple)
                                FeatureTag(text: "Kızgınlık", color: .pink)
                            }
                        }
                        .padding()
                        .background(Color.gray.opacity(0.15))
                        .cornerRadius(12)
                        .padding(.horizontal)
                    }
                }
                .padding(.top)
            }
            .navigationTitle("📹 Çiftlik İzleme")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { showAddCamera = true }) {
                        Image(systemName: "plus")
                            .foregroundColor(.green)
                    }
                }
            }
            .sheet(isPresented: $showAddCamera) {
                AddCameraSheet(
                    name: $newCameraName,
                    url: $newCameraUrl,
                    onAdd: addCamera,
                    onCancel: { showAddCamera = false }
                )
            }
        }
        .onAppear { loadData() }
    }
    
    func loadData() {
        isLoading = true
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
            cameras = [
                CameraFeed(name: "Ahır Kamerası 1", url: "rtsp://192.168.1.100:554/stream1", status: .active, fps: 25, animalsDetected: 12, eventsCount: 3),
                CameraFeed(name: "Otlak Kamerası", url: "rtsp://192.168.1.101:554/stream1", status: .active, fps: 20, animalsDetected: 28, eventsCount: 1),
                CameraFeed(name: "Kümes Kamerası", url: "rtsp://192.168.1.102:554/stream1", status: .inactive, fps: 0, animalsDetected: 0, eventsCount: 0),
            ]
            totalDetections = cameras.reduce(0) { $0 + $1.animalsDetected }
            eventsToday = cameras.reduce(0) { $0 + $1.eventsCount }
            isLoading = false
        }
    }
    
    func addCamera() {
        guard !newCameraName.isEmpty, !newCameraUrl.isEmpty else { return }
        let newCamera = CameraFeed(name: newCameraName, url: newCameraUrl, status: .inactive, fps: 0, animalsDetected: 0, eventsCount: 0)
        cameras.append(newCamera)
        newCameraName = ""
        newCameraUrl = ""
        showAddCamera = false
    }
    
    func deleteCamera(_ camera: CameraFeed) {
        cameras.removeAll { $0.id == camera.id }
    }
}

struct MonitorStatCard: View {
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
                .font(.title2)
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

struct CameraCard: View {
    let camera: CameraFeed
    let onDelete: () -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Circle()
                    .fill(camera.status.color)
                    .frame(width: 10, height: 10)
                
                Text(camera.name)
                    .font(.headline)
                    .foregroundColor(.white)
                
                Spacer()
                
                Button(action: onDelete) {
                    Image(systemName: "trash")
                        .foregroundColor(.red)
                }
            }
            
            Text(camera.url)
                .font(.caption)
                .foregroundColor(.gray)
                .lineLimit(1)
            
            HStack(spacing: 16) {
                HStack(spacing: 4) {
                    Image(systemName: "speedometer")
                        .font(.caption)
                        .foregroundColor(.gray)
                    Text("\(camera.fps) FPS")
                        .font(.caption)
                        .foregroundColor(.white)
                }
                
                HStack(spacing: 4) {
                    Image(systemName: "pawprint.fill")
                        .font(.caption)
                        .foregroundColor(.gray)
                    Text("\(camera.animalsDetected)")
                        .font(.caption)
                        .foregroundColor(.white)
                }
                
                HStack(spacing: 4) {
                    Image(systemName: "bell.fill")
                        .font(.caption)
                        .foregroundColor(.gray)
                    Text("\(camera.eventsCount)")
                        .font(.caption)
                        .foregroundColor(.white)
                }
            }
        }
        .padding()
        .background(Color.gray.opacity(0.15))
        .cornerRadius(16)
    }
}

struct FeatureTag: View {
    let text: String
    let color: Color
    
    var body: some View {
        Text(text)
            .font(.caption)
            .fontWeight(.medium)
            .foregroundColor(color)
            .padding(.horizontal, 10)
            .padding(.vertical, 4)
            .background(color.opacity(0.2))
            .cornerRadius(8)
    }
}

struct AddCameraSheet: View {
    @Binding var name: String
    @Binding var url: String
    let onAdd: () -> Void
    let onCancel: () -> Void
    
    var body: some View {
        NavigationView {
            ZStack {
                Color.black.ignoresSafeArea()
                
                VStack(spacing: 20) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Kamera Adı")
                            .font(.headline)
                            .foregroundColor(.white)
                        TextField("Örn: Ahır Kamerası 1", text: $name)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                    }
                    
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Kamera URL (RTSP/HTTP)")
                            .font(.headline)
                            .foregroundColor(.white)
                        TextField("rtsp://kullanici:sifre@192.168.1.100:554/stream", text: $url)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .autocapitalization(.none)
                    }
                    
                    VStack(alignment: .leading, spacing: 8) {
                        Text("📌 Örnek URL Formatları")
                            .font(.subheadline)
                            .foregroundColor(.gray)
                        
                        Text("RTSP: rtsp://admin:password@192.168.1.100:554/stream1")
                            .font(.caption)
                            .foregroundColor(.gray)
                        Text("HTTP: http://192.168.1.100:8080/video")
                            .font(.caption)
                            .foregroundColor(.gray)
                    }
                    .padding()
                    .background(Color.gray.opacity(0.15))
                    .cornerRadius(12)
                    
                    Spacer()
                    
                    Button(action: onAdd) {
                        Text("Kamera Ekle")
                            .font(.headline)
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(name.isEmpty || url.isEmpty ? Color.gray : Color.green)
                            .cornerRadius(12)
                    }
                    .disabled(name.isEmpty || url.isEmpty)
                }
                .padding()
            }
            .navigationTitle("Yeni Kamera")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("İptal", action: onCancel)
                        .foregroundColor(.red)
                }
            }
        }
    }
}

#Preview {
    FarmMonitorView()
        .preferredColorScheme(.dark)
}
