import Foundation

// MARK: - API Configuration
struct APIConfig {
    // ==============================================
    // BACKEND AYARLARI
    // ==============================================
    // Geliştirme için: Lokal IP adresinizi kullanın
    // Prodüksiyon için: Hugging Face URL'ini kullanın
    
    // 🔧 GELİŞTİRME (Lokal)
    // static let baseURL = "http://172.20.10.3:8000"
    
    // 🚀 PRODÜKSİYON (Hugging Face)
    // static let baseURL = "https://teknova-animal-tracking.hf.space"
    
    // ☁️ COLAB (ngrok)
    static let baseURL = "https://unsentimentalized-gaston-hypolithic.ngrok-free.dev"
    
    // ==============================================
    
    static let apiPrefix = "/api/v1/detection"
    
    static var processFrameURL: URL {
        URL(string: "\(baseURL)\(apiPrefix)/process-frame")!
    }
    
    static var galleryURL: URL {
        URL(string: "\(baseURL)\(apiPrefix)/gallery")!
    }
    
    static var resetURL: URL {
        URL(string: "\(baseURL)\(apiPrefix)/reset")!
    }
    
    static var healthURL: URL {
        URL(string: "\(baseURL)/health")!
    }
}

// MARK: - Detected Animal
struct DetectedAnimal: Codable, Identifiable {
    let trackId: Int
    let animalId: String
    let className: String
    let bbox: [Int]
    let confidence: Double
    let reIdConfidence: Double?
    let isIdentified: Bool
    let isNew: Bool
    let velocity: [Double]
    let direction: Double
    let healthScore: Double?
    let behavior: String?
    
    var id: String { "\(trackId)-\(animalId)" }
    
    enum CodingKeys: String, CodingKey {
        case trackId = "track_id"
        case animalId = "animal_id"
        case className = "class_name"
        case bbox, confidence
        case reIdConfidence = "re_id_confidence"
        case isIdentified = "is_identified"
        case isNew = "is_new"
        case velocity, direction
        case healthScore = "health_score"
        case behavior
    }
    
    var classEmoji: String {
        let emojis: [String: String] = [
            "cow": "🐄", "cattle": "🐄",
            "sheep": "🐑", "goat": "🐐",
            "horse": "🐴", "dog": "🐕",
            "cat": "🐱", "bird": "🐦",
            "chicken": "🐔", "elephant": "🐘",
            "bear": "🐻", "zebra": "🦓",
            "giraffe": "🦒"
        ]
        return emojis[className.lowercased()] ?? "🐾"
    }
}

// MARK: - Process Result
struct ProcessResult: Codable {
    let frameId: Int
    let timestamp: Double
    let fps: Double
    let animalCount: Int
    let totalRegistered: Int
    let newThisFrame: Int
    let animals: [DetectedAnimal]
    let frameSize: [Int]?
    
    enum CodingKeys: String, CodingKey {
        case frameId = "frame_id"
        case timestamp, fps
        case animalCount = "animal_count"
        case totalRegistered = "total_registered"
        case newThisFrame = "new_this_frame"
        case animals
        case frameSize = "frame_size"
    }
}

// MARK: - Gallery Animal
struct GalleryAnimal: Codable, Identifiable {
    let animalId: String
    let className: String
    let firstSeen: Double
    let lastSeen: Double
    let totalDetections: Int
    let bestConfidence: Double
    let metadata: [String: String]?
    
    var id: String { animalId }
    
    enum CodingKeys: String, CodingKey {
        case animalId = "animal_id"
        case className = "class_name"
        case firstSeen = "first_seen"
        case lastSeen = "last_seen"
        case totalDetections = "total_detections"
        case bestConfidence = "best_confidence"
        case metadata
    }
    
    var classEmoji: String {
        let emojis: [String: String] = [
            "cow": "🐄", "cattle": "🐄",
            "sheep": "🐑", "goat": "🐐",
            "horse": "🐴", "dog": "🐕",
            "cat": "🐱", "bird": "🐦",
            "chicken": "🐔", "elephant": "🐘",
            "bear": "🐻", "zebra": "🦓",
            "giraffe": "🦒"
        ]
        return emojis[className.lowercased()] ?? "🐾"
    }
    
    var firstSeenDate: Date {
        Date(timeIntervalSince1970: firstSeen)
    }
    
    var lastSeenDate: Date {
        Date(timeIntervalSince1970: lastSeen)
    }
}

// MARK: - Gallery Stats
struct GalleryStats: Codable {
    let totalAnimals: Int
    let byClass: [String: Int]
    let idCounters: [String: Int]
    
    enum CodingKeys: String, CodingKey {
        case totalAnimals = "total_animals"
        case byClass = "by_class"
        case idCounters = "id_counters"
    }
}

// MARK: - Gallery Response
struct GalleryResponse: Codable {
    let animals: [GalleryAnimal]
    let stats: GalleryStats
}

// MARK: - Alert Model
struct AlertItem: Identifiable {
    let id = UUID()
    let type: AlertType
    let severity: AlertSeverity
    let title: String
    let message: String
    let createdAt: Date
    var isRead: Bool
    
    enum AlertType: String {
        case health = "sağlık"
        case security = "güvenlik"
        case system = "sistem"
        case activity = "aktivite"
        
        var icon: String {
            switch self {
            case .health: return "cross.case.fill"
            case .security: return "lock.shield.fill"
            case .system: return "gear"
            case .activity: return "chart.bar.fill"
            }
        }
    }
    
    enum AlertSeverity: String {
        case low = "düşük"
        case medium = "orta"
        case high = "yüksek"
        case critical = "kritik"
        
        var color: Color {
            switch self {
            case .low: return .green
            case .medium: return .yellow
            case .high: return .orange
            case .critical: return .red
            }
        }
    }
}

import SwiftUI
