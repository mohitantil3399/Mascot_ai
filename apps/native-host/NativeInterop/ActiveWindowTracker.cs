// NativeInterop/ActiveWindowTracker.cs
// Tracks the currently focused app window bounding box to optimize Vision LLM tokens
using System.Runtime.InteropServices;
using System.Drawing;

namespace DesktopCompanion.NativeInterop;

public static partial class ActiveWindowTracker
{
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT
    {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    [LibraryImport("user32.dll")]
    private static partial nint GetForegroundWindow();

    [LibraryImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static partial bool GetWindowRect(nint hWnd, out RECT lpRect);

    /// <summary>
    /// Returns the bounding rectangle of the currently focused external application window.
    /// Available as an ROI window tracking utility for targeted screen capture cropping modes.
    /// </summary>
    public static Rectangle GetActiveAppBounds()
    {
        nint hwnd = GetForegroundWindow();
        if (hwnd == nint.Zero || !GetWindowRect(hwnd, out RECT rect))
        {
            // Fallback: Primary screen bounds if no foreground window detected
            return new Rectangle(0, 0, 1920, 1080);
        }

        int width = Math.Max(100, rect.Right - rect.Left);
        int height = Math.Max(100, rect.Bottom - rect.Top);
        return new Rectangle(rect.Left, rect.Top, width, height);
    }
}
