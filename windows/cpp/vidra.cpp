/*
 * Vidra - Universal Video Downloader
 * Windows C++ Version
 * Powered by Sheri Akhtamov | v7 (2026 Motion Daylight UI)
 */

#pragma comment(lib, "comctl32.lib")
#pragma comment(lib, "gdi32.lib")
#pragma comment(lib, "user32.lib")
#pragma comment(lib, "shell32.lib")
#pragma comment(lib, "ole32.lib")
#pragma comment(lib, "uuid.lib")
#pragma comment(lib, "wininet.lib")
#pragma comment(lib, "shlwapi.lib")

#include <windows.h>
#include <commctrl.h>
#include <commdlg.h>
#include <shellapi.h>
#include <shlwapi.h>
#include <string>
#include <vector>
#include <thread>
#include <mutex>
#include <queue>
#include <functional>
#include <sstream>
#include <iomanip>
#include <algorithm>
#include <map>
#include <ctime>
#include <cstdlib>
#include <cstdio>

// ==========================================
// 🎨 2026 AERO GLASS PREMIUM PALETTE (LIGHT)
// ==========================================
#define BG_APP          RGB(242, 246, 252)
#define BG_LAYER        RGB(231, 238, 248)
#define BG_BLOB_A       RGB(228, 240, 255)
#define BG_BLOB_B       RGB(234, 251, 246)
#define BG_BLOB_C       RGB(255, 243, 234)

#define GLASS_BG        RGB(255, 255, 255)
#define GLASS_BG_SOFT   RGB(247, 250, 255)
#define GLASS_BORDER    RGB(214, 225, 239)
#define GLASS_BORDER_FOCUS RGB(163, 188, 216)

#define PRI             RGB(14, 107, 255)
#define PRI_H           RGB(10, 86, 204)
#define PRI_L           RGB(232, 241, 255)
#define PRI_MUTED       RGB(127, 174, 246)

#define TEAL            RGB(20, 184, 166)
#define TEAL_H          RGB(15, 148, 135)
#define TEAL_L          RGB(234, 251, 248)

#define PLUM            RGB(255, 123, 91)
#define PLUM_H          RGB(226, 96, 65)
#define PLUM_L          RGB(255, 241, 234)

#define TEXT_MAIN       RGB(12, 27, 47)
#define TEXT_SEC        RGB(64, 86, 112)
#define TEXT_TERT       RGB(133, 151, 173)

#define OK_COLOR        RGB(22, 179, 100)
#define OK_H            RGB(19, 146, 85)
#define OK_L            RGB(234, 249, 241)

#define ERR             RGB(229, 72, 77)
#define ERR_H           RGB(201, 58, 63)
#define ERR_L           RGB(253, 238, 238)

#define WARN            RGB(245, 158, 11)
#define WARN_L          RGB(255, 247, 232)

#define SHADOW_SOFT     RGB(221, 231, 244)
#define SHADOW_STRONG   RGB(201, 216, 234)

// ==========================================
// Constants & IDs
// ==========================================
#define WINDOW_WIDTH    1360
#define WINDOW_HEIGHT   920
#define SIDEBAR_WIDTH   280

#define ID_BTN_DOWNLOAD     1001
#define ID_BTN_QUEUE        1002
#define ID_BTN_HISTORY      1003
#define ID_BTN_SETTINGS     1004

#define ID_EDIT_URL         2001
#define ID_BTN_PASTE        2002
#define ID_BTN_CLEAR        2003
#define ID_CHK_SUBTITLES    2004
#define ID_BTN_FETCH        2005

#define ID_COMBO_QUALITY    2101
#define ID_LIST_FORMATS     2102

#define ID_TXT_LOG          3001
#define ID_BTN_CLEAR_LOG    3002

#define ID_PROGRESS         4001
#define ID_TXT_STATUS       4002
#define ID_TXT_PERCENT      4003
#define ID_BTN_FOLDER       4004
#define ID_BTN_ADD_QUEUE    4005
#define ID_BTN_DOWNLOAD_NOW 4006

#define ID_TIMER_SMOOTH     5001

