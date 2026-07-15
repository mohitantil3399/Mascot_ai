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
    
    # Persistent chat session history using dictionary format with roles:
    # 'system', 'model_response', and 'User_query' up to 8 continuous message pairs (16 turns).
    session_history: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    active_task: asyncio.Task | None = None
    print(f"[WS] Client connected: {websocket.client}")

    try:
        while True:
            # Step 1: Receive text metadata frame
            raw_meta = await websocket.receive_text()
            try:
                data = json.loads(raw_meta)
            except Exception:
                continue
            msg_type = data.get("type")

            if msg_type in ("start_session", "close_session", "reset_session"):
                if active_task and not active_task.done():
                    active_task.cancel()
                session_history = [{"role": "system", "content": SYSTEM_PROMPT}]
                print(f"[WS] Session event '{msg_type}'. Chat history cleared (system prompt retained).")
                await websocket.send_json({"type": "session_reset", "status": msg_type})

            elif msg_type == "vision_prompt":
                prompt = data.get("prompt", "")
                roi = data.get("roi") # Optional tuple [x, y, w, h]

                # Step 2: Receive binary image frame
                raw_image_bytes = await websocket.receive_bytes()

                # Step 3: Process image via ROI cropping and SSIM/pixel diff check
                processed_bytes, has_changed = preprocessor.process_and_check_diff(
                    raw_image_bytes, 
                    tuple(roi) if roi and len(roi) == 4 else None
                )

                # Append User_query to session history and enforce max 8 continuous pairs (16 user/model turns + 1 system prompt)
                session_history.append({"role": "User_query", "content": prompt})
                if len(session_history) > 17:  # 1 system + 16 continuous user/model messages
                    session_history = [session_history[0]] + session_history[-16:]

                # Cancel any in-progress stream if user sends a new prompt
                if active_task and not active_task.done():
                    active_task.cancel()
                    await websocket.send_json({"type": "stream_cancelled"})

                # Step 4: Stream AI tokens back
                async def stream_response():
                    await websocket.send_json({"type": "stream_start"})
                    if not has_changed and prompt.strip() == "":
                        # Screen hasn't changed and no question asked — save VRAM
                        msg = "[No visual change detected on screen since last capture.]"
                        await websocket.send_json({
                            "type": "token", 
                            "payload": msg
                        })
                        session_history.append({"role": "model_response", "content": msg})
                        if len(session_history) > 17:
                            session_history[:] = [session_history[0]] + session_history[-16:]
                    else:
                        full_ai_response = ""
                        async for token in llm.stream_vision(prompt, processed_bytes, SYSTEM_PROMPT, session_history=session_history):
                            full_ai_response += token
                            await websocket.send_json({"type": "token", "payload": token})
                        if full_ai_response:
                            session_history.append({"role": "model_response", "content": full_ai_response})
                            if len(session_history) > 17:
                                session_history[:] = [session_history[0]] + session_history[-16:]
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

