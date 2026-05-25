# Vidra - Windows C++ Build Instructions

## Требования

- Visual Studio 2022 или новее
- Windows SDK 10.0 или новее
- Компилятор с поддержкой C++17

## Сборка через командную строку (MSVC)

```batch
:: Откройте "Developer Command Prompt for VS 2022"
cd windows\cpp

:: Компиляция
cl.exe /EHsc /std:c++17 /O2 vidra.cpp /Fe:Vidra.exe /link ^
    comctl32.lib gdi32.lib user32.lib shell32.lib ole32.lib uuid.lib wininet.lib shlwapi.lib ^
    /SUBSYSTEM:WINDOWS

:: Готово! Vidra.exe создан
```

## Сборка через Visual Studio IDE

1. Создайте новый проект "Windows Desktop Application"
2. Добавьте файл `vidra.cpp` в проект
3. В свойствах проекта:
   - Configuration: Release
   - Platform: x64
   - C++ Language Standard: C++17
   - Linker → System → SubSystem: Windows (/SUBSYSTEM:WINDOWS)
4. Добавьте библиотеки в Linker → Input → Additional Dependencies:
   ```
   comctl32.lib;gdi32.lib;user32.lib;shell32.lib;ole32.lib;uuid.lib;wininet.lib;shlwapi.lib
   ```
5. Соберите проект (Ctrl+Shift+B)

## Запуск

Просто запустите `Vidra.exe`

## Примечания

- Приложение использует нативный Win32 API для создания UI
- Поддержка многопоточности через std::thread
- Плавная анимация прогресса через таймер
- Все цвета соответствуют дизайну 2026 Aero Glass Premium Palette
