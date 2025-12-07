import SwiftUI

struct SettingsView: View {
    @State private var notificationsEnabled = true
    @State private var darkModeEnabled = true
    @State private var autoSyncEnabled = true
    @State private var soundEnabled = true
    @State private var selectedLanguage = "Türkçe"
    @State private var serverUrl = "http://localhost:8000"
    @State private var showingLogout = false
    
    var body: some View {
        NavigationView {
            ZStack {
                Color.black.ignoresSafeArea()
                
                ScrollView {
                    VStack(spacing: 20) {
                        // Profile Section
                        VStack(spacing: 16) {
                            ZStack {
                                Circle()
                                    .fill(Color.green.opacity(0.2))
                                    .frame(width: 80, height: 80)
                                Image(systemName: "person.fill")
                                    .font(.system(size: 40))
                                    .foregroundColor(.green)
                            }
                            
                            Text("Çiftlik Yöneticisi")
                                .font(.title2)
                                .fontWeight(.bold)
                                .foregroundColor(.white)
                            
                            Text("admin@teknova.com")
                                .font(.subheadline)
                                .foregroundColor(.gray)
                        }
                        .padding(.vertical)
                        
                        // Notifications Section
                        SettingsSection(title: "Bildirimler") {
                            SettingsToggle(icon: "bell.fill", title: "Bildirimler", isOn: $notificationsEnabled, color: .blue)
                            SettingsToggle(icon: "speaker.wave.2.fill", title: "Ses", isOn: $soundEnabled, color: .purple)
                        }
                        
                        // Appearance Section
                        SettingsSection(title: "Görünüm") {
                            SettingsToggle(icon: "moon.fill", title: "Karanlık Mod", isOn: $darkModeEnabled, color: .indigo)
                            SettingsRow(icon: "globe", title: "Dil", value: selectedLanguage, color: .green)
                        }
                        
                        // Sync Section
                        SettingsSection(title: "Senkronizasyon") {
                            SettingsToggle(icon: "arrow.triangle.2.circlepath", title: "Otomatik Senkronizasyon", isOn: $autoSyncEnabled, color: .orange)
                            SettingsRow(icon: "server.rack", title: "Sunucu", value: "Bağlı", color: .green)
                        }
                        
                        // Server Section
                        SettingsSection(title: "Sunucu Ayarları") {
                            VStack(alignment: .leading, spacing: 8) {
                                HStack {
                                    Image(systemName: "link")
                                        .foregroundColor(.blue)
                                        .frame(width: 30)
                                    Text("API URL")
                                        .foregroundColor(.white)
                                }
                                TextField("Sunucu adresi", text: $serverUrl)
                                    .textFieldStyle(RoundedBorderTextFieldStyle())
                                    .font(.subheadline)
                            }
                            .padding()
                            .background(Color.gray.opacity(0.15))
                            .cornerRadius(12)
                        }
                        
                        // About Section
                        SettingsSection(title: "Hakkında") {
                            SettingsRow(icon: "info.circle.fill", title: "Versiyon", value: "1.0.0", color: .gray)
                            SettingsRow(icon: "doc.text.fill", title: "Lisans", value: "MIT", color: .gray)
                            
                            Button(action: {}) {
                                HStack {
                                    Image(systemName: "questionmark.circle.fill")
                                        .foregroundColor(.blue)
                                        .frame(width: 30)
                                    Text("Yardım & Destek")
                                        .foregroundColor(.white)
                                    Spacer()
                                    Image(systemName: "chevron.right")
                                        .foregroundColor(.gray)
                                }
                                .padding()
                                .background(Color.gray.opacity(0.15))
                                .cornerRadius(12)
                            }
                        }
                        
                        // Logout Button
                        Button(action: { showingLogout = true }) {
                            HStack {
                                Image(systemName: "rectangle.portrait.and.arrow.right")
                                Text("Çıkış Yap")
                            }
                            .font(.headline)
                            .foregroundColor(.red)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.red.opacity(0.15))
                            .cornerRadius(12)
                        }
                        .padding(.top)
                    }
                    .padding()
                }
            }
            .navigationTitle("⚙️ Ayarlar")
            .navigationBarTitleDisplayMode(.large)
            .alert("Çıkış Yap", isPresented: $showingLogout) {
                Button("İptal", role: .cancel) {}
                Button("Çıkış", role: .destructive) {}
            } message: {
                Text("Çıkış yapmak istediğinize emin misiniz?")
            }
        }
    }
}

struct SettingsSection<Content: View>: View {
    let title: String
    @ViewBuilder let content: Content
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.headline)
                .foregroundColor(.gray)
                .padding(.leading, 4)
            
            VStack(spacing: 8) {
                content
            }
        }
    }
}

struct SettingsToggle: View {
    let icon: String
    let title: String
    @Binding var isOn: Bool
    let color: Color
    
    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundColor(color)
                .frame(width: 30)
            Text(title)
                .foregroundColor(.white)
            Spacer()
            Toggle("", isOn: $isOn)
                .tint(.green)
        }
        .padding()
        .background(Color.gray.opacity(0.15))
        .cornerRadius(12)
    }
}

struct SettingsRow: View {
    let icon: String
    let title: String
    let value: String
    let color: Color
    
    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundColor(color)
                .frame(width: 30)
            Text(title)
                .foregroundColor(.white)
            Spacer()
            Text(value)
                .foregroundColor(.gray)
        }
        .padding()
        .background(Color.gray.opacity(0.15))
        .cornerRadius(12)
    }
}

#Preview {
    SettingsView()
        .preferredColorScheme(.dark)
}
