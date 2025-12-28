"""
Search Nodes

Nodes for executing search operations using LangChain StructuredTool.
"""
import json
import logging
from typing import Dict, Any, Optional, TYPE_CHECKING

from app.src.application.dto.chat_dto import ChatMessageDTO
from app.src.application.dto.search_dto import SearchResultDTO
from app.src.application.use_cases.rag_orchestration.state import GraphState
from app.src.application.use_cases.error_handle_use_cases import (
    ToolExecutionError,
    SearchError
)

if TYPE_CHECKING:
    from langchain_core.tools import StructuredTool
    from app.src.domain.services.context_builder import ContextBuilderService
    from langfuse.langchain import CallbackHandler

logger = logging.getLogger(__name__)

# LangChain StructuredTool import
try:
    from langchain_core.tools import StructuredTool
except ImportError:
    StructuredTool = None


async def search_company_node(
    state: GraphState,
    structured_tools: Dict[str, "StructuredTool"],  # LangChain StructuredTool dict (injected)
    context_builder: "ContextBuilderService",  # ContextBuilderService (injected)
    langfuse_handler: Optional["CallbackHandler"] = None  # Langfuse CallbackHandler (injected)
) -> Dict[str, Any]:
    """
    Execute company info search using LangChain StructuredTool

    RESPONSIBILITY:
    - Calls LangChain StructuredTool (search_company_info)
    - Converts JSON tool result to SearchResultDTO
    - Formats results using ContextBuilderService
    - No business logic, just orchestration

    ARCHITECTURE:
    - Uses LangChain StructuredTool for tool execution
    - Tool execution is traced via Langfuse handler
    - All business logic remains in StructuredTool implementation

    EMBEDDING NOTE:
    - This node MAY indirectly trigger embeddings
    - StructuredTool → SearchUseCase → VectorStore → may use embeddings
    - But embeddings are handled by existing services, not this node

    Args:
        state: Current graph state
        structured_tools: Dict of LangChain StructuredTool instances (injected)
        context_builder: Context builder service (injected)
        langfuse_handler: Langfuse callback handler for tracing (injected)

    Returns:
        Updated state with search results
    """
    # Get StructuredTool from dict
    tool = structured_tools.get("search_company_info")
    if not tool:
        logger.warning("search_company_info tool not available")
        return {
            "search_results": [],
            "products_metadata": [],
            "intent": "company_info"
        }

    # Execute via StructuredTool (has validation + Langfuse tracing)
    config = {}
    if langfuse_handler:
        config["callbacks"] = [langfuse_handler]

    query_preview = state["query"][:100] if len(state["query"]) > 100 else state["query"]
    logger.debug(f"Executing company search: query='{query_preview}'")

    try:
        tool_result_json = await tool.ainvoke(
            {"query": state["query"], "top_k": 5},
            config=config
        )
        logger.debug(f"Company search completed: response_length={len(tool_result_json)}")
    except Exception as e:
        # Tool execution failed
        logger.error(
            "Company search tool execution failed",
            exc_info=True,
            extra={
                "error_type": type(e).__name__,
                "tool_name": "search_company_info",
                "query_preview": query_preview
            }
        )
        # Fallback on error
        tool_result_json = json.dumps({
            "error": f"Tool execution failed: {str(e)}",
            "total_results": 0,
            "results": []
        }, ensure_ascii=False)

    # Parse JSON result and convert to SearchResultDTO
    try:
        tool_result = json.loads(tool_result_json)
        results_data = tool_result.get("results", [])

        # Convert to SearchResultDTO list
        search_results = []
        for result_data in results_data:
            # Create SearchResultDTO from tool result
            from app.src.domain.value_objects.query import QueryMetadata
            metadata = QueryMetadata(
                source=result_data.get("metadata", {}).get("source"),
                category=result_data.get("metadata", {}).get("category")
            )
            search_result = SearchResultDTO(
                content=result_data.get("content", ""),
                score=result_data.get("score", 0.0),
                metadata=metadata
            )
            search_results.append(search_result)

        products_metadata = []  # Company info doesn't have products

    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse company search tool result JSON",
            exc_info=True,
            extra={
                "error_type": "JSONDecodeError",
                "tool_name": "search_company_info",
                "query_preview": query_preview
            }
        )
        search_results = []
        products_metadata = []
    except (KeyError, Exception) as e:
        logger.error(
            "Error processing company search results",
            exc_info=True,
            extra={
                "error_type": type(e).__name__,
                "tool_name": "search_company_info",
                "query_preview": query_preview
            }
        )
        search_results = []
        products_metadata = []

    # Format results using ContextBuilderService
    if context_builder and search_results:
        formatted_results = [
            {
                "content": result.content,
                "score": result.score,
                "metadata": result.metadata.model_dump() if hasattr(result.metadata, 'model_dump') else result.metadata.dict()
            }
            for result in search_results
        ]
        formatted_tool_result_json = context_builder.format_tool_results(
            search_results=formatted_results,
            max_content_length=500
        )
    else:
        # Fallback formatting
        formatted_tool_result_json = tool_result_json

    # Return partial state update
    return {
        "search_results": search_results,
        "products_metadata": products_metadata,
        "intent": "company_info",
        "messages": state.get("messages", []) + [
            ChatMessageDTO(
                role="tool",
                content=formatted_tool_result_json,
                metadata={"tool_call_id": "search_company_info"}
            )
        ]
    }


