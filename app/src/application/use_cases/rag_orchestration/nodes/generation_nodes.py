"""
Generation Nodes

Nodes for generating final answers using LLM.
"""
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List, TYPE_CHECKING

from app.src.application.dto.chat_dto import ChatMessageDTO
from app.src.application.use_cases.rag_orchestration.state import GraphState

if TYPE_CHECKING:
    from app.src.application.interfaces.services.llm_service_interface import ILLMService
    from app.src.domain.services.prompt_builder import PromptBuilderService
    from langfuse.langchain import CallbackHandler

logger = logging.getLogger(__name__)


async def generate_answer_node(
    state: GraphState,
    llm_service: "ILLMService",
    prompt_builder: "PromptBuilderService",
    chat_history: List[Dict[str, str]],
    langfuse_handler: Optional["CallbackHandler"] = None
) -> Dict[str, Any]:
    """Generate final answer (handles both no-tool and RAG flows)"""
    query_preview = state.get("query", "")[:100] if len(state.get("query", "")) > 100 else state.get("query", "")
    logger.debug(f"Generating answer: query_preview='{query_preview}'")

    action_result = state.get("action_result")
    if action_result:
        logger.debug("Generating action response (add_to_cart confirmation)")
        if prompt_builder:
            from app.src.domain.entities.message import Message, MessageRole

            history_messages = []
            for msg in chat_history:
                role = MessageRole.USER if msg.get("role") == "user" else MessageRole.ASSISTANT
                history_messages.append(Message(role=role, content=msg.get("content", ""), timestamp=None))

            action_prompt = prompt_builder.build_action_response_prompt(
                query=state["query"],
                chat_history=history_messages if history_messages else None
            )

            action_result_json = json.dumps(action_result, ensure_ascii=False)
            final_messages = [
                ChatMessageDTO(role="system", content=action_prompt),
                ChatMessageDTO(role="user", content=state["query"]),
                ChatMessageDTO(role="tool", content=action_result_json, metadata={"tool_call_id": "add_to_cart"})
            ]

            config = {}
            if langfuse_handler:
                config["callbacks"] = [langfuse_handler]

            final_answer = await llm_service.generate_response(
                messages=final_messages,
                temperature=0.7,
                max_tokens=2048,
                **config
            )
        else:
            # Fallback: Simple confirmation message
            if action_result.get("success", False):
                final_answer = f"I've added the product to your cart. {json.dumps(action_result, ensure_ascii=False)}"
            else:
                final_answer = f"I couldn't add the product to your cart. {action_result.get('error', 'Unknown error')}"

        return {"final_answer": final_answer}

    has_search_results = bool(state.get("search_results"))
    intent = state.get("intent")

    if has_search_results and intent:
        logger.debug(f"Generating RAG answer: intent={intent}, results_count={len(state.get('search_results', []))}")
        from app.src.domain.value_objects.context import RAGContext
        from app.src.domain.entities.document import Document
        from app.src.domain.entities.message import Message, MessageRole

        domain_documents = []
        for result in state["search_results"]:
            doc = Document(
                content=result.content,
                source=result.metadata.get("source", "") if hasattr(result.metadata, 'get') else (result.metadata.model_dump().get("source", "") if hasattr(result.metadata, 'model_dump') else ""),
                relevance_score=result.score,
                metadata=result.metadata.model_dump() if hasattr(result.metadata, 'model_dump') else result.metadata.dict()
            )
            domain_documents.append(doc)

        rag_context = RAGContext(documents=domain_documents)

        history_messages = []
        for msg in chat_history:
            role = MessageRole.USER if msg.get("role") == "user" else MessageRole.ASSISTANT
            history_messages.append(Message(role=role, content=msg.get("content", ""), timestamp=None))

        rag_prompt = prompt_builder.build_rag_prompt(
            query=state["query"],
            context=rag_context,
            chat_history=history_messages if history_messages else None,
            intent=intent
        )

        final_messages = [ChatMessageDTO(role="system", content=rag_prompt)]
    else:
        logger.debug("Generating direct answer (no search results)")
        messages = state.get("messages", [])
        if not messages:
            messages = state.get("initial_messages", [])
        final_messages = messages

    config = {}
    if langfuse_handler:
        config["callbacks"] = [langfuse_handler]

    try:
        final_answer = await llm_service.generate_response(
            messages=final_messages,
            temperature=0.7,
            max_tokens=2048,
            **config
        )

        answer_preview = final_answer[:100] if len(final_answer) > 100 else final_answer
        logger.debug(f"Answer generated: preview='{answer_preview}', length={len(final_answer)}")
    except Exception as e:
        logger.error("Failed to generate answer", exc_info=True, extra={"error_type": type(e).__name__, "generation_type": "rag" if has_search_results else "direct", "query_preview": query_preview})
        final_answer = "I apologize, but I encountered an error while generating a response. Please try again."

    return {"final_answer": final_answer}


