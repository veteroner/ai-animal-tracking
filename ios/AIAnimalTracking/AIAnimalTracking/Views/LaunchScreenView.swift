//
//  LaunchScreenView.swift
//  AIAnimalTracking
//
//  Teknova - AI Animal Tracking System
//  Copyright © 2024 Teknova. All rights reserved.
//

import SwiftUI

struct LaunchScreenView: View {
    @State private var isAnimating = false
    @State private var showLogo = false
    @State private var showText = false
    @State private var showTagline = false
    
    var body: some View {
        ZStack {
            // Background Gradient
            LinearGradient(
                gradient: Gradient(colors: [
                    Color(red: 0.04, green: 0.12, blue: 0.18),
                    Color(red: 0.07, green: 0.20, blue: 0.25),
                    Color(red: 0.04, green: 0.12, blue: 0.18)
                ]),
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()
            
            // Animated Background Circles
            GeometryReader { geometry in
                ZStack {
                    Circle()
                        .fill(TeknovaColors.primary.opacity(0.1))
                        .frame(width: 300, height: 300)
                        .offset(x: -100, y: -200)
                        .scaleEffect(isAnimating ? 1.2 : 0.8)
                    
                    Circle()
                        .fill(TeknovaColors.secondary.opacity(0.1))
                        .frame(width: 400, height: 400)
                        .offset(x: 150, y: 300)
                        .scaleEffect(isAnimating ? 1.1 : 0.9)
                    
                    Circle()
                        .fill(TeknovaColors.accent.opacity(0.08))
                        .frame(width: 250, height: 250)
                        .offset(x: 100, y: -100)
                        .scaleEffect(isAnimating ? 1.3 : 0.7)
                }
            }
            
            // Main Content
            VStack(spacing: 40) {
                Spacer()
                
                // Logo Animation
                ZStack {
                    // Outer Ring
                    Circle()
                        .stroke(
                            LinearGradient(
                                gradient: Gradient(colors: [TeknovaColors.primary, TeknovaColors.secondary]),
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            ),
                            lineWidth: 3
                        )
                        .frame(width: 140, height: 140)
                        .scaleEffect(showLogo ? 1 : 0.5)
                        .opacity(showLogo ? 1 : 0)
                    
                    // Inner Circle with Gradient
                    Circle()
                        .fill(
                            LinearGradient(
                                gradient: Gradient(colors: [
                                    TeknovaColors.primary,
                                    TeknovaColors.secondary.opacity(0.8)
                                ]),
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 110, height: 110)
                        .shadow(color: TeknovaColors.primary.opacity(0.5), radius: 20, x: 0, y: 10)
                        .scaleEffect(showLogo ? 1 : 0)
                    
                    // AI Eye Symbol
                    VStack(spacing: 4) {
                        // Eye
                        ZStack {
                            Ellipse()
                                .stroke(Color.white, lineWidth: 2.5)
                                .frame(width: 55, height: 30)
                            
                            Circle()
                                .fill(Color.white)
                                .frame(width: 16, height: 16)
                            
                            // Scan Line
                            Rectangle()
                                .fill(TeknovaColors.accent)
                                .frame(width: 50, height: 2)
                                .offset(y: isAnimating ? 10 : -10)
                        }
                        
                        // Paw
                        Image(systemName: "pawprint.fill")
                            .font(.system(size: 24))
                            .foregroundColor(TeknovaColors.accent)
                    }
                    .opacity(showLogo ? 1 : 0)
                    .scaleEffect(showLogo ? 1 : 0.5)
                }
                
                // Company Name
                VStack(spacing: 8) {
                    Text("TEKNOVA")
                        .font(.system(size: 42, weight: .bold, design: .rounded))
                        .foregroundColor(.white)
                        .tracking(8)
                        .opacity(showText ? 1 : 0)
                        .offset(y: showText ? 0 : 20)
                    
                    Text("AI Animal Tracking System")
                        .font(.system(size: 16, weight: .medium, design: .rounded))
                        .foregroundColor(.white.opacity(0.7))
                        .tracking(2)
                        .opacity(showTagline ? 1 : 0)
                        .offset(y: showTagline ? 0 : 10)
                }
                
                Spacer()
                
                // Loading Indicator
                VStack(spacing: 16) {
                    // Progress Bar
                    ZStack(alignment: .leading) {
                        RoundedRectangle(cornerRadius: 4)
                            .fill(Color.white.opacity(0.2))
                            .frame(width: 200, height: 4)
                        
                        RoundedRectangle(cornerRadius: 4)
                            .fill(
                                LinearGradient(
                                    gradient: Gradient(colors: [TeknovaColors.primary, TeknovaColors.secondary]),
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                            .frame(width: isAnimating ? 200 : 0, height: 4)
                    }
                    .opacity(showTagline ? 1 : 0)
                    
                    Text("Sistem Başlatılıyor...")
                        .font(.system(size: 12, weight: .medium, design: .rounded))
                        .foregroundColor(.white.opacity(0.5))
                        .opacity(showTagline ? 1 : 0)
                }
                .padding(.bottom, 60)
            }
        }
        .onAppear {
            withAnimation(.easeOut(duration: 0.8)) {
                showLogo = true
            }
            
            withAnimation(.easeOut(duration: 0.6).delay(0.3)) {
                showText = true
            }
            
            withAnimation(.easeOut(duration: 0.5).delay(0.6)) {
                showTagline = true
            }
            
            withAnimation(.easeInOut(duration: 2).repeatForever(autoreverses: true)) {
                isAnimating = true
            }
        }
    }
}

#Preview {
    LaunchScreenView()
}
