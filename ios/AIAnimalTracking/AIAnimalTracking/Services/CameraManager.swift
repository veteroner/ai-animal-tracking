import AVFoundation
import UIKit
import SwiftUI

class CameraManager: NSObject, ObservableObject {
    @Published var capturedImage: UIImage?
    @Published var isRunning = false
    @Published var error: String?
    @Published var isSessionReady = false
    
    var captureSession: AVCaptureSession?
    private var videoOutput: AVCaptureVideoDataOutput?
    
    private let sessionQueue = DispatchQueue(label: "camera.session.queue")
    private var lastCaptureTime = Date()
    private let captureInterval: TimeInterval = 1.0 // 1 saniyede bir
    
    var onFrameCaptured: ((UIImage) -> Void)?
    
    override init() {
        super.init()
    }
    
    func checkPermission() async -> Bool {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            return true
        case .notDetermined:
            return await AVCaptureDevice.requestAccess(for: .video)
        default:
            return false
        }
    }
    
    func setupSession() {
        sessionQueue.async { [weak self] in
            self?.configureSession()
        }
    }
    
    private func configureSession() {
        let session = AVCaptureSession()
        session.beginConfiguration()
        session.sessionPreset = .medium
        
        // Input
        guard let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back),
              let input = try? AVCaptureDeviceInput(device: device) else {
            DispatchQueue.main.async {
                self.error = "Kamera başlatılamadı"
            }
            return
        }
        
        if session.canAddInput(input) {
            session.addInput(input)
        }
        
        // Output
        let output = AVCaptureVideoDataOutput()
        output.setSampleBufferDelegate(self, queue: DispatchQueue(label: "video.output.queue"))
        output.alwaysDiscardsLateVideoFrames = true
        output.videoSettings = [
            kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA
        ]
        
        if session.canAddOutput(output) {
            session.addOutput(output)
        }
        
        session.commitConfiguration()
        
        self.captureSession = session
        self.videoOutput = output
        
        DispatchQueue.main.async {
            self.isSessionReady = true
        }
    }
    
    func startCapture() {
        sessionQueue.async { [weak self] in
            guard let self = self, let session = self.captureSession else { return }
            if !session.isRunning {
                session.startRunning()
            }
            DispatchQueue.main.async {
                self.isRunning = true
            }
        }
    }
    
    func stopCapture() {
        sessionQueue.async { [weak self] in
            guard let self = self, let session = self.captureSession else { return }
            if session.isRunning {
                session.stopRunning()
            }
            DispatchQueue.main.async {
                self.isRunning = false
            }
        }
    }
}

// MARK: - AVCaptureVideoDataOutputSampleBufferDelegate
extension CameraManager: AVCaptureVideoDataOutputSampleBufferDelegate {
    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        
        // Frame rate limiti
        let now = Date()
        guard now.timeIntervalSince(lastCaptureTime) >= captureInterval else { return }
        lastCaptureTime = now
        
        guard let imageBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        
        let ciImage = CIImage(cvPixelBuffer: imageBuffer)
        let context = CIContext()
        
        guard let cgImage = context.createCGImage(ciImage, from: ciImage.extent) else { return }
        
        let image = UIImage(cgImage: cgImage, scale: 1.0, orientation: .right)
        
        DispatchQueue.main.async { [weak self] in
            self?.capturedImage = image
            self?.onFrameCaptured?(image)
        }
    }
}

// MARK: - Camera Preview UIViewRepresentable
struct CameraPreviewView: UIViewRepresentable {
    @ObservedObject var cameraManager: CameraManager
    
    func makeUIView(context: Context) -> CameraPreviewUIView {
        let view = CameraPreviewUIView()
        return view
    }
    
    func updateUIView(_ uiView: CameraPreviewUIView, context: Context) {
        if let session = cameraManager.captureSession, uiView.previewLayer.session != session {
            uiView.previewLayer.session = session
        }
    }
}

class CameraPreviewUIView: UIView {
    override class var layerClass: AnyClass {
        AVCaptureVideoPreviewLayer.self
    }
    
    var previewLayer: AVCaptureVideoPreviewLayer {
        layer as! AVCaptureVideoPreviewLayer
    }
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupPreviewLayer()
    }
    
    required init?(coder: NSCoder) {
        super.init(coder: coder)
        setupPreviewLayer()
    }
    
    private func setupPreviewLayer() {
        previewLayer.videoGravity = .resizeAspectFill
        backgroundColor = .black
    }
    
    override func layoutSubviews() {
        super.layoutSubviews()
        previewLayer.frame = bounds
    }
}
