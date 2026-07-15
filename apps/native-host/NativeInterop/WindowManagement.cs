// NativeInterop/WindowManagement.cs
// .NET 9 Win32 Transparent Overlay & Click-Through Bridge
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Interop;

namespace DesktopCompanion.NativeInterop;

public static partial class WindowManagement
{
    private const int GWL_EXSTYLE = -20;
    private const int WS_EX_LAYERED = 0x00080000;
    private const int WS_EX_TRANSPARENT = 0x00000020;
    private const int WS_EX_TOOLWINDOW = 0x00000080;

    [LibraryImport("user32.dll", EntryPoint = "GetWindowLongW")]
    private static partial int GetWindowLong(nint hWnd, int nIndex);

    [LibraryImport("user32.dll", EntryPoint = "SetWindowLongW")]
    private static partial int SetWindowLong(nint hWnd, int nIndex, int dwNewLong);

    [LibraryImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static partial bool SetWindowPos(nint hWnd, nint hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);

    [StructLayout(LayoutKind.Sequential)]
    public struct MARGINS
    {
        public int cxLeftWidth;
        public int cxRightWidth;
        public int cyTopHeight;
        public int cyBottomHeight;
    }

    [DllImport("dwmapi.dll")]
    private static extern int DwmExtendFrameIntoClientArea(IntPtr hWnd, ref MARGINS pMarInset);

    private static readonly nint HWND_TOPMOST = new(-1);
    private const uint SWP_NOMOVE = 0x0002;
    private const uint SWP_NOSIZE = 0x0001;
    private const uint SWP_NOACTIVATE = 0x0010;

    /// <summary>
    /// Makes the WPF Window TOPMOST and configures DWM sheet glass transparency
    /// instead of WS_EX_LAYERED so that child WebView2 controls receive mouse events normally.
    /// </summary>
    public static void ConfigureOverlay(Window window)
    {
        var hwnd = new WindowInteropHelper(window).EnsureHandle();

        // 1. Pin to TOPMOST above all other applications
        SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);

        // 2. Set tool window style (hide from Alt+Tab) and ensure WS_EX_LAYERED is stripped
        int exStyle = GetWindowLong(hwnd, GWL_EXSTYLE);
        SetWindowLong(hwnd, GWL_EXSTYLE, (exStyle & ~WS_EX_LAYERED) | WS_EX_TOOLWINDOW);

        // 3. Extend DWM glass frame across entire window (-1 margin = full sheet glass transparency)
        var margins = new MARGINS { cxLeftWidth = -1, cxRightWidth = -1, cyTopHeight = -1, cyBottomHeight = -1 };
        DwmExtendFrameIntoClientArea(hwnd, ref margins);
    }

    /// <summary>
    /// Re-asserts HWND_TOPMOST status without re-running DWM extensions or changing styles.
    /// Used by periodic maintenance timers to keep window above desktop icons.
    /// </summary>
    public static void EnsureTopmost(Window window)
    {
        var hwnd = new WindowInteropHelper(window).EnsureHandle();
        SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
    }
}
