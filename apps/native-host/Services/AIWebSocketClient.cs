// Services/AIWebSocketClient.cs
// Persistent WS connection with exponential backoff reconnect
using System.Net.WebSockets;
using System.Text;
using System.Text.Json;
using System.IO;

namespace DesktopCompanion.Services;

public sealed class AIWebSocketClient : IAsyncDisposable
{
    private ClientWebSocket _ws = new();
    private readonly string _uri;
    private readonly CancellationTokenSource _cts = new();
    private int _reconnectAttempts = 0;
    private WebViewBridge? _bridge;

    public AIWebSocketClient(string uri = "ws://localhost:8000/ws")
    {
        _uri = uri;
    }

    public bool IsConnected => _ws.State == WebSocketState.Open;

    public void SetBridge(WebViewBridge bridge)
    {
        _bridge = bridge;
    }

    /// <summary>Connect with exponential backoff fallback.</summary>
    public async Task ConnectAsync()
    {
        while (!_cts.IsCancellationRequested)
        {
            try
            {
                _ws = new ClientWebSocket();
                await _ws.ConnectAsync(new Uri(_uri), _cts.Token);
                _reconnectAttempts = 0;
                Console.WriteLine("[WS] Connected to AI Orchestrator.");
                if (_bridge != null) await _bridge.SendStatusAsync("connected");
                await ListenAsync();
            }
            catch (Exception ex)
            {
                _reconnectAttempts++;
                var delay = TimeSpan.FromSeconds(Math.Min(Math.Pow(2, _reconnectAttempts), 15));
                Console.WriteLine($"[WS] Disconnected: {ex.Message}. Retrying in {delay.TotalSeconds}s...");
                
                if (_bridge != null) await _bridge.SendStatusAsync("reconnecting");
                await Task.Delay(delay, _cts.Token);
            }
        }
    }

    /// <summary>Send vision prompt — metadata frame + binary image frame.</summary>
    public async Task SendVisionRequestAsync(string prompt, byte[] imageBytes)
    {
        if (_ws.State != WebSocketState.Open)
        {
            Console.WriteLine("[WS] Not connected. Vision request dropped.");
            return;
        }

        // Frame 1: JSON metadata
        var meta = JsonSerializer.SerializeToUtf8Bytes(new { type = "vision_prompt", prompt });
        await _ws.SendAsync(meta, WebSocketMessageType.Text, true, _cts.Token);

        // Frame 2: Raw JPEG bytes (binary frame)
        await _ws.SendAsync(imageBytes, WebSocketMessageType.Binary, true, _cts.Token);
    }

    /// <summary>Send text JSON frame over WebSocket.</summary>
    public async Task SendTextMessageAsync(string jsonMessage)
    {
        if (_ws.State != WebSocketState.Open)
        {
            return;
        }

        var bytes = Encoding.UTF8.GetBytes(jsonMessage);
        await _ws.SendAsync(bytes, WebSocketMessageType.Text, true, _cts.Token);
    }

    private async Task ListenAsync()
    {
        var buffer = new byte[16_384];
        while (_ws.State == WebSocketState.Open)
        {
            using var ms = new MemoryStream();
            WebSocketReceiveResult result;
            do
            {
                result = await _ws.ReceiveAsync(buffer, _cts.Token);
                if (result.MessageType == WebSocketMessageType.Close) break;
                ms.Write(buffer, 0, result.Count);
            } while (!result.EndOfMessage);

            if (result.MessageType == WebSocketMessageType.Close) break;

            var rawJson = Encoding.UTF8.GetString(ms.ToArray());
            if (_bridge != null)
            {
                try
                {
                    var doc = JsonDocument.Parse(rawJson);
                    var type = doc.RootElement.GetProperty("type").GetString();
                    switch (type)
                    {
                        case "token":
                            var payload = doc.RootElement.GetProperty("payload").GetString() ?? "";
                            await _bridge.DispatchAIChunkAsync(payload);
                            break;
                        case "stream_end":
                        case "stream_cancelled":
                            await _bridge.SendStreamEndAsync();
                            break;
                        case "session_reset":
                            await _bridge.SendSessionResetAsync();
                            break;
                        case "error":
                            var errPayload = doc.RootElement.TryGetProperty("payload", out var p) ? p.GetString() ?? "Unknown error" : "Unknown error";
                            await _bridge.SendErrorAsync(errPayload);
                            break;
                        // "stream_start" / "pong" require no action
                    }
                }
                catch
                {
                    // If not json, pass as raw text chunk
                    await _bridge.DispatchAIChunkAsync(rawJson);
                }
            }
        }
    }

    public async ValueTask DisposeAsync()
    {
        await _cts.CancelAsync();
        _ws.Dispose();
    }
}
