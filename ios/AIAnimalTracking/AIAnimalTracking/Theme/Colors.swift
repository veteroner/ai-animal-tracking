//
//  Colors.swift
//  AIAnimalTracking
//
//  Teknova - AI Animal Tracking System
//  Copyright © 2024 Teknova. All rights reserved.
//

import SwiftUI

// MARK: - Teknova Brand Colors
// Note: These use Asset Catalog colors (TeknovaPrimary, etc.)
// Access via Color.Teknova.primary, Color.Teknova.secondary, etc.

struct TeknovaColors {
    // Primary Brand Colors (from Asset Catalog)
    static let primary = Color("TeknovaPrimary")
    static let secondary = Color("TeknovaSecondary")
    static let accent = Color("TeknovaAccent")
    static let background = Color("TeknovaBackground")
    
    // Semantic Colors
    static let success = Color(red: 0.18, green: 0.80, blue: 0.44)  // #2ECC71
    static let warning = Color(red: 0.95, green: 0.77, blue: 0.06)  // #F1C40F
    static let danger = Color(red: 0.91, green: 0.30, blue: 0.24)   // #E74C3C
    static let info = Color(red: 0.20, green: 0.60, blue: 0.86)     // #3498DB
    
    // Gradient Colors
    static let gradientStart = Color(red: 0.07, green: 0.48, blue: 0.31)  // #127A50
    static let gradientEnd = Color(red: 0.23, green: 0.43, blue: 0.95)    // #3B6DF2
}

// Convenience accessor
extension Color {
    static let Teknova = TeknovaColors.self
}

// MARK: - Teknova Gradients
struct TeknovaGradients {
    static let primary = LinearGradient(
        gradient: Gradient(colors: [TeknovaColors.gradientStart, TeknovaColors.gradientEnd]),
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )
    
    static let card = LinearGradient(
        gradient: Gradient(colors: [
            TeknovaColors.gradientStart.opacity(0.1),
            TeknovaColors.gradientEnd.opacity(0.1)
        ]),
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )
}

// MARK: - Typography
struct TeknovaFont {
    static func headline(_ size: CGFloat = 24) -> Font {
        .system(size: size, weight: .bold, design: .rounded)
    }
    
    static func title(_ size: CGFloat = 20) -> Font {
        .system(size: size, weight: .semibold, design: .rounded)
    }
    
    static func body(_ size: CGFloat = 16) -> Font {
        .system(size: size, weight: .regular, design: .rounded)
    }
    
    static func caption(_ size: CGFloat = 12) -> Font {
        .system(size: size, weight: .medium, design: .rounded)
    }
}
