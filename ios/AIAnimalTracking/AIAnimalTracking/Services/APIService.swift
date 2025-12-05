import Foundation
import UIKit

class APIService: ObservableObject {
    static let shared = APIService()
    
    @Published var isConnected = false
    @Published var lastError: String?
    
    private init() {}
    
    // MARK: - Health Check
    func checkHealth() async -> Bool {
        do {
            let (_, response) = try await URLSession.shared.data(from: APIConfig.healthURL)
            if let httpResponse = response as? HTTPURLResponse {
                DispatchQueue.main.async {
                    self.isConnected = httpResponse.statusCode == 200
                }
                return httpResponse.statusCode == 200
            }
        } catch {
            DispatchQueue.main.async {
                self.isConnected = false
                self.lastError = error.localizedDescription
            }
        }
        return false
    }
    
    // MARK: - Process Frame
    func processFrame(image: UIImage) async -> ProcessResult? {
        guard let imageData = image.jpegData(compressionQuality: 0.5) else {
            print("❌ Image compression failed")
            return nil
        }
        
        print("📸 Sending frame to: \(APIConfig.processFrameURL)")
        print("📦 Image size: \(imageData.count) bytes")
        
        let boundary = UUID().uuidString
        var request = URLRequest(url: APIConfig.processFrameURL)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 10
        
        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"frame.jpg\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(imageData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        
        request.httpBody = body
        
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            
            if let httpResponse = response as? HTTPURLResponse {
                print("📡 Response status: \(httpResponse.statusCode)")
                
                if httpResponse.statusCode == 200 {
                    if let jsonString = String(data: data, encoding: .utf8) {
                        print("✅ Response: \(jsonString.prefix(500))")
                    }
                    let decoder = JSONDecoder()
                    let result = try decoder.decode(ProcessResult.self, from: data)
                    print("🐄 Animals detected: \(result.animalCount)")
                    return result
                } else {
                    if let errorString = String(data: data, encoding: .utf8) {
                        print("❌ Error response: \(errorString)")
                    }
                }
            }
        } catch {
            print("❌ Process frame error: \(error)")
            DispatchQueue.main.async {
                self.lastError = error.localizedDescription
            }
        }
        
        return nil
    }
    
    // MARK: - Get Gallery
    func getGallery() async -> GalleryResponse? {
        do {
            let (data, response) = try await URLSession.shared.data(from: APIConfig.galleryURL)
            
            if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 {
                let decoder = JSONDecoder()
                return try decoder.decode(GalleryResponse.self, from: data)
            }
        } catch {
            print("Gallery fetch error: \(error)")
            DispatchQueue.main.async {
                self.lastError = error.localizedDescription
            }
        }
        
        return nil
    }
    
    // MARK: - Reset Gallery
    func resetGallery() async -> Bool {
        var request = URLRequest(url: APIConfig.resetURL)
        request.httpMethod = "POST"
        
        do {
            let (_, response) = try await URLSession.shared.data(for: request)
            if let httpResponse = response as? HTTPURLResponse {
                return httpResponse.statusCode == 200
            }
        } catch {
            print("Reset error: \(error)")
            DispatchQueue.main.async {
                self.lastError = error.localizedDescription
            }
        }
        
        return false
    }
}
