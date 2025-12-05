import SwiftUI

struct ContentView: View {
    @State private var selectedTab = 0
    
    var body: some View {
        TabView(selection: $selectedTab) {
            HomeView()
                .tabItem {
                    Image(systemName: "house.fill")
                    Text("Ana Sayfa")
                }
                .tag(0)
            
            CameraView()
                .tabItem {
                    Image(systemName: "camera.fill")
                    Text("Kamera")
                }
                .tag(1)
            
            GalleryView()
                .tabItem {
                    Image(systemName: "photo.stack.fill")
                    Text("Hayvanlar")
                }
                .tag(2)
            
            AlertsView()
                .tabItem {
                    Image(systemName: "bell.fill")
                    Text("Uyarılar")
                }
                .tag(3)
        }
        .accentColor(.green)
    }
}

#Preview {
    ContentView()
        .preferredColorScheme(.dark)
}