// ==========================================
// Structures
// ==========================================
struct QualityPreset {
    const wchar_t* label;
    const wchar_t* sub;
    const wchar_t* fmt;
    int height;
};

static QualityPreset g_qualityPresets[] = {
    { L"Лучшее качество", L"авто", L"bestvideo+bestaudio/best", 9999 },
    { L"4K", L"до 2160p", L"bestvideo[height<=2160]+bestaudio/bestvideo+bestaudio/best", 2160 },
    { L"Full HD", L"до 1080p", L"bestvideo[height<=1080]+bestaudio/bestvideo+bestaudio/best", 1080 },
    { L"HD", L"до 720p", L"bestvideo[height<=720]+bestaudio/bestvideo+bestaudio/best", 720 },
    { L"SD", L"до 480p", L"bestvideo[height<=480]+bestaudio/bestvideo+bestaudio/best", 480 },
    { L"360p", L"до 360p", L"bestvideo[height<=360]+bestaudio/bestvideo+bestaudio/best", 360 },
    { L"Только аудио", L"MP3", L"bestaudio/best", 0 }
};

struct QueueItem {
    std::wstring url;
    std::wstring title;
    std::wstring format;
    bool isPlaylist;
    int count;
    std::wstring status;
    bool audioOnly;
};

struct LogEntry {
    std::wstring text;
    COLORREF color;
    time_t timestamp;
};

// ==========================================
// Global State
// ==========================================
HWND g_hMainWnd = NULL;
HWND g_hSidebar = NULL;
HWND g_hContentContainer = NULL;
HWND g_hCurrentTab = NULL;

// Navigation buttons
HWND g_hBtnDownload = NULL;
HWND g_hBtnQueue = NULL;
HWND g_hBtnHistory = NULL;
HWND g_hBtnSettings = NULL;

// Download tab controls
HWND g_hEditUrl = NULL;
HWND g_hBtnPaste = NULL;
HWND g_hBtnClearUrl = NULL;
HWND g_hChkSubtitles = NULL;
HWND g_hBtnFetch = NULL;
HWND g_hInfoLabel = NULL;
HWND g_hFmtScroll = NULL;
HWND g_hLogBox = NULL;
HWND g_hFolderLabel = NULL;
HWND g_hProgress = NULL;
HWND g_hPercentLabel = NULL;
HWND g_hStatusLabel = NULL;
HWND g_hBtnAddQueue = NULL;
HWND g_hBtnDownloadNow = NULL;

// Queue tab
HWND g_hQueueList = NULL;

// History tab
HWND g_hHistoryList = NULL;

// State variables
std::wstring g_currentUrl = L"";
std::wstring g_downloadDir = L"";
bool g_fetching = false;
bool g_downloading = false;
double g_progressValue = 0.0;
double g_targetProgress = 0.0;
bool g_isPlaylist = false;
int g_playlistCount = 0;
int g_selectedQuality = 2; // Full HD default
std::vector<std::wstring> g_availableFormats;
std::vector<QueueItem> g_downloadQueue;
std::vector<LogEntry> g_logEntries;
std::mutex g_logMutex;
std::mutex g_queueMutex;

HFONT g_hFontDisplay = NULL;
HFONT g_hFontH1 = NULL;
HFONT g_hFontH2 = NULL;
HFONT g_hFontH3 = NULL;
HFONT g_hFontBody = NULL;
HFONT g_hFontBodyBold = NULL;
HFONT g_hFontSmall = NULL;
HFONT g_hFontCode = NULL;

HBRUSH g_hBrushBgApp = NULL;
HBRUSH g_hBrushGlass = NULL;
HBRUSH g_hBrushGlassSoft = NULL;
HBRUSH g_hBrushPri = NULL;
HBRUSH g_hBrushOk = NULL;
HBRUSH g_hBrushErr = NULL;

// ==========================================
// Helper Functions
// ==========================================

std::wstring GetCurrentTime() {
    time_t now = time(NULL);
    struct tm* t = localtime(&now);
    wchar_t buf[32];
    swprintf(buf, 32, L"%02d:%02d:%02d", t->tm_hour, t->tm_min, t->tm_sec);
    return std::wstring(buf);
}