async def search_collection_node(
    state: GraphState,
    structured_tools: Dict[str, "StructuredTool"],  # LangChain StructuredTool dict (injected)
    context_builder: "ContextBuilderService",  # ContextBuilderService (injected)
    langfuse_handler: Optional["CallbackHandler"] = None  # Langfuse CallbackHandler (injected)
) -> Dict[str, Any]:
    """
    Execute collection info search using LangChain StructuredTool

    RESPONSIBILITY:
    - Calls LangChain StructuredTool (search_collection_info)
    - Converts JSON tool result to SearchResultDTO
    - Formats results using ContextBuilderService

    ARCHITECTURE:
    - Uses LangChain StructuredTool for tool execution
    - Tool execution is traced via Langfuse handler

    EMBEDDING NOTE:
    - This node MAY indirectly trigger embeddings (via tool execution)

    Args:
        state: Current graph state
        structured_tools: Dict of LangChain StructuredTool instances (injected)
        context_builder: Context builder service (injected)
        langfuse_handler: Langfuse callback handler for tracing (injected)

    Returns:
        Updated state with search results
    """
    # Get StructuredTool from dict
    tool = structured_tools.get("search_collection_info")
    if not tool:
        logger.warning("search_collection_info tool not available")
        return {
            "search_results": [],
            "products_metadata": [],
            "intent": "collection_info"
        }

    # Execute via StructuredTool
    config = {}
    if langfuse_handler:
        config["callbacks"] = [langfuse_handler]

    query_preview = state["query"][:100] if len(state["query"]) > 100 else state["query"]
    logger.debug(f"Executing collection search: query='{query_preview}'")

    try:
        tool_result_json = await tool.ainvoke(
            {"query": state["query"], "top_k": 5},
            config=config
        )
        logger.debug(f"Collection search completed: response_length={len(tool_result_json)}")
    except Exception as e:
        logger.error(
            "Collection search tool execution failed",
            exc_info=True,
            extra={
                "error_type": type(e).__name__,
                "tool_name": "search_collection_info",
                "query_preview": query_preview
            }
        )
        tool_result_json = json.dumps({
            "error": f"Tool execution failed: {str(e)}",
            "total_results": 0,
            "results": []
        }, ensure_ascii=False)

    # Parse JSON result and convert to SearchResultDTO
    try:
        tool_result = json.loads(tool_result_json)
        results_data = tool_result.get("results", [])

        search_results = []
        for result_data in results_data:
            from app.src.domain.value_objects.query import QueryMetadata
            metadata = QueryMetadata(
                source=result_data.get("metadata", {}).get("source"),
                category=result_data.get("metadata", {}).get("category")
            )
            search_result = SearchResultDTO(
                content=result_data.get("content", ""),
                score=result_data.get("score", 0.0),
                metadata=metadata
            )
            search_results.append(search_result)

        products_metadata = []

    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse collection search tool result JSON",
            exc_info=True,
            extra={
                "error_type": "JSONDecodeError",
                "tool_name": "search_collection_info",
                "query_preview": query_preview
            }
        )
        search_results = []
        products_metadata = []
    except (KeyError, Exception) as e:
        logger.error(
            "Error processing collection search results",
            exc_info=True,
            extra={
                "error_type": type(e).__name__,
                "tool_name": "search_collection_info",
                "query_preview": query_preview
            }
        )
        search_results = []
        products_metadata = []

    # Format results
    if context_builder and search_results:
        formatted_results = [
            {
                "content": result.content,
                "score": result.score,
                "metadata": result.metadata.model_dump() if hasattr(result.metadata, 'model_dump') else result.metadata.dict()
            }
            for result in search_results
        ]
        formatted_tool_result_json = context_builder.format_tool_results(
            search_results=formatted_results,
            max_content_length=500
        )
    else:
        formatted_tool_result_json = tool_result_json

    # Return partial state update
    return {
        "search_results": search_results,
        "products_metadata": products_metadata,
        "intent": "collection_info",
        "messages": state.get("messages", []) + [
            ChatMessageDTO(
                role="tool",
                content=formatted_tool_result_json,
                metadata={"tool_call_id": "search_collection_info"}
            )
        ]
    }


