import SwiftUI

struct GalleryView: View {
    @StateObject private var apiService = APIService.shared
    @State private var animals: [GalleryAnimal] = []
    @State private var stats: GalleryStats?
    @State private var isLoading = true
    @State private var showResetAlert = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Stats Header
                if let stats = stats {
                    statsHeader(stats)
                }
                
                // Reset Button
                Button(action: { showResetAlert = true }) {
                    HStack {
                        Image(systemName: "trash")
                        Text("Galeriyi Sıfırla")
                    }
                    .foregroundColor(.red)
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(Color(UIColor.secondarySystemBackground))
                    .cornerRadius(8)
                }
                .padding()
                
                // Animal List
                if animals.isEmpty {
                    emptyView
                } else {
                    animalList
                }
            }
            .navigationTitle("Kayıtlı Hayvanlar")
            .onAppear {
                Task { await loadData() }
            }
            .refreshable {
                await loadData()
            }
            .alert("Galeriyi Sıfırla", isPresented: $showResetAlert) {
                Button("İptal", role: .cancel) { }
                Button("Sıfırla", role: .destructive) {
                    Task {
                        if await apiService.resetGallery() {
                            animals = []
                            stats = nil
                        }
                    }
                }
            } message: {
                Text("Tüm kayıtlı hayvanlar silinecek. Emin misiniz?")
            }
        }
    }
    
    // MARK: - Stats Header
    private func statsHeader(_ stats: GalleryStats) -> some View {
        HStack {
            statBox(value: "\(stats.totalAnimals)", label: "Toplam", color: .green)
            
            ForEach(Array(stats.byClass.prefix(3)), id: \.key) { className, count in
                statBox(value: "\(count)", label: className.capitalized, color: .blue)
            }
        }
        .padding()
        .background(Color(UIColor.secondarySystemBackground))
    }
    
    private func statBox(value: String, label: String, color: Color) -> some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.title2)
                .fontWeight(.bold)
                .foregroundColor(color)
            Text(label)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
    }
    
    // MARK: - Animal List
    private var animalList: some View {
        List(animals) { animal in
            AnimalRowView(animal: animal)
        }
        .listStyle(.plain)
    }
    
    // MARK: - Empty View
    private var emptyView: some View {
        VStack(spacing: 16) {
            Spacer()
            Text("📭")
                .font(.system(size: 60))
            Text(isLoading ? "Yükleniyor..." : "Henüz kayıtlı hayvan yok")
                .font(.headline)
            Text("Kamera sekmesinden hayvan tespiti yapın")
                .font(.subheadline)
                .foregroundColor(.secondary)
            Spacer()
        }
    }
    
    // MARK: - Load Data
    private func loadData() async {
        if let response = await apiService.getGallery() {
            DispatchQueue.main.async {
                self.animals = response.animals
                self.stats = response.stats
                self.isLoading = false
            }
        } else {
            DispatchQueue.main.async {
                self.isLoading = false
            }
        }
    }
}

// MARK: - Animal Row View
struct AnimalRowView: View {
    let animal: GalleryAnimal
    
    private let dateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "dd.MM.yyyy HH:mm"
        formatter.locale = Locale(identifier: "tr_TR")
        return formatter
    }()
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header
            HStack {
                Text(animal.classEmoji)
                    .font(.system(size: 40))
                
                VStack(alignment: .leading, spacing: 4) {
                    Text(animal.animalId)
                        .font(.headline)
                        .fontWeight(.bold)
                    Text(animal.className.capitalized)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                // Confidence Badge
                Text("\(Int(animal.bestConfidence * 100))%")
                    .font(.caption)
                    .fontWeight(.bold)
                    .foregroundColor(.white)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(Color.green)
                    .cornerRadius(12)
            }
            
            // Details
            VStack(spacing: 8) {
                detailRow(label: "İlk Görülme:", value: dateFormatter.string(from: animal.firstSeenDate))
                detailRow(label: "Son Görülme:", value: dateFormatter.string(from: animal.lastSeenDate))
                detailRow(label: "Toplam Tespit:", value: "\(animal.totalDetections) kez")
            }
            .padding()
            .background(Color(UIColor.tertiarySystemBackground))
            .cornerRadius(8)
        }
        .padding()
        .background(Color(UIColor.secondarySystemBackground))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.green, lineWidth: 2)
                .opacity(0.3)
        )
        .listRowSeparator(.hidden)
        .listRowBackground(Color.clear)
        .listRowInsets(EdgeInsets(top: 6, leading: 16, bottom: 6, trailing: 16))
    }
    
    private func detailRow(label: String, value: String) -> some View {
        HStack {
            Text(label)
                .font(.caption)
                .foregroundColor(.secondary)
            Spacer()
            Text(value)
                .font(.caption)
                .fontWeight(.medium)
        }
    }
}

#Preview {
    GalleryView()
        .preferredColorScheme(.dark)
}