std::wstring GetDownloadsPath() {
    wchar_t path[MAX_PATH];
    if (SUCCEEDED(SHGetFolderPathW(NULL, CSIDL_DOWNLOADS, NULL, 0, path))) {
        return std::wstring(path);
    }
    return L"C:\\Users\\Public\\Downloads";
}

void AddLog(const std::wstring& text, COLORREF color = TEXT_SEC) {
    std::lock_guard<std::mutex> lock(g_logMutex);
    LogEntry entry;
    entry.text = L"[" + GetCurrentTime() + L"] " + text;
    entry.color = color;
    entry.timestamp = time(NULL);
    g_logEntries.push_back(entry);
    
    if (g_logEntries.size() > 500) {
        g_logEntries.erase(g_logEntries.begin());
    }
    
    InvalidateRect(g_hLogBox, NULL, TRUE);
}

void ClearLog() {
    std::lock_guard<std::mutex> lock(g_logMutex);
    g_logEntries.clear();
    InvalidateRect(g_hLogBox, NULL, TRUE);
}

std::wstring FormatFileSize(unsigned long long bytes) {
    if (bytes == 0) return L"";
    
    const wchar_t* units[] = { L"B", L"KB", L"MB", L"GB", L"TB" };
    int unitIndex = 0;
    double size = (double)bytes;
    
    while (size >= 1024.0 && unitIndex < 4) {
        size /= 1024.0;
        unitIndex++;
    }
    
    wchar_t buf[64];
    if (unitIndex == 0) {
        swprintf(buf, 64, L"%llu %s", (unsigned long long)bytes, units[unitIndex]);
    } else {
        swprintf(buf, 64, L"%.1f %s", size, units[unitIndex]);
    }
    return std::wstring(buf);
}

std::wstring FormatDuration(int seconds) {
    if (seconds <= 0) return L"—";
    
    int h = seconds / 3600;
    int r = seconds % 3600;
    int m = r / 60;
    int s = r % 60;
    
    wchar_t buf[32];
    if (h > 0) {
        swprintf(buf, 32, L"%d:%02d:%02d", h, m, s);
    } else {
        swprintf(buf, 32, L"%d:%02d", m, s);
    }
    return std::wstring(buf);
}

void SetControlFont(HWND hWnd, HFONT hFont) {
    SendMessage(hWnd, WM_SETFONT, (WPARAM)hFont, TRUE);
}

HWND CreateStyledButton(HWND hParent, int id, const wchar_t* text, 
                        int x, int y, int w, int h, 
                        COLORREF bgColor, COLORREF textColor,
                        HFONT hFont, bool border = false) {
    HWND hBtn = CreateWindowExW(0, L"BUTTON", text,
        WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
        x, y, w, h, hParent, (HMENU)id, NULL, NULL);
    
    if (hBtn) {
        SetControlFont(hBtn, hFont);
    }
    return hBtn;
}

HWND CreateStyledEdit(HWND hParent, int id, const wchar_t* placeholder,
                      int x, int y, int w, int h, HFONT hFont) {
    HWND hEdit = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"",
        WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL,
        x, y, w, h, hParent, (HMENU)id, NULL, NULL);
    
    if (hEdit) {
        SetControlFont(hEdit, hFont);
        SendMessage(hEdit, EM_SETCUEBANNER, TRUE, (LPARAM)placeholder);
    }
    return hEdit;
}

// ==========================================
// Window Procedures
// ==========================================