async def search_products_node(
    state: GraphState,
    structured_tools: Dict[str, "StructuredTool"],  # LangChain StructuredTool dict (injected)
    context_builder: "ContextBuilderService",  # ContextBuilderService (injected)
    langfuse_handler: Optional["CallbackHandler"] = None  # Langfuse CallbackHandler (injected)
) -> Dict[str, Any]:
    """
    Execute products search using LangChain StructuredTool

    RESPONSIBILITY:
    - Calls LangChain StructuredTool (search_products)
    - Converts JSON tool result to SearchResultDTO
    - Extracts products_metadata from tool result
    - Formats results using ContextBuilderService

    ARCHITECTURE:
    - Uses LangChain StructuredTool for tool execution
    - Tool execution is traced via Langfuse handler

    EMBEDDING NOTE:
    - This node MAY indirectly trigger embeddings (via tool execution)

    Args:
        state: Current graph state
        structured_tools: Dict of LangChain StructuredTool instances (injected)
        context_builder: Context builder service (injected)
        langfuse_handler: Langfuse callback handler for tracing (injected)

    Returns:
        Updated state with search results and products_metadata
    """
    # Get StructuredTool from dict
    tool = structured_tools.get("search_products")
    if not tool:
        logger.warning("search_products tool not available")
        return {
            "search_results": [],
            "products_metadata": [],
            "intent": "products"
        }

    # Execute via StructuredTool
    config = {}
    if langfuse_handler:
        config["callbacks"] = [langfuse_handler]

    query_preview = state["query"][:100] if len(state["query"]) > 100 else state["query"]
    logger.debug(f"Executing products search: query='{query_preview}'")

    try:
        tool_result_json = await tool.ainvoke(
            {"query": state["query"], "top_k": 5},
            config=config
        )
        logger.debug(f"Products search completed: response_length={len(tool_result_json)}")
    except Exception as e:
        logger.error(
            "Products search tool execution failed",
            exc_info=True,
            extra={
                "error_type": type(e).__name__,
                "tool_name": "search_products",
                "query_preview": query_preview
            }
        )
        tool_result_json = json.dumps({
            "error": f"Tool execution failed: {str(e)}",
            "total_results": 0,
            "results": []
        }, ensure_ascii=False)

    # Parse JSON result and convert to SearchResultDTO
    try:
        tool_result = json.loads(tool_result_json)
        results_data = tool_result.get("results", [])

        search_results = []
        products_metadata = []

        for result_data in results_data:
            from app.src.domain.value_objects.query import QueryMetadata
            metadata_dict = result_data.get("metadata", {})
            metadata = QueryMetadata(
                source=metadata_dict.get("source"),
                category=metadata_dict.get("category")
            )
            search_result = SearchResultDTO(
                content=result_data.get("content", ""),
                score=result_data.get("score", 0.0),
                metadata=metadata
            )
            search_results.append(search_result)

            # Extract products_metadata (product_code, collection_name, brand_name)
            if metadata_dict.get("product_code"):
                products_metadata.append({
                    "product_code": metadata_dict.get("product_code"),
                    "collection_name": metadata_dict.get("collection_name"),
                    "brand_name": metadata_dict.get("brand_name")
                })

    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse products search tool result JSON",
            exc_info=True,
            extra={
                "error_type": "JSONDecodeError",
                "tool_name": "search_products",
                "query_preview": query_preview
            }
        )
        search_results = []
        products_metadata = []
    except (KeyError, Exception) as e:
        logger.error(
            "Error processing products search results",
            exc_info=True,
            extra={
                "error_type": type(e).__name__,
                "tool_name": "search_products",
                "query_preview": query_preview
            }
        )
        search_results = []
        products_metadata = []

    # Format results
    if context_builder and search_results:
        formatted_results = [
            {
                "content": result.content,
                "score": result.score,
                "metadata": result.metadata.model_dump() if hasattr(result.metadata, 'model_dump') else result.metadata.dict()
            }
            for result in search_results
        ]
        formatted_tool_result_json = context_builder.format_tool_results(
            search_results=formatted_results,
            max_content_length=500
        )
    else:
        formatted_tool_result_json = tool_result_json

    # Return partial state update
    return {
        "search_results": search_results,
        "products_metadata": products_metadata,
        "intent": "products",
        "messages": state.get("messages", []) + [
            ChatMessageDTO(
                role="tool",
                content=formatted_tool_result_json,
                metadata={"tool_call_id": "search_products"}
            )
        ]
    }

