"""Answer Cache Facade - Domain orchestrator managing 4-layer caching pipeline"""
import hashlib
import json
import asyncio
from typing import Optional, List, Tuple, Callable, Awaitable, Any
from app.src.domain.value_objects.cache_result import CacheResult


class AnswerCacheFacade:
    """Domain orchestrator for 4-layer caching: text → embedding → vector → semantic → RAG"""

    def __init__(
        self,
        text_cache: Any,  # ITextCache interface (injected from Application layer)
        embedding_service: Any,  # IEmbeddingService interface (injected from Application layer)
        vector_cache: Any,  # IVectorCache interface (injected from Application layer)
        semantic_cache: Any,  # ISemanticCache interface (injected from Application layer)
        retriever: Any,  # Document retriever (any object with invoke/ainvoke methods)
        llm_service: Any,  # ILLMService interface (injected from Application layer)
        guardrails_service: Optional[Any] = None,  # IGuardrailsService interface (injected from Application layer)
        similarity_threshold: float = 0.8
    ):
        """
        Initialize AnswerCacheFacade with 4 cache layers, retriever, LLM, and optional guardrails

        Note: All services are injected as Any to avoid Domain layer importing Application interfaces.
        Application layer (Use Cases) will inject implementations that conform to interfaces.
        """
        self.text_cache = text_cache
        self.embedding_service = embedding_service
        self.vector_cache = vector_cache
        self.semantic_cache = semantic_cache
        self.retriever = retriever
        self.llm_service = llm_service
        self.guardrails_service = guardrails_service
        self.similarity_threshold = similarity_threshold

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Step 0: Input normalization - lowercase, trim, normalize whitespace"""
        normalized = text.lower().strip()
        normalized = " ".join(normalized.split())
        return normalized

    @staticmethod
    def _hash_text(text: str) -> str:
        """Generate SHA256 hash for text"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    @staticmethod
    def _hash_vector(vector: List[float]) -> str:
        """Generate SHA256 hash for vector"""
        vector_str = json.dumps(vector, sort_keys=True)
        return hashlib.sha256(vector_str.encode('utf-8')).hexdigest()

    async def check_cache(self, raw_text: str) -> CacheResult:
        """Check all 4 cache layers - returns CacheResult"""
        # Step 0: Input normalization
        normalized_text = self._normalize_text(raw_text)
        text_hash = self._hash_text(normalized_text)

        # Step 0.5: Input Guardrails (before cache check)
        if self.guardrails_service:
            validation_result = await self.guardrails_service.validate_input(
                messages=[{"role": "user", "content": normalized_text}]
            )
            if validation_result.get("blocked", False):
                return CacheResult.blocked()
            if validation_result.get("altered_user_message"):
                normalized_text = validation_result["altered_user_message"]
                text_hash = self._hash_text(normalized_text)

        # Step 1: Cache #1 - Exact text answer
        cached_answer = await self.text_cache.get(text_hash)
        if cached_answer:
            return CacheResult.hit(cached_answer, "cache1", None)

        # Step 2: Cache #2 - Embedding cache (ONLY place /embed is called)
        query_vector = await asyncio.to_thread(
            self.embedding_service.embed_query,
            normalized_text
        )
        vector_hash = self._hash_vector(query_vector)

        # Step 3: Cache #3 - Exact embedding answer
        cached_answer = await self.vector_cache.get(vector_hash)
        if cached_answer:
            return CacheResult.hit(cached_answer, "cache3", query_vector)

        # Step 4: Cache #4 - Semantic cache (HNSW)
        semantic_result = await self.semantic_cache.search(
            query_vector=query_vector,
            similarity_threshold=self.similarity_threshold,
            top_k=1
        )
        if semantic_result:
            answer, score = semantic_result
            return CacheResult.hit(answer, "cache4", query_vector)

        return CacheResult.miss(query_vector)

    async def get_answer(
        self,
        raw_text: str,
        rag_generator: Optional[Callable[[str, List[float]], Awaitable[str]]] = None,
        context: Optional[str] = None
    ) -> Tuple[Optional[str], str]:
        """Execute 4-layer caching pipeline with optional custom RAG generator"""
        # Check cache first
        cache_result = await self.check_cache(raw_text)
        if cache_result.is_hit:
            return cache_result.answer, cache_result.cache_hit_layer
        if cache_result.is_blocked:
            return None, "blocked"

        query_vector = cache_result.query_vector

        # Step 5: Fallback - RAG Core
        if rag_generator:
            answer = await rag_generator(raw_text, query_vector)
        else:
            # Default RAG generation
            # Use retriever via duck typing (any object with invoke/ainvoke methods)
            # This works with LangChain BaseRetriever without importing LangChain in Domain layer
            try:
                # Try async first (preferred)
                if hasattr(self.retriever, 'ainvoke'):
                    documents_lc = await self.retriever.ainvoke(raw_text)
                else:
                    # Fallback to sync
                    documents_lc = await asyncio.to_thread(
                        self.retriever.invoke,
                        raw_text
                    )

                # Convert documents to dict format (handle both LangChain Documents and dicts)
                documents = []
                for doc in documents_lc[:5]:
                    if hasattr(doc, 'page_content'):
                        # LangChain Document
                        documents.append({
                            "content": doc.page_content,
                            "metadata": doc.metadata,
                            "id": doc.metadata.get("id") if isinstance(doc.metadata, dict) else None,
                            "score": doc.metadata.get("score", 0.0) if isinstance(doc.metadata, dict) else 0.0
                        })
                    elif isinstance(doc, dict):
                        # Already a dict
                        documents.append(doc)
                    else:
                        # Fallback: convert to string
                        documents.append({
                            "content": str(doc),
                            "metadata": {},
                            "id": None,
                            "score": 0.0
                        })
            except Exception as e:
                raise RuntimeError(
                    f"Failed to invoke retriever: {e}. "
                    f"Retriever must have invoke(query: str) and optionally ainvoke(query: str) methods."
                )

            prompt = f"Question: {raw_text}\n\nContext:\n"
            if context:
                prompt = f"{context}\n\n{prompt}"
            for doc in documents:
                prompt += f"- {doc.get('content', '')}\n"
            prompt += "\nAnswer based on the context above:"
            answer = await self.llm_service.invoke(prompt)

        # Step 6: Write-back to all caches
        normalized_text = self._normalize_text(raw_text)
        text_hash = self._hash_text(normalized_text)
        vector_hash = self._hash_vector(query_vector)
        await self._write_back(normalized_text, text_hash, query_vector, vector_hash, answer)

        return answer, "rag"

    async def write_to_cache(self, raw_text: str, answer: str, query_vector: Optional[List[float]] = None) -> None:
        """Write answer to all caches (Cache #1, #3, #4)"""
        normalized_text = self._normalize_text(raw_text)
        text_hash = self._hash_text(normalized_text)

        if query_vector is None:
            query_vector = await asyncio.to_thread(
                self.embedding_service.embed_query,
                normalized_text
            )
        vector_hash = self._hash_vector(query_vector)

        await self._write_back(normalized_text, text_hash, query_vector, vector_hash, answer)

    async def _write_back(
        self,
        normalized_text: str,
        text_hash: str,
        query_vector: List[float],
        vector_hash: str,
        answer: str
    ) -> None:
        """Step 6: Write-back to Cache #1, #3, and #4"""
        await self.text_cache.set(text_hash, answer)
        await self.vector_cache.set(vector_hash, answer)
        await self.semantic_cache.add(query_vector, answer)