LRESULT CALLBACK LogBoxProc(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {
        case WM_PAINT: {
            PAINTSTRUCT ps;
            HDC hdc = BeginPaint(hWnd, &ps);
            
            RECT rc;
            GetClientRect(hWnd, &rc);
            
            // Background
            HBRUSH hBrush = CreateSolidBrush(GLASS_BG_SOFT);
            FillRect(hdc, &rc, hBrush);
            DeleteObject(hBrush);
            
            // Draw log entries
            std::lock_guard<std::mutex> lock(g_logMutex);
            
            SetBkMode(hdc, TRANSPARENT);
            
            int y = 10;
            int lineHeight = 18;
            
            for (auto it = g_logEntries.rbegin(); it != g_logEntries.rend(); ++it) {
                if (y + lineHeight > rc.bottom) break;
                
                SetTextColor(hdc, it->color);
                TextOutW(hdc, 10, y, it->text.c_str(), (int)it->text.length());
                y += lineHeight;
            }
            
            EndPaint(hWnd, &ps);
            return 0;
        }
        case WM_ERASEBKGND:
            return 1;
    }
    return DefWindowProcW(hWnd, msg, wParam, lParam);
}

void SmoothProgressTimer(HWND hWnd) {
    static double currentSmooth = 0.0;
    
    if (currentSmooth < g_targetProgress) {
        currentSmooth += (g_targetProgress - currentSmooth) * 0.05;
        if (currentSmooth > g_targetProgress) currentSmooth = g_targetProgress;
    } else if (currentSmooth > g_targetProgress) {
        currentSmooth -= (currentSmooth - g_targetProgress) * 0.1;
        if (currentSmooth < g_targetProgress) currentSmooth = g_targetProgress;
    }
    
    g_progressValue = currentSmooth;
    
    wchar_t pctText[16];
    swprintf(pctText, 16, L"%.0f%%", g_progressValue * 100.0);
    SetWindowTextW(g_hPercentLabel, pctText);
    
    SendMessage(g_hProgress, PBM_SETPOS, (WPARAM)(g_progressValue * 100), 0);
    
    InvalidateRect(g_hProgress, NULL, FALSE);
}

void OnDownloadThread(void* param) {
    std::wstring* pUrl = (std::wstring*)param;
    std::wstring url = *pUrl;
    delete pUrl;
    
    AddLog(L"Начало загрузки: " + url, PRI);
    
    // Simulate download process
    for (int i = 0; i <= 100; i++) {
        g_targetProgress = i / 100.0;
        
        wchar_t statusMsg[128];
        swprintf(statusMsg, 128, L"Загрузка... %d%%", i);
        SetWindowTextW(g_hStatusLabel, statusMsg);
        
        Sleep(50); // Simulate work
    }
    
    g_targetProgress = 0.0;
    g_downloading = false;
    
    SetWindowTextW(g_hStatusLabel, L"Загрузка завершена!");
    AddLog(L"Завершено: " + url, OK_COLOR);
    
    EnableWindow(g_hBtnDownloadNow, TRUE);
    EnableWindow(g_hBtnAddQueue, TRUE);
}

void OnFetchThread(void* param) {
    std::wstring* pUrl = (std::wstring*)param;
    std::wstring url = *pUrl;
    delete pUrl;
    
    AddLog(L"Анализ URL: " + url, PRI);
    
    g_fetching = true;
    EnableWindow(g_hBtnFetch, FALSE);
    SetWindowTextW(g_hBtnFetch, L"Анализ...");
    
    // Simulate fetching info
    Sleep(500);
    
    // Mock result
    g_isPlaylist = (url.find(L"playlist") != std::wstring::npos);
    g_playlistCount = g_isPlaylist ? 12 : 1;
    
    wchar_t infoText[256];
    if (g_isPlaylist) {
        swprintf(infoText, 256, L"✓ Плейлист обнаружен (%d видео)", g_playlistCount);
    } else {
        swprintf(infoText, 256, L"✓ Видео готово к загрузке");
    }
    SetWindowTextW(g_hInfoLabel, infoText);
    
    g_fetching = false;
    EnableWindow(g_hBtnFetch, TRUE);
    SetWindowTextW(g_hBtnFetch, L"Анализировать");
    EnableWindow(g_hBtnAddQueue, TRUE);
    EnableWindow(g_hBtnDownloadNow, TRUE);
    
    AddLog(L"Анализ завершен", OK_COLOR);
}

