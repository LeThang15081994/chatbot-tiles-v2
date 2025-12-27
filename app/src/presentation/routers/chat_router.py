"""
Chat Router
Handles chat-related WebSocket endpoints
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from dependency_injector.wiring import inject, Provide

from app.src.presentation.controllers import ChatController
from app.src.application.dto.chat_dto import WSChatMessageDTO
from app.src.bootstrap.container import Container


router = APIRouter(prefix="/v1/chat", tags=["Chat"])


@router.websocket("/completions")
async def websocket_chat(
    websocket: WebSocket,
):
    """
    WebSocket endpoint for chat (supports both streaming and non-streaming)

    Protocol:
    - Client sends: WSChatMessage with "stream": true/false
    - Server sends:
      * Streaming mode (stream=true): START -> SOURCES -> CHUNK* -> END
      * Non-streaming mode (stream=false): START -> SOURCES -> RESPONSE -> END

    Examples:
    - Streaming: {"type": "chat", "query": "...", "stream": true}
    - Non-streaming: {"type": "chat", "query": "...", "stream": false}
    """
    await websocket.accept()

    # Get controller from container (using DI)
    from app.src.bootstrap.container import Container
    container = Container()
    controller = container.chat_controller()

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            # Parse message
            try:
                message = WSChatMessageDTO(**data)
            except Exception as e:
                # Send error for invalid message
                await websocket.send_json({
                    "type": "error",
                    "error": "ValidationError",
                    "message": "Invalid message format",
                    "detail": str(e),
                })
                continue

            # Handle PING
            if message.type == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "message": "pong",
                })
                continue

            # Handle CHAT
            if message.type == "chat":
                try:
                    # Use unified method that handles both streaming and non-streaming
                    async for response_chunk in controller.chat_websocket(message.model_dump()):
                        await websocket.send_json(response_chunk)

                except Exception as e:
                    # Send error
                    await websocket.send_json({
                        "type": "error",
                        "error": "ChatError",
                        "message": "Chat processing failed",
                        "detail": str(e),
                    })

    except WebSocketDisconnect:
        print("WebSocket disconnected")

    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "error": "InternalError",
                "message": "Unexpected error",
                "detail": str(e),
            })
        except:
            pass

    finally:
        await websocket.close()


@router.get("/history/{user_id}/{session_id}")
@inject
async def get_conversation_history(
    user_id: str,
    session_id: str,
    controller: ChatController = Depends(Provide[Container.chat_controller]),
):
    """
    Get conversation history

    Args:
        user_id: User identifier
        session_id: Session identifier
        controller: Chat controller (injected)

    Returns:
        Conversation history
    """
    try:
        history = await controller.get_conversation_history(user_id, session_id)
        return {"user_id": user_id, "session_id": session_id, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{user_id}/{session_id}")
@inject
async def clear_conversation_history(
    user_id: str,
    session_id: str,
    controller: ChatController = Depends(Provide[Container.chat_controller]),
):
    """
    Clear conversation history

    Args:
        user_id: User identifier
        session_id: Session identifier
        controller: Chat controller (injected)

    Returns:
        Success message
    """
    try:
        success = await controller.clear_conversation(user_id, session_id)
        if success:
            return {"message": "Conversation history cleared successfully"}
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
