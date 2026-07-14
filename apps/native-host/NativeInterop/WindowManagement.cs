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

    private static readonly nint HWND_TOPMOST = new(-1);
    private const uint SWP_NOMOVE = 0x0002;
    private const uint SWP_NOSIZE = 0x0001;
    private const uint SWP_NOACTIVATE = 0x0010;

    /// <summary>
    /// Makes the WPF Window TOPMOST and configures transparent click-through
    /// for all areas outside the React UI interactable components.
    /// </summary>
    public static void ConfigureOverlay(Window window)
    {
        var hwnd = new WindowInteropHelper(window).EnsureHandle();

        // 1. Pin to TOPMOST above all other applications
        SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);

        // 2. Set layered tool window styles to hide from Alt+Tab and enable transparency
        int exStyle = GetWindowLong(hwnd, GWL_EXSTYLE);
        SetWindowLong(hwnd, GWL_EXSTYLE, exStyle | WS_EX_LAYERED | WS_EX_TOOLWINDOW);
    }

    /// <summary>
    /// Dynamically toggles click-through pass-through based on mouse coordinates.
    /// Called when the mouse hovers over transparent background vs React UI controls.
    /// </summary>
    public static void SetClickThrough(Window window, bool passThrough)
    {
        var hwnd = new WindowInteropHelper(window).EnsureHandle();
        int exStyle = GetWindowLong(hwnd, GWL_EXSTYLE);

        if (passThrough)
        {
            SetWindowLong(hwnd, GWL_EXSTYLE, exStyle | WS_EX_TRANSPARENT);
        }
        else
        {
            SetWindowLong(hwnd, GWL_EXSTYLE, exStyle & ~WS_EX_TRANSPARENT);
        }
    }
}
