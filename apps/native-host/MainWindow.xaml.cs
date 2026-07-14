// MainWindow.xaml.cs
// .NET 9 WPF Host bridging WebView2, Win32 transparent overlay, and WebSocket AI pipeline
using System.Text.Json;
using System.Windows;
using Microsoft.Web.WebView2.Core;
using DesktopCompanion.NativeInterop;
using DesktopCompanion.Services;

namespace DesktopCompanion;

public partial class MainWindow : Window
{
    private WebViewBridge? _bridge;
    private readonly AIWebSocketClient _wsClient = new("ws://localhost:8000/ws");
    private readonly GpuScreenCapture _capture = new();

    public MainWindow()
    {
        InitializeComponent();
        Loaded += OnLoaded;
        Closing += OnClosing;
    }

    private async void OnLoaded(object sender, RoutedEventArgs e)
    {
        // Anchor the widget to the bottom-right corner of the work area instead
        // of covering the whole screen — this is what keeps the rest of the
        // desktop clickable while the companion is running.
        var workArea = SystemParameters.WorkArea;
        Left = workArea.Right - Width - 20;
        Top = workArea.Bottom - Height - 20;

        // Configure Win32 TOPMOST & layered transparent styling
        WindowManagement.ConfigureOverlay(this);

        // Initialize WebView2
        await WebView.EnsureCoreWebView2Async(null);
        _bridge = new WebViewBridge(WebView.CoreWebView2);
        _wsClient.SetBridge(_bridge);

        // Navigate to Vite dev server or production bundle
        WebView.CoreWebView2.Navigate("http://localhost:3000");

        // Subscribe to messages from React UI
        _bridge.Subscribe(async (type, payload) =>
        {
            if (type == "capture_and_ask")
            {
                string prompt = payload.GetProperty("prompt").GetString() ?? "";
                
                // Capture primary screen (downscaled to max 1024px)
                byte[] jpegBytes = _capture.CapturePrimaryScreenJpeg(1024);
                await _bridge!.SendCaptureCompleteAsync();

                // Send over WebSocket to Python Orchestrator
                await _wsClient.SendVisionRequestAsync(prompt, jpegBytes);
            }
            else if (type == "toggle_overlay")
            {
                // Toggle pass-through dynamically if needed
            }
        });

        // Connect to Python backend in background
        _ = _wsClient.ConnectAsync();
    }

    private async void OnClosing(object? sender, System.ComponentModel.CancelEventArgs e)
    {
        await _wsClient.DisposeAsync();
        _capture.Dispose();
    }
}
