# api/ws_endpoint.py
# Binary frame protocol: Text JSON metadata -> Binary JPEG -> Text token stream
import json
import asyncio

from fastapi import WebSocket, WebSocketDisconnect
from inference.engine import LocalLLM
from inference.vision_parser import VisionPreprocessor
from inference.prompts import SYSTEM_PROMPT

async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    llm = LocalLLM()
    preprocessor = VisionPreprocessor(max_dimension=1024, diff_threshold=0.03)
    
    active_task: asyncio.Task | None = None
    print(f"[WS] Client connected: {websocket.client}")

    try:
        while True:
            # Step 1: Receive text metadata frame
            raw_meta = await websocket.receive_text()
            data = json.loads(raw_meta)
            msg_type = data.get("type")

            if msg_type == "vision_prompt":
                prompt = data.get("prompt", "")
                roi = data.get("roi") # Optional tuple [x, y, w, h]

                # Step 2: Receive binary image frame
                raw_image_bytes = await websocket.receive_bytes()

                # Step 3: Process image via ROI cropping and SSIM/pixel diff check
                processed_bytes, has_changed = preprocessor.process_and_check_diff(
                    raw_image_bytes, 
                    tuple(roi) if roi and len(roi) == 4 else None
                )

                # Cancel any in-progress stream if user sends a new prompt
                if active_task and not active_task.done():
                    active_task.cancel()
                    await websocket.send_json({"type": "stream_cancelled"})

                # Step 4: Stream AI tokens back
                async def stream_response():
                    await websocket.send_json({"type": "stream_start"})
                    if not has_changed and prompt.strip() == "":
                        # Screen hasn't changed and no question asked — save VRAM
                        await websocket.send_json({
                            "type": "token", 
                            "payload": "[No visual change detected on screen since last capture.]"
                        })
                    else:
                        async for token in llm.stream_vision(prompt, processed_bytes, SYSTEM_PROMPT):
                            await websocket.send_json({"type": "token", "payload": token})
                    await websocket.send_json({"type": "stream_end"})

                active_task = asyncio.create_task(stream_response())

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif msg_type == "cancel_stream":
                if active_task and not active_task.done():
                    active_task.cancel()
                    await websocket.send_json({"type": "stream_cancelled"})

    except WebSocketDisconnect:
        print(f"[WS] Client disconnected.")
        if active_task:
            active_task.cancel()
    except Exception as e:
        print(f"[WS] Unhandled error: {e}")
        try:
            await websocket.send_json({"type": "error", "payload": str(e)})
        except:
            pass
