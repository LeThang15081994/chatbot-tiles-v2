"""
Shopping Cart Service
Handles API calls to shopping cart service
"""
import httpx
from typing import Dict, Any, Optional
from app.src.infrastructure.config.llm_settings import LLMSettings


class ShoppingCartService:
    """
    Shopping Cart Service

    Handles API calls to shopping cart service for adding products to cart
    """

    def __init__(self, settings: LLMSettings):
        """
        Initialize shopping cart service

        Args:
            settings: LLM configuration settings (contains shopping cart settings)
        """
        self.settings = settings
        self.api_url = settings.SHOPPING_CART_API_URL
        self.timeout = settings.SHOPPING_CART_API_TIMEOUT

        # HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            base_url=self.api_url,
            timeout=self.timeout,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=50)
        )

    async def add_to_cart(
        self,
        product_id: int,
        quantity: int,
        price: float,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add product to shopping cart via API

        Args:
            product_id: Product ID (integer)
            quantity: Quantity to add
            price: Product price
            session_id: Optional session ID for cart management

        Returns:
            Dictionary with API response

        Raises:
            RuntimeError: If API call fails
        """
        try:
            payload = {
                "productId": product_id,
                "quantity": quantity,
                "price": price
            }

            # Add session_id to headers if provided
            headers = {}
            if session_id:
                headers["X-Session-Id"] = session_id

            response = await self.client.post(
                "/add",
                json=payload,
                headers=headers if headers else None
            )
            response.raise_for_status()

            result = response.json()
            return {
                "success": True,
                "data": result,
                "product_id": product_id,
                "quantity": quantity,
                "price": price
            }

        except httpx.HTTPStatusError as e:
            error_message = f"Shopping cart API error: {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_message += f" - {error_detail}"
            except:
                error_message += f" - {e.response.text}"

            return {
                "success": False,
                "error": error_message,
                "product_id": product_id,
                "quantity": quantity,
                "price": price
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to add product to cart: {str(e)}",
                "product_id": product_id,
                "quantity": quantity,
                "price": price
            }

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

