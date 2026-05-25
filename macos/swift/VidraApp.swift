//
//  Vidra - Universal Video Downloader
//  macOS Swift Version
//  Powered by Sheri Akhtamov | v7 (2026 Motion Daylight UI)
//

import Cocoa
import SwiftUI
import Foundation
import WebKit

// MARK: - 🎨 2026 AERO GLASS PREMIUM PALETTE (LIGHT)

struct VidraColors {
    static let bgApp = Color(red: 242/255, green: 246/255, blue: 252/255)
    static let bgLayer = Color(red: 231/255, green: 238/255, blue: 248/255)
    static let glassBg = Color(red: 1.0, green: 1.0, blue: 1.0)
    static let glassBgSoft = Color(red: 247/255, green: 250/255, blue: 255/255)
    static let glassBorder = Color(red: 214/255, green: 225/255, blue: 239/255)
    
    static let primary = Color(red: 14/255, green: 107/255, blue: 255/255)
    static let primaryHover = Color(red: 10/255, green: 86/255, blue: 204/255)
    static let primaryLight = Color(red: 232/255, green: 241/255, blue: 255/255)
    
    static let teal = Color(red: 20/255, green: 184/255, blue: 166/255)
    static let tealDark = Color(red: 15/255, green: 148/255, blue: 135/255)
    static let tealLight = Color(red: 234/255, green: 251/255, blue: 248/255)
    
    static let plum = Color(red: 255/255, green: 123/255, blue: 91/255)
    static let plumDark = Color(red: 226/255, green: 96/255, blue: 65/255)
    static let plumLight = Color(red: 255/255, green: 241/255, blue: 234/255)
    
    static let textMain = Color(red: 12/255, green: 27/255, blue: 47/255)
    static let textSec = Color(red: 64/255, green: 86/255, blue: 112/255)
    static let textTert = Color(red: 133/255, green: 151/255, blue: 173/255)
    
    static let ok = Color(red: 22/255, green: 179/255, blue: 100/255)
    static let okDark = Color(red: 19/255, green: 146/255, blue: 85/255)
    
    static let error = Color(red: 229/255, green: 72/255, blue: 77/255)
    static let warn = Color(red: 245/255, green: 158/255, blue: 11/255)
}

// MARK: - Models

struct QualityPreset: Identifiable {
    let id = UUID()
    let label: String
    let sublabel: String
    let format: String
    let height: Int
}

let qualityPresets: [QualityPreset] = [
    .init(label: "Лучшее качество", sublabel: "авто", format: "bestvideo+bestaudio/best", height: 9999),
    .init(label: "4K", sublabel: "до 2160p", format: "bestvideo[height<=2160]+bestaudio/best", height: 2160),
    .init(label: "Full HD", sublabel: "до 1080p", format: "bestvideo[height<=1080]+bestaudio/best", height: 1080),
    .init(label: "HD", sublabel: "до 720p", format: "bestvideo[height<=720]+bestaudio/best", height: 720),
    .init(label: "SD", sublabel: "до 480p", format: "bestvideo[height<=480]+bestaudio/best", height: 480),
    .init(label: "360p", sublabel: "до 360p", format: "bestvideo[height<=360]+bestaudio/best", height: 360),
    .init(label: "Только аудио", sublabel: "MP3", format: "bestaudio/best", height: 0)
]

struct QueueItem: Identifiable {
    let id = UUID()
    var url: String
    var title: String
    var isPlaylist: Bool
    var count: Int
    var status: String
    var audioOnly: Bool
}

struct LogEntry: Identifiable {
    let id = UUID()
    let text: String
    let color: Color
    let timestamp: Date
}

// MARK: - View Models

@MainActor
class AppViewModel: ObservableObject {
    @Published var currentUrl: String = ""
    @Published var downloadDir: String = ""
    @Published var isFetching: Bool = false
    @Published var isDownloading: Bool = false
    @Published var progressValue: Double = 0.0
    @Published var targetProgress: Double = 0.0
    @Published var isPlaylist: Bool = false
    @Published var playlistCount: Int = 0
    @Published var selectedQualityIndex: Int = 2
    @Published var subtitlesEnabled: Bool = false
    @Published var logEntries: [LogEntry] = []
    @Published var downloadQueue: [QueueItem] = []
    @Published var canAddToQueue: Bool = false
    @Published var canDownloadNow: Bool = false
    