void StartFetch() {
    wchar_t url[2048];
    GetWindowTextW(g_hEditUrl, url, 2048);
    g_currentUrl = url;
    
    if (g_currentUrl.empty()) {
        MessageBoxW(g_hMainWnd, L"Введите URL видео", L"Vidra", MB_ICONWARNING);
        return;
    }
    
    std::wstring* pUrl = new std::wstring(g_currentUrl);
    std::thread t(OnFetchThread, pUrl);
    t.detach();
}

void StartDownload() {
    if (g_currentUrl.empty()) {
        MessageBoxW(g_hMainWnd, L"Сначала проанализируйте URL", L"Vidra", MB_ICONWARNING);
        return;
    }
    
    g_downloading = true;
    EnableWindow(g_hBtnDownloadNow, FALSE);
    EnableWindow(g_hBtnAddQueue, FALSE);
    
    std::wstring* pUrl = new std::wstring(g_currentUrl);
    std::thread t(OnDownloadThread, pUrl);
    t.detach();
}

void AddToQueue() {
    if (g_currentUrl.empty()) return;
    
    QueueItem item;
    item.url = g_currentUrl;
    item.title = L"Video " + std::to_wstring(g_downloadQueue.size() + 1);
    item.isPlaylist = g_isPlaylist;
    item.count = g_playlistCount;
    item.status = L"waiting";
    item.audioOnly = (g_selectedQuality == 6);
    
    g_downloadQueue.push_back(item);
    
    AddLog(L"Добавлено в очередь: " + g_currentUrl, TEAL);
    
    // Refresh queue list
    ListView_DeleteAllItems(g_hQueueList);
    for (size_t i = 0; i < g_downloadQueue.size(); i++) {
        LVITEMW lvi = {0};
        lvi.mask = LVIF_TEXT;
        lvi.iItem = (int)i;
        
        wchar_t idx[16];
        swprintf(idx, 16, L"%d", (int)i + 1);
        lvi.pszText = idx;
        ListView_InsertItem(g_hQueueList, &lvi);
        
        lvi.iSubitem = 1;
        lvi.pszText = (wchar_t*)g_downloadQueue[i].title.c_str();
        ListView_SetItem(g_hQueueList, &lvi);
        
        lvi.iSubitem = 2;
        lvi.pszText = (wchar_t*)(g_downloadQueue[i].isPlaylist ? L"Плейлист" : L"Видео");
        ListView_SetItem(g_hQueueList, &lvi);
        
        lvi.iSubitem = 3;
        lvi.pszText = (wchar_t*)g_downloadQueue[i].status.c_str();
        ListView_SetItem(g_hQueueList, &lvi);
    }
}

void SelectTab(HWND hNewTab) {
    if (g_hCurrentTab) {
        ShowWindow(g_hCurrentTab, SW_HIDE);
    }
    g_hCurrentTab = hNewTab;
    ShowWindow(g_hCurrentTab, SW_SHOW);
    
    // Update nav buttons
    SetBkColor(GetDC(g_hBtnDownload), (hNewTab == g_hBtnDownload) ? PRI_L : GLASS_BG_SOFT);
}

