// Services/WebViewBridge.cs
// 2026 Standard: Use typed PostWebMessageAsJson — NOT raw ExecuteScriptAsync string injection
using Microsoft.Web.WebView2.Core;
using System.Text.Json;

namespace DesktopCompanion.Services;

public sealed class WebViewBridge
{
    private readonly CoreWebView2 _webView;

    public WebViewBridge(CoreWebView2 webView) => _webView = webView;

    /// <summary>Dispatch AI token chunk to React as a typed JSON message.</summary>
    public Task DispatchAIChunkAsync(string tokenChunk)
    {
        var msg = JsonSerializer.Serialize(new { type = "ai_chunk", payload = tokenChunk });
        _webView.PostWebMessageAsJson(msg);
        return Task.CompletedTask;
    }

    /// <summary>Dispatch connection status to React.</summary>
    public Task SendStatusAsync(string status)
    {
        var msg = JsonSerializer.Serialize(new { type = "status", payload = status });
        _webView.PostWebMessageAsJson(msg);
        return Task.CompletedTask;
    }

    /// <summary>Dispatch capture complete notification to React.</summary>
    public Task SendCaptureCompleteAsync()
    {
        var msg = JsonSerializer.Serialize(new { type = "capture_complete" });
        _webView.PostWebMessageAsJson(msg);
        return Task.CompletedTask;
    }

    /// <summary>Tell React the current response stream has finished.</summary>
    public Task SendStreamEndAsync()
    {
        var msg = JsonSerializer.Serialize(new { type = "stream_end" });
        _webView.PostWebMessageAsJson(msg);
        return Task.CompletedTask;
    }

    /// <summary>Dispatch an error message to React.</summary>
    public Task SendErrorAsync(string errorMessage)
    {
        var msg = JsonSerializer.Serialize(new { type = "error", payload = errorMessage });
        _webView.PostWebMessageAsJson(msg);
        return Task.CompletedTask;
    }

    /// <summary>Subscribe to messages from React.</summary>
    public void Subscribe(Action<string, JsonElement> handler)
    {
        _webView.WebMessageReceived += (_, e) =>
        {
            try
            {
                string jsonString = e.TryGetWebMessageAsString() ?? e.WebMessageAsJson;
                if (string.IsNullOrEmpty(jsonString)) jsonString = e.WebMessageAsJson;

                var doc = JsonDocument.Parse(jsonString);
                var root = doc.RootElement;
                if (root.ValueKind == JsonValueKind.String)
                {
                    var innerString = root.GetString() ?? "{}";
                    doc = JsonDocument.Parse(innerString);
                    root = doc.RootElement;
                }

                var type = root.TryGetProperty("type", out var prop) ? prop.GetString() ?? "" : "";
                handler(type, root);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[Bridge Error] Failed to parse JSON message: {ex.Message}");
            }
        };
    }
}