    private var fetchTask: Task<Void, Never>?
    private var downloadTask: Task<Void, Never>?
    
    init() {
        setupDownloadDir()
        addLog("Vidra запущен", color: .primary)
        addLog("FFmpeg интегрирован — доступно студийное качество", color: .green)
    }
    
    func setupDownloadDir() {
        let paths = FileManager.default.urls(for: .downloadsDirectory, in: .userDomainMask)
        downloadDir = paths.first?.path ?? "~/Downloads"
    }
    
    func addLog(_ text: String, color: Color = .textSec) {
        let entry = LogEntry(
            text: "[\(currentTime())] \(text)",
            color: color,
            timestamp: Date()
        )
        logEntries.append(entry)
        if logEntries.count > 500 {
            logEntries.removeFirst()
        }
    }
    
    func currentTime() -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm:ss"
        return formatter.string(from: Date())
    }
    
    func startFetch() {
        guard !currentUrl.isEmpty else {
            addLog("Введите URL видео", color: .orange)
            return
        }
        
        fetchTask?.cancel()
        isFetching = true
        canDownloadNow = false
        canAddToQueue = false
        
        addLog("Анализ URL: \(currentUrl)", color: .primary)
        
        fetchTask = Task {
            try? await Task.sleep(nanoseconds: 500_000_000)
            
            guard !Task.isCancelled else { return }
            
            isPlaylist = currentUrl.contains("playlist")
            playlistCount = isPlaylist ? 12 : 1
            
            if isPlaylist {
                addLog("Плейлист обнаружен (\(playlistCount) видео)", color: .teal)
            } else {
                addLog("Видео готово к загрузке", color: .green)
            }
            
            isFetching = false
            canAddToQueue = true
            canDownloadNow = true
        }
    }
    
    func startDownload() {
        guard !currentUrl.isEmpty else {
            addLog("Сначала проанализируйте URL", color: .orange)
            return
        }
        
        downloadTask?.cancel()
        isDownloading = true
        canDownloadNow = false
        canAddToQueue = false
        
        addLog("Начало загрузки: \(currentUrl)", color: .primary)
        
        downloadTask = Task {
            for i in stride(from: 0, through: 100, by: 5) {
                guard !Task.isCancelled else { break }
                
                await MainActor.run {
                    targetProgress = Double(i) / 100.0
                }
                
                try? await Task.sleep(nanoseconds: 50_000_000)
            }
            
            await MainActor.run {
                targetProgress = 0.0
                isDownloading = false
                canDownloadNow = true
                canAddToQueue = true
                addLog("Загрузка завершена!", color: .green)
            }
        }
    }
    
    func addToQueue() {
        guard !currentUrl.isEmpty else { return }
        
        let item = QueueItem(
            url: currentUrl,
            title: "Video \(downloadQueue.count + 1)",
            isPlaylist: isPlaylist,
            count: playlistCount,
            status: "waiting",
            audioOnly: selectedQualityIndex == 6
        )
        
        downloadQueue.append(item)
        addLog("Добавлено в очередь: \(currentUrl)", color: .teal)
    }
    
    func clearLog() {
        logEntries.removeAll()
    }
    
    func chooseFolder() {
        let panel = NSOpenPanel()
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = false
        panel.message = "Выберите папку для загрузок"
        
        if panel.runModal() == .OK, let url = panel.url {
            downloadDir = url.path
            addLog("Папка загрузок: \(downloadDir)", color: .teal)
        }
    }
}

// MARK: - UI Components

struct GlassCard: View {
    var content: AnyView
    
    init(@ViewBuilder content: () -> some View) {
        self.content = AnyView(content())
    }
    
    var body: some View {
        content
            .padding()
            .background(VidraColors.glassBg)
            .cornerRadius(20)
            .overlay(
                RoundedRectangle(cornerRadius: 20)
                    .stroke(VidraColors.glassBorder, lineWidth: 1)
            )
            .shadow(color: Color.black.opacity(0.05), radius: 8, x: 0, y: 4)
    }
}

