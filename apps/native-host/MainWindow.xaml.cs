// MainWindow.xaml.cs
// .NET 9 WPF Host bridging WebView2, Win32 transparent overlay, and WebSocket AI pipeline
using System.Text.Json;
using System.Windows;
using System.Windows.Interop;
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

    protected override void OnSourceInitialized(EventArgs e)
    {
        base.OnSourceInitialized(e);
        var source = PresentationSource.FromVisual(this) as HwndSource;
        source?.AddHook(WndProc);
    }

    private IntPtr WndProc(IntPtr hwnd, int msg, IntPtr wParam, IntPtr lParam, ref bool handled)
    {
        const int WM_NCHITTEST = 0x0084;
        const int HTTRANSPARENT = -1;
        const int HTCLIENT = 1;

        if (msg == WM_NCHITTEST)
        {
            try
            {
                int screenX = (short)(lParam.ToInt64() & 0xFFFF);
                int screenY = (short)((lParam.ToInt64() >> 16) & 0xFFFF);
                System.Windows.Point pt = PointFromScreen(new System.Windows.Point(screenX, screenY));

                bool inStatusPill = pt.X >= 360 && pt.Y <= 80;
                bool inPetContainer = pt.X >= 30 && pt.X <= 320 && pt.Y >= 300 && pt.Y <= 560;
                bool inChatPanel = pt.X >= 270 && pt.X <= 630 && pt.Y >= 30 && pt.Y <= 560;

                if (inStatusPill || inPetContainer || inChatPanel)
                {
                    handled = true;
                    return new IntPtr(HTCLIENT);
                }
                else
                {
                    handled = true;
                    return new IntPtr(HTTRANSPARENT);
                }
            }
            catch
            {
                // Fallback to client click if coordinates fail to convert
            }
        }
        return IntPtr.Zero;
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

        WebView.CoreWebView2.NavigationCompleted += async (_, _) =>
        {
            if (_bridge != null)
            {
                await _bridge.SendStatusAsync(_wsClient.IsConnected ? "connected" : "connecting");
            }
        };

        // Subscribe to messages from React UI
        _bridge.Subscribe(async (type, payload) =>
        {
            if (type == "get_status")
            {
                await _bridge!.SendStatusAsync(_wsClient.IsConnected ? "connected" : "connecting");
            }
            else if (type == "capture_and_ask")
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
