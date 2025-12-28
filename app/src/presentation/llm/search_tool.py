"""
Search Tools for LLM Function Calling
Uses LangChain StructuredTool to create specialized search tools

This module provides four separate tools:
1. search_company_info - For searching company information
2. search_collection_info - For searching collection information
3. search_products - For searching specific products
4. add_to_cart - For adding products to cart

These tools are placed in Presentation/llm/ as they represent
the "presentation" of search and action capabilities to the LLM.
"""
import json
from typing import Optional, List
from langchain_core.tools import StructuredTool

from app.src.application.use_cases.search_use_case import SearchUseCase
from app.src.application.dto.search_dto import (
    SearchRequestDTO,
    CollectionType,
    CompanyInfoSearchArgsDTO,
    CollectionInfoSearchArgsDTO,
    ProductsSearchArgsDTO,
    AddToCartArgsDTO
)
from app.src.infrastructure.tool.shopping_cart_service import ShoppingCartService


def create_company_info_tool(search_use_case: SearchUseCase) -> StructuredTool:
    """
    Create search_company_info tool using LangChain StructuredTool

    This tool searches in the company_document collection for information about:
    - Company history, mission, vision
    - Company policies and procedures
    - About us information
    - General company documentation

    Args:
        search_use_case: SearchUseCase instance for document retrieval

    Returns:
        StructuredTool instance for search_company_info
    """
    async def search_company_info(
        query: str,
        top_k: int = 5
    ) -> str:
        """
        Search for company information in the company_document collection

        Use this tool when the user asks about:
        - Company information, history, about us
        - Company policies, procedures
        - General company documentation

        Args:
            query: Search query about company information
            top_k: Number of results (1-20)

        Returns:
            JSON string with search results
        """
        try:
            # Create search request for company_document collection
            search_request = SearchRequestDTO(
                query=query,
                top_k=top_k,
                collection_name=CollectionType.COMPANY_DOCUMENT,
                metadata_filter=None
            )

            # Execute search
            search_response = await search_use_case.search_documents(search_request)
            search_results = search_response.results

            # Format results as JSON string for LLM
            formatted_results = []
            for result in search_results:
                formatted_results.append({
                    "content": result.content[:500],  # Truncate for token efficiency
                    "score": result.score,
                    "metadata": {
                        "source": result.metadata.source if hasattr(result.metadata, 'source') else None,
                        "category": result.metadata.category if hasattr(result.metadata, 'category') else None,
                    }
                })

            # Return as JSON string
            return json.dumps({
                "total_results": len(formatted_results),
                "results": formatted_results
            }, ensure_ascii=False)

        except Exception as e:
            return json.dumps({
                "error": f"Search failed: {str(e)}",
                "total_results": 0,
                "results": []
            }, ensure_ascii=False)

    # Create StructuredTool using LangChain
    return StructuredTool.from_function(
        func=search_company_info,
        name="search_company_info",
        description=(
            "Search for company information in the company_document collection. "
            "Use this tool when the user asks about company information, history, about us, "
            "company policies, procedures, or general company documentation. "
            "DO NOT use this tool for product or collection questions."
        ),
        args_schema=CompanyInfoSearchArgsDTO
    )