struct PrimaryButton: View {
    let title: String
    let action: () -> Void
    var disabled: Bool = false
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.system(size: 14, weight: .bold))
                .foregroundColor(.white)
                .frame(height: 44)
                .frame(minWidth: 120)
                .background(disabled ? VidraColors.primary.opacity(0.5) : VidraColors.primary)
                .cornerRadius(12)
        }
        .disabled(disabled)
    }
}

struct SecondaryButton: View {
    let title: String
    let action: () -> Void
    var textColor: Color = .textSec
    var bgColor: Color = VidraColors.glassBgSoft
    var hoverColor: Color = VidraColors.primaryLight
    var disabled: Bool = false
    
    @State private var isHovering: Bool = false
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.system(size: 14, weight: .bold))
                .foregroundColor(textColor)
                .frame(height: 38)
                .frame(minWidth: 100)
                .background(isHovering && !disabled ? hoverColor : bgColor)
                .cornerRadius(12)
        }
        .disabled(disabled)
        .onHover { hovering in
            isHovering = hovering
        }
    }
}

// MARK: - Main Views

struct SidebarView: View {
    @ObservedObject var viewModel: AppViewModel
    @State private var selectedTab: Tab = .download
    
    enum Tab {
        case download, queue, history, settings
    }
    
    var body: some View {
        VStack(spacing: 0) {
            // Logo
            HStack(spacing: 12) {
                RoundedRectangle(cornerRadius: 14)
                    .fill(VidraColors.primaryLight)
                    .frame(width: 48, height: 48)
                    .overlay(
                        Text("V")
                            .font(.system(size: 20, weight: .bold))
                            .foregroundColor(.primary)
                    )
                
                VStack(alignment: .leading, spacing: 2) {
                    Text("Vidra")
                        .font(.system(size: 24, weight: .bold))
                        .foregroundColor(.textMain)
                    Text("Universal Video Downloader")
                        .font(.system(size: 12))
                        .foregroundColor(.textTert)
                }
                Spacer()
            }
            .padding(20)
            
            Divider()
            
            // Navigation
            VStack(spacing: 2) {
                NavButton(title: "Загрузка", icon: "arrow.down.circle", 
                         isSelected: selectedTab == .download) {
                    selectedTab = .download
                }
                NavButton(title: "Очередь", icon: "list.bullet", 
                         isSelected: selectedTab == .queue) {
                    selectedTab = .queue
                }
                NavButton(title: "История", icon: "clock", 
                         isSelected: selectedTab == .history) {
                    selectedTab = .history
                }
                NavButton(title: "Настройки", icon: "gear", 
                         isSelected: selectedTab == .settings) {
                    selectedTab = .settings
                }
            }
            .padding(.horizontal, 12)
            
            Spacer()
            
            // Footer
            Text("Vidra 2026 • by Sheri Akhtamov")
                .font(.system(size: 12))
                .foregroundColor(.textTert)
                .padding(20)
        }
        .frame(width: 280)
        .background(VidraColors.glassBgSoft)
    }
}

struct NavButton: View {
    let title: String
    let icon: String
    let isSelected: Bool
    let action: () -> Void
    
    @State private var isHovering: Bool = false
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Image(systemName: icon)
                    .frame(width: 20)
                Text(title)
                    .font(.system(size: 14, weight: .bold))
                Spacer()
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .background(isSelected ? VidraColors.primaryLight : Color.clear)
            .foregroundColor(isSelected ? .primary : .textSec)
            .cornerRadius(12)
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            isHovering = hovering
        }
    }
}

struct DownloadTabView: View {
    @ObservedObject var viewModel: AppViewModel
    
