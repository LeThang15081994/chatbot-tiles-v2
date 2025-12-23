"""
Milvus Vector Store Repository Implementation
Implements IVectorStore interface from Application layer
"""
from typing import List, Optional, Dict, Any
from pymilvus import connections, Collection, utility
from langchain_milvus import Milvus, BM25BuiltInFunction
from langchain_core.documents import Document as LangchainDocument

from app.src.application.interfaces.vector_store_repository import IVectorStoreRepository
from app.src.domain.entities import Document, RetrievalResult, RetrievalStrategy
from app.src.domain.value_objects import SearchQuery, SearchFilter
from app.src.infrastructure.config.milvus_settings import MilvusSettings


class MilvusVectorStoreRepository(IVectorStoreRepository):
    """
    Milvus implementation of IVectorStore

    Provides vector search, BM25, and hybrid search capabilities
    with support for multiple collections (company_document_info, products)
    """

    def __init__(
        self,
        settings: MilvusSettings,
        embedding_service
    ):
        """
        Initialize Milvus repository

        Args:
            settings: Milvus configuration settings
            embedding_service: Embedding service for vector generation
        """
        self.settings = settings
        self.embedding_service = embedding_service
        self.is_connected = False

        # Collections
        self.company_collection: Optional[Collection] = None
        self.products_collection: Optional[Collection] = None
        self.products_info_collection: Optional[Collection] = None
        self.collection_info_collection: Optional[Collection] = None

        # LangChain wrappers
        self.langchain_milvus_document: Optional[Milvus] = None
        self.langchain_milvus_products: Optional[Milvus] = None
        self.langchain_milvus_products_info: Optional[Milvus] = None
        self.langchain_milvus_collection_info: Optional[Milvus] = None

        # BM25 function
        self.bm25_function: Optional[BM25BuiltInFunction] = None

        # Connect
        self._connect()

    def _connect(self) -> None:
        """Establish connection to Milvus and initialize collections"""
        try:
            # Connect to Milvus with database name
            connections.connect(
                alias=self.settings.MILVUS_ALIAS,
                host=self.settings.MILVUS_HOST,
                port=self.settings.MILVUS_PORT,
                db_name=self.settings.MILVUS_DB  # Specify database name
            )

            # Load company_document_info collection
            if utility.has_collection(
                self.settings.MILVUS_COLLECTION_COMPANY_DOCUMENT,
                using=self.settings.MILVUS_ALIAS
            ):
                self.company_collection = Collection(
                    self.settings.MILVUS_COLLECTION_COMPANY_DOCUMENT,
                    using=self.settings.MILVUS_ALIAS
                )
                self.company_collection.load()

            # Load products collection
            if utility.has_collection(
                self.settings.MILVUS_COLLECTION_PRODUCTS,
                using=self.settings.MILVUS_ALIAS
            ):
                self.products_collection = Collection(
                    self.settings.MILVUS_COLLECTION_PRODUCTS,
                    using=self.settings.MILVUS_ALIAS
                )
                self.products_collection.load()

            # Load products_info collection (for company info search)
            if utility.has_collection(
                self.settings.MILVUS_COLLECTION_PRODUCTS_INFO,
                using=self.settings.MILVUS_ALIAS
            ):
                self.products_info_collection = Collection(
                    self.settings.MILVUS_COLLECTION_PRODUCTS_INFO,
                    using=self.settings.MILVUS_ALIAS
                )
                self.products_info_collection.load()

            # Load collection_info collection (for collection info search)
            if utility.has_collection(
                self.settings.MILVUS_COLLECTION_COLLECTION_INFO,
                using=self.settings.MILVUS_ALIAS
            ):
                self.collection_info_collection = Collection(
                    self.settings.MILVUS_COLLECTION_COLLECTION_INFO,
                    using=self.settings.MILVUS_ALIAS
                )
                self.collection_info_collection.load()

            # Initialize LangChain wrappers
            self._initialize_langchain_wrappers()

            # Initialize BM25
            self._initialize_bm25()

            self.is_connected = True

        except Exception as e:
            raise ConnectionError(f"Failed to connect to Milvus: {e}")

    def _initialize_langchain_wrappers(self) -> None:
        """Initialize LangChain Milvus wrappers"""
        connection_args = {
            "host": self.settings.MILVUS_HOST,
            "port": self.settings.MILVUS_PORT,
            "alias": self.settings.MILVUS_ALIAS
        }

        # Company collection wrapper
        if self.company_collection:
            self.langchain_milvus_document = Milvus(
                embedding_function=self.embedding_service,
                collection_name=self.settings.MILVUS_COLLECTION_COMPANY_DOCUMENT,
                connection_args=connection_args,
                primary_field="id",
                text_field="content",
                vector_field="vector",
                enable_dynamic_field=True
            )

        # Products collection wrapper
        if self.products_collection:
            self.langchain_milvus_products = Milvus(
                embedding_function=self.embedding_service,
                collection_name=self.settings.MILVUS_COLLECTION_PRODUCTS,
                connection_args=connection_args,
                primary_field="id",
                text_field="description",
                vector_field="vector",
                enable_dynamic_field=True
            )

        # Products info collection wrapper (for company info search)
        if self.products_info_collection:
            self.langchain_milvus_products_info = Milvus(
                embedding_function=self.embedding_service,
                collection_name=self.settings.MILVUS_COLLECTION_PRODUCTS_INFO,
                connection_args=connection_args,
                primary_field="id",
                text_field="description",  # Assuming same schema as products
                vector_field="vector",
                enable_dynamic_field=True
            )

        # Collection info collection wrapper (for collection info search)
        if self.collection_info_collection:
            self.langchain_milvus_collection_info = Milvus(
                embedding_function=self.embedding_service,
                collection_name=self.settings.MILVUS_COLLECTION_COLLECTION_INFO,
                connection_args=connection_args,
                primary_field="id",
                text_field="description",  # Assuming same schema as products
                vector_field="vector",
                enable_dynamic_field=True
            )

    def _initialize_bm25(self) -> None:
        """Initialize BM25 function"""
        try:
            self.bm25_function = BM25BuiltInFunction()
        except Exception:
            self.bm25_function = None

    def _get_collection_by_name(
        self,
        collection_name: Optional[str] = None
    ) -> tuple:
        """Get collection, wrapper, and text field by name"""
        # Support both old and new collection names for backward compatibility
        if not collection_name or collection_name.lower() in [
            "company_document", "company_document_info", "company", "document"
        ]:
            return (
                self.company_collection,
                self.langchain_milvus_document,
                "content"
            )
        elif collection_name.lower() in ["products_info", "products_info"]:
            return (
                self.products_info_collection,
                self.langchain_milvus_products_info,
                "description"
            )
        elif collection_name.lower() in ["collection_info", "collection_info"]:
            return (
                self.collection_info_collection,
                self.langchain_milvus_collection_info,
                "description"
            )
        else:
            return (
                self.company_collection,
                self.langchain_milvus_document,
                "content"
            )

    def _convert_langchain_doc_to_domain(
        self,
        lc_doc: LangchainDocument
    ) -> Document:
        """Convert LangChain Document to Domain Document"""
        return Document(
            content=lc_doc.page_content,
            source=lc_doc.metadata.get("source"),
            metadata=lc_doc.metadata,
            vector_score=lc_doc.metadata.get("score"),
            bm25_score=lc_doc.metadata.get("bm25_score"),
            hybrid_score=lc_doc.metadata.get("hybrid_score")
        )

    async def search(
        self,
        query: SearchQuery,
        filters: Optional[SearchFilter] = None
    ) -> RetrievalResult:
        """
        Hybrid search implementation

        Args:
            query: Search query with parameters
            filters: Optional metadata filters

        Returns:
            RetrievalResult with documents
        """
        try:
            # Get collection
            collection, wrapper, text_field = self._get_collection_by_name(
                query.collection_name
            )

            if not collection or not wrapper:
                return RetrievalResult(
                    query=query.text,
                    documents=[],
                    strategy=RetrievalStrategy.HYBRID,
                    total_retrieved=0
                )

            # Convert filters to Milvus expression
            filter_expr = None
            if filters and not filters.is_empty():
                filter_expr = filters.to_milvus_expr()

            # For products, always filter active products
            if query.collection_name and "product" in query.collection_name.lower():
                active_filter = "isActive == true"
                if filter_expr:
                    filter_expr = f"{filter_expr} && {active_filter}"
                else:
                    filter_expr = active_filter

            # Perform hybrid search
            documents = []

            # Vector search
            vector_results = wrapper.similarity_search(
                query=query.text,
                k=query.top_k * 2,
                expr=filter_expr
            )

            # BM25 search if available
            bm25_results = []
            if self.bm25_function:
                try:
                    bm25_results = collection.search(
                        data=[query.text],
                        anns_field=text_field,
                        param={"metric_type": "BM25"},
                        limit=query.top_k * 2,
                        expr=filter_expr,
                        output_fields=[text_field, "metadata"]
                    )
                except Exception:
                    pass

            # Combine and score results
            doc_scores = {}

            # Process vector results
            for lc_doc in vector_results:
                doc_id = lc_doc.metadata.get('id')
                if doc_id:
                    doc = self._convert_langchain_doc_to_domain(lc_doc)
                    doc_scores[doc_id] = {
                        'doc': doc,
                        'vector_score': doc.vector_score or 0.0,
                        'bm25_score': 0.0,
                        'combined_score': (doc.vector_score or 0.0) * 0.7
                    }

            # Process BM25 results
            for hits in bm25_results:
                for hit in hits:
                    doc_id = hit.id
                    if doc_id in doc_scores:
                        doc_scores[doc_id]['bm25_score'] = hit.score
                        doc_scores[doc_id]['combined_score'] += hit.score * 0.3
                    else:
                        # Create new document from BM25 result
                        doc = Document(
                            content=hit.entity.get(text_field, ""),
                            metadata=hit.entity.get("metadata", {}),
                            bm25_score=hit.score
                        )
                        doc_scores[doc_id] = {
                            'doc': doc,
                            'vector_score': 0.0,
                            'bm25_score': hit.score,
                            'combined_score': hit.score * 0.3
                        }

            # Sort by combined score and take top_k
            sorted_results = sorted(
                doc_scores.values(),
                key=lambda x: x['combined_score'],
                reverse=True
            )[:query.top_k]

            # Update document scores
            for result in sorted_results:
                doc = result['doc']
                doc.vector_score = result['vector_score']
                doc.bm25_score = result['bm25_score']
                doc.hybrid_score = result['combined_score']
                documents.append(doc)

            return RetrievalResult(
                query=query.text,
                documents=documents,
                strategy=RetrievalStrategy.HYBRID,
                total_retrieved=len(documents)
            )

        except Exception as e:
            raise RuntimeError(f"Search failed: {e}")

    async def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to collection"""
        try:
            if not self.langchain_milvus_document:
                raise RuntimeError("Milvus not initialized")

            # Convert domain documents to LangChain documents
            lc_docs = [
                LangchainDocument(
                    page_content=doc.content,
                    metadata=doc.metadata
                )
                for doc in documents
            ]

            # Add via LangChain wrapper
            doc_ids = self.langchain_milvus_document.add_documents(lc_docs)

            return doc_ids

        except Exception as e:
            raise RuntimeError(f"Failed to add documents: {e}")

    async def delete_documents(self, document_ids: List[str]) -> bool:
        """Delete documents by IDs"""
        try:
            if not self.company_collection:
                raise RuntimeError("Collection not initialized")

            # Create filter expression
            ids_str = "', '".join(document_ids)
            expr = f"id in ['{ids_str}']"

            # Delete
            self.company_collection.delete(expr)
            self.company_collection.flush()

            return True

        except Exception as e:
            raise RuntimeError(f"Failed to delete documents: {e}")

    async def health_check(self) -> bool:
        """Check Milvus health"""
        try:
            return self.is_connected and self.company_collection is not None
        except Exception:
            return False