def create_collection_info_tool(search_use_case: SearchUseCase) -> StructuredTool:
    """
    Create search_collection_info tool using LangChain StructuredTool

    This tool searches in the products collection for collection information:
    - Tile collection descriptions
    - Collection features and characteristics
    - Collection types (Wooden look, Marble look, etc.)

    Args:
        search_use_case: SearchUseCase instance for document retrieval

    Returns:
        StructuredTool instance for search_collection_info
    """
    async def search_collection_info(
        query: str,
        top_k: int = 5
    ) -> str:
        """
        Search for collection information in the products collection

        Use this tool when the user asks about:
        - Tile collections (Wooden look, Marble look, etc.)
        - Collection descriptions and features
        - Collection types and characteristics

        Args:
            query: Search query about tile collections
            top_k: Number of results (1-20)

        Returns:
            JSON string with search results
        """
        try:
            # Create search request for products collection
            # Filter to only get collection info (where collectionName is not empty)
            search_request = SearchRequestDTO(
                query=query,
                top_k=top_k,
                collection_name=CollectionType.PRODUCTS,
                metadata_filter={
                    # Filter for collection info: records where collectionName is not empty
                    # This will be handled in the search use case
                }
            )

            # Execute search
            search_response = await search_use_case.search_documents(search_request)
            search_results = search_response.results

            # Filter results to only include collection info (where collectionName exists)
            filtered_results = []
            for result in search_results:
                metadata_dict = result.metadata.model_dump() if hasattr(result.metadata, 'model_dump') else result.metadata.dict()
                collection_name = metadata_dict.get('collection_name') or metadata_dict.get('collectionName')

                # Only include results that have collectionName (collection info, not specific products)
                if collection_name:
                    filtered_results.append({
                        "content": result.content[:500],  # Truncate for token efficiency
                        "score": result.score,
                        "metadata": {
                            "collection_name": collection_name,
                            "source": metadata_dict.get('source'),
                        }
                    })

            # Return as JSON string
            return json.dumps({
                "total_results": len(filtered_results),
                "results": filtered_results
            }, ensure_ascii=False)

        except Exception as e:
            return json.dumps({
                "error": f"Search failed: {str(e)}",
                "total_results": 0,
                "results": []
            }, ensure_ascii=False)

    # Create StructuredTool using LangChain
    return StructuredTool.from_function(
        func=search_collection_info,
        name="search_collection_info",
        description=(
            "Search for tile collection information in the products collection. "
            "Use this tool when the user asks about tile collections, collection types, "
            "collection descriptions, or collection features (e.g., Wooden look tile, "
            "Marble look tile, Decor tile, etc.). "
            "DO NOT use this tool for company information questions."
        ),
        args_schema=CollectionInfoSearchArgsDTO
    )


def create_products_tool(search_use_case: SearchUseCase) -> StructuredTool:
    """
    Create search_products tool using LangChain StructuredTool

    This tool searches in the products collection for specific products:
    - Product codes, names, descriptions
    - Product specifications and features
    - Individual product information (not collection info)

    Args:
        search_use_case: SearchUseCase instance for document retrieval

    Returns:
        StructuredTool instance for search_products
    """
    async def search_products(
        query: str,
        top_k: int = 5
    ) -> str:
        """
        Search for specific products in the products collection

        Use this tool when the user asks about:
        - Specific product codes or names
        - Product specifications, features, prices
        - Individual product information
        - Product details and descriptions

        Args:
            query: Search query about specific products
            top_k: Number of results (1-20)

        Returns:
            JSON string with search results
        """
        try:
            # Create search request for products collection
            search_request = SearchRequestDTO(
                query=query,
                top_k=top_k,
                collection_name=CollectionType.PRODUCTS,
                metadata_filter=None
            )

            # Execute search
            search_response = await search_use_case.search_documents(search_request)
            search_results = search_response.results

            # Filter results to only include specific products (where productCode exists)
            filtered_results = []
            for result in search_results:
                metadata_dict = result.metadata.model_dump() if hasattr(result.metadata, 'model_dump') else result.metadata.dict()
                product_code = metadata_dict.get('product_code') or metadata_dict.get('productCode')

                # Only include results that have productCode (specific products, not collection info)
                if product_code:
                    filtered_results.append({
                        "content": result.content[:500],  # Truncate for token efficiency
                        "score": result.score,
                        "metadata": {
                            "product_code": product_code,
                            "collection_name": metadata_dict.get('collection_name') or metadata_dict.get('collectionName'),
                            "brand_name": metadata_dict.get('brand_name') or metadata_dict.get('brandName'),
                            "source": metadata_dict.get('source'),
                        }
                    })

            # Return as JSON string
            return json.dumps({
                "total_results": len(filtered_results),
                "results": filtered_results
            }, ensure_ascii=False)

        except Exception as e:
            return json.dumps({
                "error": f"Search failed: {str(e)}",
                "total_results": 0,
                "results": []
            }, ensure_ascii=False)

    # Create StructuredTool using LangChain
    return StructuredTool.from_function(
        func=search_products,
        name="search_products",
        description=(
            "Search for specific products in the products collection. "
            "Use this tool when the user asks about specific product codes, product names, "
            "product specifications, features, prices, or individual product details. "
            "DO NOT use this tool for company information or collection information questions."
        ),
        args_schema=ProductsSearchArgsDTO
    )