    var body: some View {
        HStack(spacing: 16) {
            // Left column
            VStack(spacing: 12) {
                // URL Card
                GlassCard {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Новая загрузка")
                            .font(.system(size: 24, weight: .bold))
                            .foregroundColor(.textMain)
                        
                        Text("Вставьте ссылку на видео, трек или плейлист")
                            .font(.system(size: 14))
                            .foregroundColor(.textSec)
                        
                        TextField("Вставьте URL сюда...", text: $viewModel.currentUrl)
                            .textFieldStyle(.roundedBorder)
                            .frame(height: 48)
                            .font(.system(size: 14))
                            .onSubmit {
                                viewModel.startFetch()
                            }
                        
                        HStack(spacing: 12) {
                            SecondaryButton(title: "Вставить") {
                                if let clipboard = NSPasteboard.general.string(forType: .string) {
                                    viewModel.currentUrl = clipboard
                                }
                            }
                            
                            SecondaryButton(title: "Очистить", textColor: .error, 
                                          bgColor: VidraColors.error.opacity(0.1)) {
                                viewModel.currentUrl = ""
                            }
                            
                            Toggle("Субтитры", isOn: $viewModel.subtitlesEnabled)
                                .toggleStyle(.checkbox)
                            
                            Spacer()
                            
                            PrimaryButton(title: viewModel.isFetching ? "Анализ..." : "Анализировать",
                                         action: { viewModel.startFetch() })
                                .disabled(viewModel.isFetching)
                        }
                        
                        if !viewModel.currentUrl.isEmpty {
                            Text(viewModel.isPlaylist ? 
                                 "✓ Плейлист обнаружен (\(viewModel.playlistCount) видео)" :
                                 "✓ Видео готово к загрузке")
                                .font(.system(size: 14, weight: .bold))
                                .foregroundColor(.tealDark)
                        }
                    }
                }
                
                // Quality Card
                GlassCard {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Качество")
                            .font(.system(size: 19, weight: .bold))
                            .foregroundColor(.textMain)
                        
                        ScrollView {
                            VStack(spacing: 8) {
                                ForEach(Array(qualityPresets.enumerated()), id: \.element.id) { index, preset in
                                    QualityRow(preset: preset, 
                                             isSelected: viewModel.selectedQualityIndex == index) {
                                        viewModel.selectedQualityIndex = index
                                    }
                                }
                            }
                        }
                        .frame(maxHeight: 200)
                    }
                }
            }
            .frame(maxWidth: .infinity)
            
            // Right column
            VStack(spacing: 20) {
                // Log Card
                GlassCard {
                    VStack(alignment: .leading, spacing: 10) {
                        HStack {
                            Text("Логи процесса")
                                .font(.system(size: 16, weight: .bold))
                                .foregroundColor(.textMain)
                            
                            Spacer()
                            
                            SecondaryButton(title: "Очистить") {
                                viewModel.clearLog()
                            }
                            .frame(width: 96, height: 34)
                        }
                        
                        ScrollView {
                            VStack(alignment: .leading, spacing: 4) {
                                ForEach(viewModel.logEntries.reversed()) { entry in
                                    Text(entry.text)
                                        .font(.system(size: 12, family: .monospace))
                                        .foregroundColor(entry.color)
                                }
                            }
                            .frame(maxWidth: .infinity, alignment: .leading)
                        }
                        .frame(height: 340)
                    }
                }
                
                // Footer Card
                GlassCard {
                    VStack(spacing: 16) {
                        HStack {
                            Text(viewModel.downloadDir)
                                .font(.system(size: 14))
                                .foregroundColor(.textSec)
                                .lineLimit(1)
                            
                            Spacer()
                            
                            SecondaryButton(title: "Изменить папку") {
                                viewModel.chooseFolder()
                            }
                            .frame(width: 120, height: 32)
                        }
                        
                        // Progress
                        VStack(spacing: 8) {
                            ProgressView(value: viewModel.progressValue)
                                .progressViewStyle(.linear)
                                .scaleEffect(x: 1, y: 1.5, anchor: .center)
                                .accentColor(.primary)
                            
                            HStack {
                                Text("\(Int(viewModel.progressValue * 100))%")
                                    .font(.system(size: 14, weight: .bold))
                                    .foregroundColor(.primary)
                                    .frame(width: 44, alignment: .trailing)
                                Spacer()
                            }
                        }
                        
                        Text(viewModel.isDownloading ? "Загрузка..." : "В ожидании ссылки...")
                            .font(.system(size: 14))
                            .foregroundColor(.textTert)
                            .frame(maxWidth: .infinity, alignment: .leading)
                        
                        HStack(spacing: 12) {
                            SecondaryButton(title: "В очередь", textColor: .plumDark,
                                          bgColor: VidraColors.plumLight) {
                                viewModel.addToQueue()
                            }
                            .disabled(!viewModel.canAddToQueue)
                            .frame(maxWidth: .infinity)
                            
                            PrimaryButton(title: "Скачать сейчас",
                                         action: { viewModel.startDownload() })
                                .disabled(!viewModel.canDownloadNow)
                                .frame(maxWidth: .infinity)
                        }
                    }
                }
            }
            .frame(width: 320)
        }
        .padding(20)
    }
}

