//
//  Components.swift
//  AIAnimalTracking
//
//  Teknova - AI Animal Tracking System
//  Copyright © 2024 Teknova. All rights reserved.
//

import SwiftUI

// MARK: - Teknova Logo View
struct TeknovaLogo: View {
    var size: CGFloat = 80
    var showText: Bool = true
    
    var body: some View {
        VStack(spacing: 12) {
            // Logo Icon
            ZStack {
                // Background Circle with Gradient
                Circle()
                    .fill(TeknovaGradients.primary)
                    .frame(width: size, height: size)
                    .shadow(color: TeknovaColors.primary.opacity(0.4), radius: 15, x: 0, y: 8)
                
                // Inner Circle
                Circle()
                    .fill(Color.white.opacity(0.2))
                    .frame(width: size * 0.75, height: size * 0.75)
                
                // AI Eye Symbol
                ZStack {
                    // Outer Eye
                    Ellipse()
                        .stroke(Color.white, lineWidth: 3)
                        .frame(width: size * 0.55, height: size * 0.35)
                    
                    // Pupil with scanning effect
                    Circle()
                        .fill(Color.white)
                        .frame(width: size * 0.18, height: size * 0.18)
                    
                    // Scanning line
                    Rectangle()
                        .fill(TeknovaColors.accent)
                        .frame(width: size * 0.5, height: 2)
                        .offset(y: -2)
                }
                
                // Paw Print Accent
                Image(systemName: "pawprint.fill")
                    .font(.system(size: size * 0.2))
                    .foregroundColor(TeknovaColors.accent)
                    .offset(x: size * 0.28, y: size * 0.28)
            }
            
            if showText {
                VStack(spacing: 2) {
                    Text("TEKNOVA")
                        .font(.system(size: size * 0.25, weight: .bold, design: .rounded))
                        .foregroundStyle(TeknovaGradients.primary)
                        .tracking(3)
                    
                    Text("AI Animal Tracking")
                        .font(.system(size: size * 0.12, weight: .medium, design: .rounded))
                        .foregroundColor(.secondary)
                }
            }
        }
    }
}

// MARK: - Primary Button
struct TeknovaPrimaryButton: View {
    let title: String
    let icon: String?
    let action: () -> Void
    
    init(_ title: String, icon: String? = nil, action: @escaping () -> Void) {
        self.title = title
        self.icon = icon
        self.action = action
    }
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                if let icon = icon {
                    Image(systemName: icon)
                        .font(.system(size: 18, weight: .semibold))
                }
                Text(title)
                    .font(TeknovaFont.body(16))
                    .fontWeight(.semibold)
            }
            .foregroundColor(.white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 16)
            .background(TeknovaGradients.primary)
            .cornerRadius(12)
            .shadow(color: TeknovaColors.primary.opacity(0.3), radius: 8, x: 0, y: 4)
        }
    }
}

// MARK: - Card View
struct TeknovaCard<Content: View>: View {
    let content: Content
    
    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }
    
    var body: some View {
        content
            .padding(16)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(Color(.systemBackground))
                    .shadow(color: .black.opacity(0.08), radius: 12, x: 0, y: 4)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .stroke(TeknovaGradients.primary, lineWidth: 1)
                    .opacity(0.3)
            )
    }
}

// MARK: - Status Badge
struct TeknovaStatusBadge: View {
    enum Status {
        case success, warning, danger, info
        
        var color: Color {
            switch self {
            case .success: return TeknovaColors.success
            case .warning: return TeknovaColors.warning
            case .danger: return TeknovaColors.danger
            case .info: return TeknovaColors.info
            }
        }
        
        var icon: String {
            switch self {
            case .success: return "checkmark.circle.fill"
            case .warning: return "exclamationmark.triangle.fill"
            case .danger: return "xmark.circle.fill"
            case .info: return "info.circle.fill"
            }
        }
    }
    
    let text: String
    let status: Status
    
    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: status.icon)
                .font(.system(size: 12))
            Text(text)
                .font(TeknovaFont.caption(11))
                .fontWeight(.medium)
        }
        .foregroundColor(status.color)
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(status.color.opacity(0.15))
        .cornerRadius(20)
    }
}

// MARK: - Loading View
struct TeknovaLoadingView: View {
    @State private var isAnimating = false
    
    var body: some View {
        VStack(spacing: 20) {
            ZStack {
                Circle()
                    .stroke(TeknovaColors.primary.opacity(0.2), lineWidth: 4)
                    .frame(width: 50, height: 50)
                
                Circle()
                    .trim(from: 0, to: 0.7)
                    .stroke(
                        TeknovaGradients.primary,
                        style: StrokeStyle(lineWidth: 4, lineCap: .round)
                    )
                    .frame(width: 50, height: 50)
                    .rotationEffect(Angle(degrees: isAnimating ? 360 : 0))
                    .animation(.linear(duration: 1).repeatForever(autoreverses: false), value: isAnimating)
            }
            
            Text("Yükleniyor...")
                .font(TeknovaFont.body(14))
                .foregroundColor(.secondary)
        }
        .onAppear {
            isAnimating = true
        }
    }
}

// MARK: - Preview
#Preview {
    VStack(spacing: 30) {
        TeknovaLogo()
        
        TeknovaPrimaryButton("Başlat", icon: "play.fill") {
            print("Tapped")
        }
        .padding(.horizontal, 40)
        
        HStack(spacing: 10) {
            TeknovaStatusBadge(text: "Aktif", status: .success)
            TeknovaStatusBadge(text: "Uyarı", status: .warning)
            TeknovaStatusBadge(text: "Hata", status: .danger)
            TeknovaStatusBadge(text: "Bilgi", status: .info)
        }
        
        TeknovaCard {
            HStack {
                Image(systemName: "pawprint.fill")
                    .foregroundColor(.teknovaPrimary)
                Text("Örnek Kart")
                Spacer()
            }
        }
        .padding(.horizontal, 20)
        
        TeknovaLoadingView()
    }
    .padding()
}
