import SwiftUI
import AVFoundation

struct CameraView: View {
    @StateObject private var cameraManager = CameraManager()
    @StateObject private var apiService = APIService.shared
    
    @State private var isProcessing = false
    @State private var result: ProcessResult?
    @State private var totalRegistered = 0
    @State private var fps: Double = 0
    @State private var showResetAlert = false
    @State private var hasPermission = false
    
    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()
            
            if hasPermission {
                cameraContent
            } else {
                permissionView
            }
        }
        .navigationTitle("Canlı Tespit")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            Task {
                hasPermission = await cameraManager.checkPermission()
                if hasPermission {
                    cameraManager.setupSession()
                    setupFrameHandler()
                }
            }
        }
        .onDisappear {
            cameraManager.stopCapture()
        }
        .alert("Galeriyi Sıfırla", isPresented: $showResetAlert) {
            Button("İptal", role: .cancel) { }
            Button("Sıfırla", role: .destructive) {
                Task {
                    if await apiService.resetGallery() {
                        totalRegistered = 0
                        result = nil
                    }
                }
            }
        } message: {
            Text("Tüm kayıtlı hayvanlar silinecek. Emin misiniz?")
        }
    }
    
    // MARK: - Camera Content
    private var cameraContent: some View {
        VStack(spacing: 0) {
            // Stats Bar
            statsBar
            
            // Camera Preview
            GeometryReader { geometry in
                ZStack {
                    // Camera Preview - Tam ekran
                    CameraPreviewView(cameraManager: cameraManager)
                        .frame(width: geometry.size.width, height: geometry.size.height)
                    
                    // Bounding Boxes
                    if let result = result {
                        ForEach(result.animals) { animal in
                            BoundingBoxView(animal: animal, containerSize: geometry.size)
                        }
                    }
                    
                    // Processing Indicator
                    if isProcessing {
                        VStack {
                            HStack {
                                Spacer()
                                Text("İşleniyor...")
                                    .font(.caption)
                                    .padding(8)
                                    .background(Color.black.opacity(0.7))
                                    .cornerRadius(8)
                                    .padding()
                            }
                            Spacer()
                        }
                    }
                }
            }
            
            // Detection List
            if let result = result, !result.animals.isEmpty {
                detectionList(result.animals)
            }
            
            // Controls
            controlsBar
        }
    }
    
    // MARK: - Stats Bar
    private var statsBar: some View {
        HStack {
            statItem(value: "\(result?.animalCount ?? 0)", label: "Tespit")
            Divider().frame(height: 30)
            statItem(value: "\(totalRegistered)", label: "Kayıtlı")
            Divider().frame(height: 30)
            statItem(value: String(format: "%.1f", fps), label: "FPS")
            Divider().frame(height: 30)
            
            HStack(spacing: 6) {
                Circle()
                    .fill(cameraManager.isRunning ? Color.green : Color.red)
                    .frame(width: 8, height: 8)
                Text(cameraManager.isRunning ? "Aktif" : "Durduruldu")
                    .font(.caption)
            }
        }
        .padding(.horizontal)
        .padding(.vertical, 12)
        .background(Color(UIColor.secondarySystemBackground))
    }
    
    private func statItem(value: String, label: String) -> some View {
        VStack(spacing: 2) {
            Text(value)
                .font(.headline)
                .fontWeight(.bold)
            Text(label)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
    }
    
    // MARK: - Detection List
    private func detectionList(_ animals: [DetectedAnimal]) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("Tespit Edilen Hayvanlar:")
                .font(.caption)
                .foregroundColor(.secondary)
                .padding(.horizontal)
            
            ForEach(animals.prefix(3)) { animal in
                HStack {
                    Text(animal.isNew ? "🆕" : "✓")
                    Text(animal.animalId)
                        .fontWeight(.medium)
                    Text("(\(animal.className))")
                        .foregroundColor(.secondary)
                }
                .font(.caption)
                .padding(.horizontal)
            }
        }
        .padding(.vertical, 8)
        .background(Color(UIColor.secondarySystemBackground))
    }
    
    // MARK: - Controls Bar
    private var controlsBar: some View {
        HStack(spacing: 20) {
            // Flip Camera (placeholder)
            Button(action: {}) {
                Image(systemName: "camera.rotate")
                    .font(.title2)
                    .foregroundColor(.white)
                    .frame(width: 50, height: 50)
                    .background(Color.gray.opacity(0.5))
                    .clipShape(Circle())
            }
            
            // Start/Stop
            Button(action: toggleCapture) {
                HStack {
                    Image(systemName: cameraManager.isRunning ? "stop.fill" : "play.fill")
                    Text(cameraManager.isRunning ? "Durdur" : "Başlat")
                        .fontWeight(.semibold)
                }
                .foregroundColor(.white)
                .padding(.horizontal, 24)
                .padding(.vertical, 14)
                .background(cameraManager.isRunning ? Color.red : Color.green)
                .cornerRadius(12)
            }
            
            // Reset
            Button(action: { showResetAlert = true }) {
                Image(systemName: "trash")
                    .font(.title2)
                    .foregroundColor(.red)
                    .frame(width: 50, height: 50)
                    .background(Color.gray.opacity(0.5))
                    .clipShape(Circle())
            }
        }
        .padding()
        .background(Color(UIColor.secondarySystemBackground))
    }
    
    // MARK: - Permission View
    private var permissionView: some View {
        VStack(spacing: 20) {
            Image(systemName: "camera.fill")
                .font(.system(size: 60))
                .foregroundColor(.gray)
            
            Text("Kamera İzni Gerekli")
                .font(.title2)
                .fontWeight(.bold)
            
            Text("Hayvan tespiti için kamera erişimi gereklidir")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
            
            Button("Ayarlara Git") {
                if let url = URL(string: UIApplication.openSettingsURLString) {
                    UIApplication.shared.open(url)
                }
            }
            .buttonStyle(.borderedProminent)
        }
        .padding()
    }
    
    // MARK: - Actions
    private func toggleCapture() {
        if cameraManager.isRunning {
            cameraManager.stopCapture()
        } else {
            cameraManager.startCapture()
        }
    }
    
    private func setupFrameHandler() {
        cameraManager.onFrameCaptured = { image in
            guard cameraManager.isRunning, !isProcessing else { return }
            
            isProcessing = true
            
            Task {
                if let processResult = await apiService.processFrame(image: image) {
                    DispatchQueue.main.async {
                        self.result = processResult
                        self.fps = processResult.fps
                        self.totalRegistered = processResult.totalRegistered
                        self.isProcessing = false
                    }
                } else {
                    DispatchQueue.main.async {
                        self.isProcessing = false
                    }
                }
            }
        }
    }
}

