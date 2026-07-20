// NativeInterop/ScreenCapture.cs
// .NET 9 | Screen Capture Pipeline with GDI+ & GPU-ready fallback
// Self-exclusion: Hides own overlay window during capture to prevent LLM self-detection
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Runtime.InteropServices;

namespace DesktopCompanion.NativeInterop;

public sealed class GpuScreenCapture : IDisposable
{
    public event EventHandler<byte[]>? FrameCaptured;

    // Win32 interop for hiding/showing our own overlay during capture
    [DllImport("user32.dll")]
    private static extern bool SetWindowPos(nint hWnd, nint hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);

    private static readonly nint HWND_TOPMOST = new(-1);
    private const uint SWP_NOMOVE = 0x0002;
    private const uint SWP_NOSIZE = 0x0001;
    private const uint SWP_NOACTIVATE = 0x0010;
    private const uint SWP_HIDEWINDOW = 0x0080;
    private const uint SWP_SHOWWINDOW = 0x0040;

    /// <summary>Handle to our own overlay window — hidden during capture to avoid self-detection.</summary>
    private nint _overlayHwnd = nint.Zero;

    /// <summary>
    /// Registers the overlay window handle so it can be hidden during screen capture.
    /// Call this once from MainWindow.OnLoaded after obtaining the HWND.
    /// </summary>
    public void SetOverlayHandle(nint hwnd) => _overlayHwnd = hwnd;

    public Task InitializeAsync(nint hwnd)
    {
        // Initialized frame capture pool
        return Task.CompletedTask;
    }

    /// <summary>
    /// Captures the primary screen or ROI region directly to JPEG bytes.
    /// Temporarily hides the companion overlay window so it is excluded from the capture.
    /// </summary>
    public byte[] CapturePrimaryScreenJpeg(int maxDimension = 1024)
    {
        // --- Self-exclusion: hide our overlay before capturing ---
        bool didHide = false;
        if (_overlayHwnd != nint.Zero)
        {
            SetWindowPos(_overlayHwnd, HWND_TOPMOST, 0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_HIDEWINDOW);
            didHide = true;
            // Brief pause to let the DWM compositor flush the previous frame
            Thread.Sleep(50);
        }

        var bounds = System.Windows.Forms.Screen.PrimaryScreen?.Bounds ?? new Rectangle(0, 0, 1920, 1080);
        using var bitmap = new Bitmap(bounds.Width, bounds.Height);
        using var g = Graphics.FromImage(bitmap);
        g.CopyFromScreen(bounds.Location, Point.Empty, bounds.Size);

        // --- Self-exclusion: restore our overlay immediately after capture ---
        if (didHide)
        {
            SetWindowPos(_overlayHwnd, HWND_TOPMOST, 0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW);
        }

        // Downscale before sending over WebSocket to save CPU/VRAM
        int newWidth = bounds.Width;
        int newHeight = bounds.Height;
        if (bounds.Width > maxDimension || bounds.Height > maxDimension)
        {
            if (bounds.Width > bounds.Height)
            {
                newWidth = maxDimension;
                newHeight = (int)(bounds.Height * ((float)maxDimension / bounds.Width));
            }
            else
            {
                newHeight = maxDimension;
                newWidth = (int)(bounds.Width * ((float)maxDimension / bounds.Height));
            }
        }

        using var resized = new Bitmap(bitmap, new Size(newWidth, newHeight));
        using var ms = new MemoryStream();
        resized.Save(ms, ImageFormat.Jpeg);
        var bytes = ms.ToArray();
        
        FrameCaptured?.Invoke(this, bytes);
        return bytes;
    }

    public void Dispose()
    {
        // Clean up unmanaged resources if needed
    }
}