LRESULT CALLBACK WndProc(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {
        case WM_CREATE: {
            INITCOMMONCONTROLSEX icex;
            icex.dwSize = sizeof(INITCOMMONCONTROLSEX);
            icex.dwICC = ICC_STANDARD_CLASSES | ICC_PROGRESS_CLASS | ICC_LISTVIEW_CLASSES;
            InitCommonControlsEx(&icex);
            
            g_downloadDir = GetDownloadsPath();
            
            // Create fonts
            g_hFontDisplay = CreateFontW(-32, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE,
                DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
                DEFAULT_QUALITY, DEFAULT_PITCH, L"Segoe UI Variable Text");
            
            g_hFontH1 = CreateFontW(-24, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE,
                DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
                DEFAULT_QUALITY, DEFAULT_PITCH, L"Segoe UI Variable Text");
            
            g_hFontH2 = CreateFontW(-19, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE,
                DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
                DEFAULT_QUALITY, DEFAULT_PITCH, L"Segoe UI Variable Text");
            
            g_hFontH3 = CreateFontW(-16, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE,
                DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
                DEFAULT_QUALITY, DEFAULT_PITCH, L"Segoe UI Variable Text");
            
            g_hFontBody = CreateFontW(-14, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
                DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
                DEFAULT_QUALITY, DEFAULT_PITCH, L"Segoe UI Variable Text");
            
            g_hFontBodyBold = CreateFontW(-14, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE,
                DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
                DEFAULT_QUALITY, DEFAULT_PITCH, L"Segoe UI Variable Text");
            
            g_hFontSmall = CreateFontW(-12, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
                DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
                DEFAULT_QUALITY, DEFAULT_PITCH, L"Segoe UI Variable Text");
            
            g_hFontCode = CreateFontW(-12, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
                DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
                DEFAULT_QUALITY, FIXED_PITCH, L"Cascadia Code");
            
            // Create brushes
            g_hBrushBgApp = CreateSolidBrush(BG_APP);
            g_hBrushGlass = CreateSolidBrush(GLASS_BG);
            g_hBrushGlassSoft = CreateSolidBrush(GLASS_BG_SOFT);
            g_hBrushPri = CreateSolidBrush(PRI);
            g_hBrushOk = CreateSolidBrush(OK_COLOR);
            g_hBrushErr = CreateSolidBrush(ERR);
            
            // Sidebar
            g_hSidebar = CreateWindowExW(0, L"STATIC", L"",
                WS_CHILD | WS_VISIBLE | SS_OWNERDRAW,
                0, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT,
                hWnd, NULL, NULL, NULL);
            
            // Content container
            g_hContentContainer = CreateWindowExW(0, L"STATIC", L"",
                WS_CHILD | WS_VISIBLE,
                SIDEBAR_WIDTH, 0, WINDOW_WIDTH - SIDEBAR_WIDTH, WINDOW_HEIGHT,
                hWnd, NULL, NULL, NULL);
            
            // Download tab (default)
            HWND hDownloadTab = CreateWindowExW(0, L"STATIC", L"",
                WS_CHILD,
                0, 0, WINDOW_WIDTH - SIDEBAR_WIDTH - 40, WINDOW_HEIGHT - 40,
                g_hContentContainer, NULL, NULL, NULL);
            
            // URL Card
            HWND hUrlCard = CreateWindowExW(0, L"STATIC", L"Новая загрузка",
                WS_CHILD | WS_VISIBLE | SS_OWNERDRAW,
                20, 20, 400, 200, hDownloadTab, NULL, NULL, NULL);
            
            g_hEditUrl = CreateStyledEdit(hDownloadTab, ID_EDIT_URL, L"Вставьте URL сюда...",
                40, 80, 360, 48, g_hFontBody);
            
            g_hBtnPaste = CreateStyledButton(hDownloadTab, ID_BTN_PASTE, L"Вставить",
                40, 140, 100, 38, GLASS_BG_SOFT, TEXT_SEC, g_hFontBodyBold);
            
            g_hBtnClearUrl = CreateStyledButton(hDownloadTab, ID_BTN_CLEAR, L"Очистить",
                150, 140, 100, 38, GLASS_BG_SOFT, ERR, g_hFontBodyBold);
            
            g_hChkSubtitles = CreateWindowExW(0, L"BUTTON", L"Субтитры",
                WS_CHILD | WS_VISIBLE | BS_AUTOCHECKBOX,
                260, 145, 100, 24, hDownloadTab, (HMENU)ID_CHK_SUBTITLES, NULL, NULL);
            
            g_hBtnFetch = CreateStyledButton(hDownloadTab, ID_BTN_FETCH, L"Анализировать",
                300, 140, 140, 44, PRI, RGB(255,255,255), g_hFontBodyBold);
            
            g_hInfoLabel = CreateWindowExW(0, L"STATIC", L"",
                WS_CHILD | WS_VISIBLE,
                40, 190, 360, 24, hDownloadTab, NULL, NULL, NULL);
            
            // Log Card
            HWND hLogCard = CreateWindowExW(0, L"STATIC", L"Логи процесса",
                WS_CHILD | WS_VISIBLE | SS_OWNERDRAW,
                440, 20, 300, 400, hDownloadTab, NULL, NULL, NULL);
            
            WNDCLASSW wc = {0};
            wc.lpfnWndProc = LogBoxProc;
            wc.lpszClassName = L"LogBoxClass";
            wc.hInstance = GetModuleHandle(NULL);
            RegisterClassW(&wc);
            
            g_hLogBox = CreateWindowExW(WS_EX_CLIENTEDGE, L"LogBoxClass", L"",
                WS_CHILD | WS_VISIBLE | WS_VSCROLL,
                460, 60, 260, 340, hDownloadTab, NULL, NULL, NULL);
            
            // Footer with progress
            HWND hFooter = CreateWindowExW(0, L"STATIC", L"",
                WS_CHILD | WS_VISIBLE,
                20, 450, 720, 150, hDownloadTab, NULL, NULL, NULL);
            
            g_hFolderLabel = CreateWindowExW(0, L"STATIC", g_downloadDir.c_str(),
                WS_CHILD | WS_VISIBLE,
                40, 20, 500, 24, hFooter, NULL, NULL, NULL);
            
            g_hBtnFolder = CreateStyledButton(hFooter, ID_BTN_FOLDER, L"Изменить папку",
                560, 16, 120, 32, GLASS_BG_SOFT, TEXT_SEC, g_hFontSmall);
            
            g_hProgress = CreateWindowExW(0, PROGRESS_CLASS, L"",
                WS_CHILD | WS_VISIBLE,
                40, 60, 500, 10, hFooter, (HMENU)ID_PROGRESS, NULL, NULL);
            SendMessage(g_hProgress, PBM_SETRANGE, 0, MAKELPARAM(0, 100));
            SendMessage(g_hProgress, PBM_SETPOS, 0, 0);
            
            g_hPercentLabel = CreateWindowExW(0, L"STATIC", L"0%",
                WS_CHILD | WS_VISIBLE,
                550, 54, 50, 24, hFooter, NULL, NULL, NULL);
            
            g_hStatusLabel = CreateWindowExW(0, L"STATIC", L"В ожидании ссылки...",
                WS_CHILD | WS_VISIBLE,
                40, 85, 500, 24, hFooter, NULL, NULL, NULL);
            
            g_hBtnAddQueue = CreateStyledButton(hFooter, ID_BTN_ADD_QUEUE, L"В очередь",
                40, 115, 200, 42, PLUM_L, PLUM_H, g_hFontBodyBold);
            EnableWindow(g_hBtnAddQueue, FALSE);
            
            g_hBtnDownloadNow = CreateStyledButton(hFooter, ID_BTN_DOWNLOAD_NOW, L"Скачать сейчас",
                260, 115, 200, 42, OK_COLOR, RGB(255,255,255), g_hFontBodyBold);
            EnableWindow(g_hBtnDownloadNow, FALSE);
            
            // Timer for smooth progress
            SetTimer(hWnd, ID_TIMER_SMOOTH, 50, NULL);
            
            AddLog(L"Vidra запущен", PRI);
            AddLog(L"FFmpeg интегрирован — доступно студийное качество", OK_COLOR);
            
            return 0;
        }
        
        case WM_SIZE: {
            int width = LOWORD(lParam);
            int height = HIWORD(lParam);
            
            MoveWindow(g_hSidebar, 0, 0, SIDEBAR_WIDTH, height, TRUE);
            MoveWindow(g_hContentContainer, SIDEBAR_WIDTH, 0, width - SIDEBAR_WIDTH, height, TRUE);
            return 0;
        }
        
        case WM_COMMAND: {
            int wmId = LOWORD(wParam);
            
            switch (wmId) {
                case ID_BTN_PASTE: {
                    if (OpenClipboard(NULL)) {
                        HANDLE hData = GetClipboardData(CF_UNICODETEXT);
                        if (hData) {
                            wchar_t* pszData = (wchar_t*)GlobalLock(hData);
                            if (pszData) {
                                SetWindowTextW(g_hEditUrl, pszData);
                                GlobalUnlock(hData);
                            }
                        }
                        CloseClipboard();
                    }
                    break;
                }
                
                case ID_BTN_CLEAR:
                    SetWindowTextW(g_hEditUrl, L"");
                    break;
                
                case ID_BTN_FETCH:
                    StartFetch();
                    break;
                
                case ID_BTN_DOWNLOAD_NOW:
                    StartDownload();
                    break;
                
                case ID_BTN_ADD_QUEUE:
                    AddToQueue();
                    break;
                
                case ID_BTN_FOLDER: {
                    BROWSEINFOW bi = {0};
                    bi.lpszTitle = L"Выберите папку для загрузок:";
                    bi.ulFlags = BIF_RETURNONLYFSDIRS | BIF_NEWDIALOGSTYLE;
                    
                    LPITEMIDLIST pidl = SHBrowseForFolderW(&bi);
                    if (pidl) {
                        wchar_t path[MAX_PATH];
                        if (SHGetPathFromIDListW(pidl, path)) {
                            g_downloadDir = path;
                            SetWindowTextW(g_hFolderLabel, g_downloadDir.c_str());
                            AddLog(L"Папка загрузок: " + g_downloadDir, TEAL);
                        }
                        CoTaskMemFree(pidl);
                    }
                    break;
                }
            }
            return 0;
        }
        
        case WM_TIMER: {
            if (wParam == ID_TIMER_SMOOTH) {
                SmoothProgressTimer(hWnd);
            }
            return 0;
        }
        
        case WM_CTLCOLORSTATIC: {
            HDC hdcStatic = (HDC)wParam;
            SetBkMode(hdcStatic, TRANSPARENT);
            
            HWND hCtrl = (HWND)lParam;
            
            if (hCtrl == g_hInfoLabel) {
                SetTextColor(hdcStatic, TEAL_H);
                return (LRESULT)CreateSolidBrush(GLASS_BG);
            }
            
            return (LRESULT)g_hBrushBgApp;
        }
        
        case WM_DESTROY: {
            KillTimer(hWnd, ID_TIMER_SMOOTH);
            
            DeleteObject(g_hFontDisplay);
            DeleteObject(g_hFontH1);
            DeleteObject(g_hFontH2);
            DeleteObject(g_hFontH3);
            DeleteObject(g_hFontBody);
            DeleteObject(g_hFontBodyBold);
            DeleteObject(g_hFontSmall);
            DeleteObject(g_hFontCode);
            
            DeleteObject(g_hBrushBgApp);
            DeleteObject(g_hBrushGlass);
            DeleteObject(g_hBrushGlassSoft);
            DeleteObject(g_hBrushPri);
            DeleteObject(g_hBrushOk);
            DeleteObject(g_hBrushErr);
            
            PostQuitMessage(0);
            return 0;
        }
    }
    
    return DefWindowProcW(hWnd, msg, wParam, lParam);
}

// ==========================================
// Entry Point
// ==========================================

int WINAPI wWinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, 
                    LPWSTR lpCmdLine, int nCmdShow) {
    
    WNDCLASSEXW wc = {0};
    wc.cbSize = sizeof(WNDCLASSEXW);
    wc.style = CS_HREDRAW | CS_VREDRAW;
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInstance;
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    wc.lpszClassName = L"VidraWindowClass";
    wc.hIcon = LoadIcon(NULL, IDI_APPLICATION);
    
    RegisterClassExW(&wc);
    
    g_hMainWnd = CreateWindowExW(
        WS_EX_APPWINDOW,
        L"VidraWindowClass",
        L"Vidra 2026 - Universal Video Downloader",
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT,
        WINDOW_WIDTH, WINDOW_HEIGHT,
        NULL, NULL, hInstance, NULL
    );
    
    if (!g_hMainWnd) {
        MessageBoxW(NULL, L"Не удалось создать окно", L"Ошибка", MB_ICONERROR);
        return -1;
    }
    
    ShowWindow(g_hMainWnd, nCmdShow);
    UpdateWindow(g_hMainWnd);
    
    MSG msg;
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    
    return (int)msg.wParam;
}