def create_add_to_cart_tool(
    search_use_case: SearchUseCase,
    shopping_cart_service: ShoppingCartService
) -> StructuredTool:
    """
    Create add_to_cart tool using LangChain StructuredTool

    This tool adds a product to the shopping cart based on product code.
    It searches for the product to get productId and price, then calls the shopping cart API.

    Args:
        search_use_case: SearchUseCase instance to find product details
        shopping_cart_service: ShoppingCartService instance to call cart API

    Returns:
        StructuredTool instance for add_to_cart
    """
    async def add_to_cart(
        product_code: str,
        quantity: int = 1,
        session_id: Optional[str] = None
    ) -> str:
        """
        Add a product to the shopping cart

        Use this tool when the user wants to:
        - Add a product to their cart
        - Purchase a product
        - Add items to shopping cart

        Args:
            product_code: Product code to add to cart
            quantity: Quantity to add (1-100)
            session_id: Optional session ID for cart management

        Returns:
            JSON string with cart operation result
        """
        try:
            # Step 1: Search for product by product_code to get productId and price
            search_request = SearchRequestDTO(
                query=product_code,
                top_k=1,
                collection_name=CollectionType.PRODUCTS,
                metadata_filter={"productCode": product_code}  # Filter by exact product code
            )

            search_response = await search_use_case.search_documents(search_request)
            search_results = search_response.results

            if not search_results:
                return json.dumps({
                    "success": False,
                    "error": f"Product with code '{product_code}' not found",
                    "product_code": product_code
                }, ensure_ascii=False)

            # Get product details from first result
            result = search_results[0]
            metadata_dict = result.metadata.model_dump() if hasattr(result.metadata, 'model_dump') else result.metadata.dict()

            # Extract productId and price from metadata
            # Note: productId might be in metadata as 'productId' or 'product_id'
            # price might be in metadata as 'price' or need to be extracted from content
            product_id = metadata_dict.get('productId') or metadata_dict.get('product_id')
            price = metadata_dict.get('price')

            # If productId is not in metadata, try to extract from content or use product_code as fallback
            if not product_id:
                # Try to parse product_code as integer (if it's already a productId)
                try:
                    product_id = int(product_code)
                except ValueError:
                    return json.dumps({
                        "success": False,
                        "error": f"Could not find productId for product code '{product_code}'. Product may not exist in the system.",
                        "product_code": product_code
                    }, ensure_ascii=False)

            # If price is not in metadata, default to 0 (API might handle this)
            if price is None:
                price = 0.0
            else:
                try:
                    price = float(price)
                except (ValueError, TypeError):
                    price = 0.0

            # Step 2: Call shopping cart API
            cart_result = await shopping_cart_service.add_to_cart(
                product_id=product_id,
                quantity=quantity,
                price=price,
                session_id=session_id
            )

            # Format result for LLM
            if cart_result.get("success"):
                return json.dumps({
                    "success": True,
                    "message": f"Product {product_code} (quantity: {quantity}) added to cart successfully",
                    "product_code": product_code,
                    "product_id": product_id,
                    "quantity": quantity,
                    "price": price,
                    "session_id": session_id or "default",
                    "data": cart_result.get("data", {})
                }, ensure_ascii=False)
            else:
                return json.dumps({
                    "success": False,
                    "error": cart_result.get("error", "Failed to add product to cart"),
                    "product_code": product_code,
                    "product_id": product_id,
                    "quantity": quantity
                }, ensure_ascii=False)

        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Failed to add product to cart: {str(e)}",
                "product_code": product_code
            }, ensure_ascii=False)

    # Create StructuredTool using LangChain
    return StructuredTool.from_function(
        func=add_to_cart,
        name="add_to_cart",
        description=(
            "Add a product to the shopping cart. "
            "Use this tool when the user wants to add a product to their cart, purchase a product, "
            "or add items to shopping cart. "
            "You need the product_code to use this tool. "
            "If the user mentions a product but doesn't provide the product code, "
            "first use search_products to find the product code."
        ),
        args_schema=AddToCartArgsDTO
    )


# Legacy function for backward compatibility (deprecated)
def create_search_tool(search_use_case: SearchUseCase) -> StructuredTool:
    """
    DEPRECATED: Use create_company_info_tool or create_collection_info_tool instead

    This function is kept for backward compatibility but should not be used in new code.
    """
    return create_company_info_tool(search_use_case)
