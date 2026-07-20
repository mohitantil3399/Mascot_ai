// MainWindow.xaml.cs
// .NET 9 WPF Host bridging WebView2, Win32 transparent overlay, and WebSocket AI pipeline
using System;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Windows;
using System.Windows.Interop;
using System.Windows.Media;
using Microsoft.Web.WebView2.Core;
using DesktopCompanion.NativeInterop;
using DesktopCompanion.Services;

namespace DesktopCompanion;

public partial class MainWindow : Window
{
    private IntPtr _hwnd;
    private double _dpiScaleX = 1.0;
    private double _dpiScaleY = 1.0;

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
        _hwnd = new WindowInteropHelper(this).EnsureHandle();
        
        // Register our overlay handle with the capture service so it can hide us during screenshots
        _capture.SetOverlayHandle(_hwnd);
        // Get DPI scale for accurate physical pixel conversion
        var dpi = VisualTreeHelper.GetDpi(this);
        _dpiScaleX = dpi.DpiScaleX;
        _dpiScaleY = dpi.DpiScaleY;

        // Configure compact overlay window anchored to bottom-right corner.
        var workArea = SystemParameters.WorkArea;
        Width = 200;
        Height = 220;
        Left = workArea.Right - Width - 20;
        Top = workArea.Bottom - Height - 20;

        // Configure Win32 TOPMOST & layered transparent styling
        WindowManagement.ConfigureOverlay(this);

        // Periodic maintenance timer to guarantee TOPMOST z-order even if Windows demotes it
        var topmostTimer = new System.Windows.Threading.DispatcherTimer
        {
            Interval = TimeSpan.FromSeconds(3)
        };
        topmostTimer.Tick += (s, args) =>
        {
            if (_hwnd != IntPtr.Zero)
            {
                WindowManagement.EnsureTopmost(this);
            }
        };
        topmostTimer.Start();

        // Initialize WebView2
        await WebView.EnsureCoreWebView2Async(null);
        _bridge = new WebViewBridge(WebView.CoreWebView2);
        _wsClient.SetBridge(_bridge);


        // Navigate to Vite dev server or production bundle
        WebView.CoreWebView2.Navigate("http://localhost:3000");

        WebView.CoreWebView2.NavigationCompleted += async (_, e) =>
        {
            if (!e.IsSuccess)
            {
                Console.WriteLine($"[WebView2] Navigation failed ({e.WebErrorStatus}). Retrying in 2 seconds...");
                await Task.Delay(2000);
                WebView.CoreWebView2.Navigate("http://localhost:3000");
                return;
            }


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
                byte[] jpegBytes = _capture.CapturePrimaryScreenJpeg(1024);
                await _bridge!.SendCaptureCompleteAsync();
                await _wsClient.SendVisionRequestAsync(prompt, jpegBytes);
            }
            else if (type == "send_prompt")
            {
                string prompt = payload.GetProperty("prompt").GetString() ?? "";
                await _wsClient.SendTextMessageAsync(JsonSerializer.Serialize(new { type, prompt }));
            }
            else if (type == "set_chat_open")
            {
                if (payload.TryGetProperty("isOpen", out var prop) && (prop.ValueKind == JsonValueKind.True || prop.ValueKind == JsonValueKind.False))
                {
                    bool isOpen = prop.GetBoolean();
                    Dispatcher.Invoke(() => ResizeTo(isOpen));
                }
            }
            else if (type == "update_regions")
            {
                if (payload.TryGetProperty("regions", out var regions))
                {
                    bool isChatOpen = regions.TryGetProperty("chatRect", out var cr) && cr.ValueKind == JsonValueKind.Array && cr.GetArrayLength() == 4;
                    Dispatcher.Invoke(() => ResizeTo(isChatOpen));
                }
            }
            else if (type == "move_window")
            {
                if (payload.TryGetProperty("dx", out var dxProp) && payload.TryGetProperty("dy", out var dyProp))
                {
                    double dx = dxProp.GetDouble();
                    double dy = dyProp.GetDouble();
                    Dispatcher.Invoke(() =>
                    {
                        Left += dx;
                        Top += dy;
                    });
                }
            }
            else if (type == "start_session" || type == "close_session" || type == "reset_session")
            {
                await _wsClient.SendTextMessageAsync(JsonSerializer.Serialize(new { type }));
            }
            else if (type == "toggle_overlay")
            {
                // Toggle pass-through dynamically if needed
            }
        });

        // Connect to Python backend in background
        _ = _wsClient.ConnectAsync();
    }

    private void ResizeTo(bool isChatOpen)
    {
        if (!Dispatcher.CheckAccess())
        {
            Dispatcher.Invoke(() => ResizeTo(isChatOpen));
            return;
        }

        var workArea = SystemParameters.WorkArea;
        if (isChatOpen)
        {
            Width = 660;
            Height = 560;
        }
        else
        {
            Width = 200;
            Height = 220;
        }

        if (Left + Width > workArea.Right)
        {
            Left = Math.Max(workArea.Left, workArea.Right - Width - 10);
        }
        if (Top + Height > workArea.Bottom)
        {
            Top = Math.Max(workArea.Top, workArea.Bottom - Height - 10);
        }
    }

    private async void OnClosing(object? sender, System.ComponentModel.CancelEventArgs e)
    {
        await _wsClient.DisposeAsync();
        _capture.Dispose();
    }
}