async def generate_answer_streaming_node(
    state: GraphState,
    llm_service: "ILLMService",
    prompt_builder: "PromptBuilderService",
    chat_history: List[Dict[str, str]],
    streaming_queue: Optional[asyncio.Queue] = None,
    langfuse_handler: Optional["CallbackHandler"] = None
) -> Dict[str, Any]:
    """Generate final answer with real-time streaming support"""
    query_preview = state.get("query", "")[:100] if len(state.get("query", "")) > 100 else state.get("query", "")
    logger.debug(f"Generating streaming answer: query_preview='{query_preview}'")

    action_result = state.get("action_result")
    if action_result:
        logger.debug("Generating action response (add_to_cart confirmation)")
        if prompt_builder:
            from app.src.domain.entities.message import Message, MessageRole

            history_messages = []
            for msg in chat_history:
                role = MessageRole.USER if msg.get("role") == "user" else MessageRole.ASSISTANT
                history_messages.append(Message(role=role, content=msg.get("content", ""), timestamp=None))

            action_prompt = prompt_builder.build_action_response_prompt(
                query=state["query"],
                chat_history=history_messages if history_messages else None
            )

            action_result_json = json.dumps(action_result, ensure_ascii=False)
            final_messages = [
                ChatMessageDTO(role="system", content=action_prompt),
                ChatMessageDTO(role="user", content=state["query"]),
                ChatMessageDTO(role="tool", content=action_result_json, metadata={"tool_call_id": "add_to_cart"})
            ]

            streaming_chunks = []
            full_response = ""
            async for chunk in llm_service.stream_response(messages=final_messages, temperature=0.7, max_tokens=2048):
                if chunk and isinstance(chunk, str) and chunk.strip():
                    streaming_chunks.append(chunk)
                    full_response += chunk
                    if streaming_queue:
                        try:
                            await streaming_queue.put(chunk)
                        except Exception as e:
                            logger.warning(f"Failed to stream chunk to queue: {e}")

            if streaming_queue:
                try:
                    await streaming_queue.put(None)
                except Exception:
                    pass

            return {
                "final_answer": full_response,
                "streaming_chunks": streaming_chunks,
                "streaming_complete": True
            }
        else:
            # Fallback: Simple confirmation message
            if action_result.get("success", False):
                final_answer = f"I've added the product to your cart. {json.dumps(action_result, ensure_ascii=False)}"
            else:
                final_answer = f"I couldn't add the product to your cart. {action_result.get('error', 'Unknown error')}"
            return {
                "final_answer": final_answer,
                "streaming_chunks": [final_answer],
                "streaming_complete": True
            }

    has_search_results = bool(state.get("search_results"))
    intent = state.get("intent")

    if has_search_results and intent:
        logger.debug(f"Generating RAG streaming answer: intent={intent}, results_count={len(state.get('search_results', []))}")
        from app.src.domain.value_objects.context import RAGContext
        from app.src.domain.entities.document import Document
        from app.src.domain.entities.message import Message, MessageRole

        domain_documents = []
        for result in state["search_results"]:
            doc = Document(
                content=result.content,
                source=result.metadata.get("source", "") if hasattr(result.metadata, 'get') else (result.metadata.model_dump().get("source", "") if hasattr(result.metadata, 'model_dump') else ""),
                relevance_score=result.score,
                metadata=result.metadata.model_dump() if hasattr(result.metadata, 'model_dump') else result.metadata.dict()
            )
            domain_documents.append(doc)

        rag_context = RAGContext(documents=domain_documents)

        history_messages = []
        for msg in chat_history:
            role = MessageRole.USER if msg.get("role") == "user" else MessageRole.ASSISTANT
            history_messages.append(Message(role=role, content=msg.get("content", ""), timestamp=None))

        rag_prompt = prompt_builder.build_rag_prompt(
            query=state["query"],
            context=rag_context,
            chat_history=history_messages if history_messages else None,
            intent=intent
        )

        final_messages = [ChatMessageDTO(role="system", content=rag_prompt)]
    else:
        logger.debug("Generating direct streaming answer (no search results)")
        messages = state.get("messages", [])
        if not messages:
            messages = state.get("initial_messages", [])
        final_messages = messages

    streaming_chunks = []
    full_response = ""
    try:
        async for chunk in llm_service.stream_response(messages=final_messages, temperature=0.7, max_tokens=2048):
            if chunk and isinstance(chunk, str) and chunk.strip():
                streaming_chunks.append(chunk)
                full_response += chunk
                if streaming_queue:
                    try:
                        await streaming_queue.put(chunk)
                    except Exception as e:
                        logger.warning(f"Failed to stream chunk to queue: {e}", extra={"query_preview": query_preview})

        if not full_response or not full_response.strip():
            logger.warning("Empty response from LLM streaming", extra={"generation_type": "rag" if has_search_results else "direct", "query_preview": query_preview})
            full_response = "I apologize, but I couldn't generate a response. Please try again."
            streaming_chunks = [full_response] if not streaming_chunks else streaming_chunks
            if streaming_queue:
                try:
                    await streaming_queue.put(full_response)
                except Exception:
                    pass

        answer_preview = full_response[:100] if len(full_response) > 100 else full_response
        logger.debug(f"Streaming answer generated: preview='{answer_preview}', length={len(full_response)}, chunks_count={len(streaming_chunks)}")
    except Exception as e:
        logger.error("Failed to generate streaming answer", exc_info=True, extra={"error_type": type(e).__name__, "generation_type": "rag" if has_search_results else "direct", "query_preview": query_preview})
        full_response = "I apologize, but I encountered an error while generating a response. Please try again."
        streaming_chunks = [full_response] if not streaming_chunks else streaming_chunks
        if streaming_queue:
            try:
                await streaming_queue.put(full_response)
            except Exception:
                pass

    if streaming_queue:
        try:
            await streaming_queue.put(None)
        except Exception:
            pass

    if not streaming_chunks:
        streaming_chunks = [full_response] if full_response else []

    return {
        "final_answer": full_response,
        "streaming_chunks": streaming_chunks,
        "streaming_complete": True
    }