// MARK: - Bounding Box View
struct BoundingBoxView: View {
    let animal: DetectedAnimal
    let containerSize: CGSize
    
    var body: some View {
        let scaleX = containerSize.width / 640
        let scaleY = containerSize.height / 480
        
        let x = CGFloat(animal.bbox[0]) * scaleX
        let y = CGFloat(animal.bbox[1]) * scaleY
        let width = CGFloat(animal.bbox[2] - animal.bbox[0]) * scaleX
        let height = CGFloat(animal.bbox[3] - animal.bbox[1]) * scaleY
        
        ZStack(alignment: .topLeading) {
            // Box
            Rectangle()
                .stroke(boxColor, lineWidth: 2)
                .frame(width: width, height: height)
                .position(x: x + width/2, y: y + height/2)
            
            // Label
            HStack(spacing: 4) {
                Text(animal.animalId.hasPrefix("TEMP_") ? "..." : animal.animalId)
                    .font(.caption2)
                    .fontWeight(.bold)
                
                if animal.isNew {
                    Text("YENİ")
                        .font(.system(size: 8))
                        .fontWeight(.bold)
                        .padding(.horizontal, 4)
                        .padding(.vertical, 2)
                        .background(Color.green.opacity(0.8))
                        .cornerRadius(4)
                }
            }
            .foregroundColor(.white)
            .padding(.horizontal, 6)
            .padding(.vertical, 3)
            .background(boxColor)
            .cornerRadius(4)
            .position(x: x + 40, y: max(y - 12, 12))
        }
    }
    
    private var boxColor: Color {
        if animal.isNew {
            return .green
        } else if animal.animalId.hasPrefix("TEMP_") {
            return .orange
        } else {
            return .blue
        }
    }
}

#Preview {
    NavigationView {
        CameraView()
    }
    .preferredColorScheme(.dark)
}
