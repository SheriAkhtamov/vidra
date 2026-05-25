# Vidra - macOS Swift Build Instructions

## Требования

- macOS 13.0 (Ventura) или новее
- Xcode 15.0 или новее
- Swift 5.9 или новее

## Сборка через Xcode

### Вариант 1: SwiftUI App (рекомендуется)

1. Откройте Xcode
2. Создайте новый проект: **File → New → Project**
3. Выберите шаблон: **macOS → App**
4. Настройте проект:
   - Product Name: `Vidra`
   - Team: Ваша команда разработчика
   - Organization Identifier: `com.yourcompany`
   - Interface: **SwiftUI**
   - Language: **Swift**
5. Замените содержимое файла `VidraApp.swift` на код из `/workspace/macos/swift/VidraApp.swift`
6. В настройках проекта (Target → Vidra):
   - Deployment Target: macOS 13.0+
   - Arch: **Arm64** (для Apple Silicon) или **x86_64** (для Intel)
7. Соберите проект: **Product → Build** (⌘B)
8. Запустите: **Product → Run** (⌘R)

### Вариант 2: Командная строка (swiftc)

```bash
cd macos/swift

# Сборка исполняемого файла
swiftc -o Vidra VidraApp.swift \
    -framework Cocoa \
    -framework SwiftUI \
    -framework Foundation \
    -target arm64-apple-macos13.0

# Для Intel Mac:
# swiftc -o Vidra VidraApp.swift \
#     -framework Cocoa \
#     -framework SwiftUI \
#     -framework Foundation \
#     -target x86_64-apple-macos13.0
```

## Создание .app бандла

```bash
cd macos/swift

# Создайте структуру приложения
mkdir -p Vidra.app/Contents/MacOS
mkdir -p Vidra.app/Contents/Resources

# Скопируйте исполняемый файл
cp Vidra Vidra.app/Contents/MacOS/

# Создайте Info.plist
cat > Vidra.app/Contents/Info.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>Vidra</string>
    <key>CFBundleIdentifier</key>
    <string>com.sheriakhtamov.vidra</string>
    <key>CFBundleName</key>
    <string>Vidra</string>
    <key>CFBundleVersion</key>
    <string>7.0</string>
    <key>CFBundleShortVersionString</key>
    <string>2026.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>13.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Теперь можно запустить
open Vidra.app
```

## Архитектурные особенности

- **SwiftUI** для современного декларативного UI
- **MVVM паттерн** с `AppViewModel` для управления состоянием
- **Async/await** для асинхронных операций
- **@MainActor** для потокобезопасности UI
- **Native macOS дизайн** с использованием системных цветов и шрифтов

## Примечания

- Приложение использует нативный SwiftUI для создания UI
- Все цвета соответствуют дизайну 2026 Aero Glass Premium Palette
- Поддержка как Apple Silicon (M1/M2/M3), так и Intel Mac
- Минимальная версия macOS: 13.0 (Ventura)

## Распространение

Для распространения приложения:

1. **Notarization**: Подпишите приложение через Apple Developer Program
2. **DMG**: Создайте образ диска для распространения
   ```bash
   hdiutil create -volname "Vidra" -srcfolder Vidra.app -ov -format UDZO Vidra.dmg
   ```