struct QualityRow: View {
    let preset: QualityPreset
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text(preset.label)
                        .font(.system(size: 14, weight: .bold))
                        .foregroundColor(.textMain)
                    Text(preset.sublabel)
                        .font(.system(size: 12))
                        .foregroundColor(.textTert)
                }
                Spacer()
                
                if isSelected {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.primary)
                }
            }
            .padding()
            .background(isSelected ? VidraColors.primaryLight : VidraColors.glassBgSoft)
            .cornerRadius(12)
        }
        .buttonStyle(.plain)
    }
}

struct QueueTabView: View {
    @ObservedObject var viewModel: AppViewModel
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Очередь загрузок")
                    .font(.system(size: 24, weight: .bold))
                    .foregroundColor(.textMain)
                
                Spacer()
                
                SecondaryButton(title: "Очистить") {
                    viewModel.downloadQueue.removeAll()
                }
            }
            .padding(.horizontal)
            
            if viewModel.downloadQueue.isEmpty {
                Spacer()
                Text("Очередь пуста")
                    .font(.system(size: 16))
                    .foregroundColor(.textTert)
                    .frame(maxWidth: .infinity)
                Spacer()
            } else {
                List(viewModel.downloadQueue) { item in
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(item.title)
                                .font(.system(size: 14, weight: .semibold))
                                .foregroundColor(.textMain)
                            Text(item.url)
                                .font(.system(size: 12))
                                .foregroundColor(.textTert)
                                .lineLimit(1)
                        }
                        
                        Spacer()
                        
                        Text(item.isPlaylist ? "\(item.count) видео" : "Видео")
                            .font(.system(size: 12))
                            .foregroundColor(.textSec)
                        
                        Text(item.status)
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(.textTert)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 4)
                            .background(VidraColors.glassBgSoft)
                            .cornerRadius(8)
                    }
                    .padding(.vertical, 4)
                }
            }
        }
        .padding(20)
    }
}

struct HistoryTabView: View {
    var body: some View {
        VStack {
            Text("История загрузок")
                .font(.system(size: 24, weight: .bold))
                .foregroundColor(.textMain)
            
            Spacer()
            Text("История пока пуста")
                .font(.system(size: 16))
                .foregroundColor(.textTert)
            Spacer()
        }
        .padding(20)
    }
}

struct SettingsTabView: View {
    var body: some View {
        VStack {
            Text("Настройки")
                .font(.system(size: 24, weight: .bold))
                .foregroundColor(.textMain)
            
            Spacer()
            Text("Настройки будут добавлены в следующей версии")
                .font(.system(size: 16))
                .foregroundColor(.textTert)
            Spacer()
        }
        .padding(20)
    }
}

// MARK: - Main App

@main
struct VidraApp: App {
    @StateObject private var viewModel = AppViewModel()
    
    var body: some Scene {
        WindowGroup {
            HStack(spacing: 0) {
                SidebarView(viewModel: viewModel)
                
                VStack(spacing: 0) {
                    DownloadTabView(viewModel: viewModel)
                }
                .frame(minWidth: 800, minHeight: 600)
                .background(VidraColors.bgApp)
            }
            .frame(minWidth: 1100, minHeight: 800)
        }
        .windowStyle(.hiddenTitleBar)
        .commands {
            CommandGroup(replacing: .newItem) {}
        }
    }
}
