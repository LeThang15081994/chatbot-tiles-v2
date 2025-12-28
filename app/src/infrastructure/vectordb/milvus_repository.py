"""
Milvus Vector Store Repository Implementation
Implements IVectorStore interface from Application layer
"""
from typing import List, Optional, Dict, Any
from pymilvus import connections, Collection, utility
from langchain_milvus import Milvus, BM25BuiltInFunction
from langchain_core.documents import Document as LangchainDocument

from app.src.application.dto.document_dto import DocumentDTO, DocumentMetadataDTO
from app.src.application.dto.search_dto import SearchResultDTO, SearchMetadataDTO
from app.src.domain.entities.document import Document
from app.src.domain.entities.retrieval_result import RetrievalResult, RetrievalStrategy
from app.src.domain.value_objects.query import SearchQuery
from app.src.domain.value_objects.search_filter import SearchFilter
from app.src.infrastructure.config.settings import MilvusSettings


class MilvusVectorStoreRepository:
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
            # Prepare connection parameters
            connect_params = {
                "alias": self.settings.MILVUS_ALIAS,
                "host": self.settings.MILVUS_HOST,
                "port": self.settings.MILVUS_PORT,
                "db_name": self.settings.MILVUS_DB
            }

            # Add authentication if provided
            if self.settings.MILVUS_USER:
                connect_params["user"] = self.settings.MILVUS_USER
            if self.settings.MILVUS_PASSWORD:
                connect_params["password"] = self.settings.MILVUS_PASSWORD

            # Connect to Milvus with database name and authentication
            connections.connect(**connect_params)

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

        # Add authentication if provided
        if self.settings.MILVUS_USER:
            connection_args["user"] = self.settings.MILVUS_USER
        if self.settings.MILVUS_PASSWORD:
            connection_args["password"] = self.settings.MILVUS_PASSWORD

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

    async def add_documents(
        self,
        documents: List[DocumentDTO],
        collection_name: Optional[str] = None
    ) -> List[str]:
        """
        Add documents to vector store (interface method)

        Args:
            documents: List of documents to add
            collection_name: Name of collection to add to

        Returns:
            List of document IDs
        """
        try:
            # Get collection wrapper
            _, wrapper, _ = self._get_collection_by_name(collection_name)

            if not wrapper:
                raise RuntimeError(f"Collection not found: {collection_name}")

            # Convert DocumentDTO to LangChain Document
            lc_docs = []
            for doc_dto in documents:
                metadata = doc_dto.metadata.dict() if doc_dto.metadata else {}
                metadata['id'] = doc_dto.id
                if doc_dto.metadata:
                    if doc_dto.metadata.source:
                        metadata['source'] = doc_dto.metadata.source
                    if doc_dto.metadata.category:
                        metadata['category'] = doc_dto.metadata.category
                    if doc_dto.metadata.brand_name:
                        metadata['brand_name'] = doc_dto.metadata.brand_name

                lc_doc = LangchainDocument(
                    page_content=doc_dto.content,
                    metadata=metadata
                )
                lc_docs.append(lc_doc)

            # Add via LangChain wrapper
            doc_ids = wrapper.add_documents(lc_docs)
            return doc_ids

        except Exception as e:
            raise RuntimeError(f"Failed to add documents: {e}")

    async def update_document(
        self,
        document_id: str,
        document: DocumentDTO,
        collection_name: Optional[str] = None
    ) -> bool:
        """
        Update a document in vector store (interface method)

        Args:
            document_id: ID of document to update
            document: Updated document data
            collection_name: Name of collection

        Returns:
            True if successful
        """
        try:
            # Get collection
            collection, wrapper, text_field = self._get_collection_by_name(collection_name)

            if not collection:
                raise RuntimeError(f"Collection not found: {collection_name}")

            # Delete old document
            await self.delete_documents([document_id], collection_name)

            # Add updated document
            doc_dto = DocumentDTO(
                id=document_id,
                content=document.content,
                metadata=document.metadata,
                vector=document.vector
            )
            await self.add_documents([doc_dto], collection_name)

            return True

        except Exception as e:
            raise RuntimeError(f"Failed to update document: {e}")

    async def hybrid_search(
        self,
        query: str,
        k: int = 5,
        collection_name: Optional[str] = None,
        filter_expr: Optional[str] = None
    ) -> List[SearchResultDTO]:
        """
        Perform hybrid search (vector + BM25) using LangChain for vector search

        Args:
            query: Search query text
            k: Number of results to return
            collection_name: Name of collection to search
            filter_expr: Filter expression for metadata filtering

        Returns:
            List of search results with combined scores
        """
        try:
            # Get collection and wrapper
            collection, wrapper, text_field = self._get_collection_by_name(collection_name)

            if not collection or not wrapper:
                return []

            # For products, always filter active products
            if collection_name and "product" in collection_name.lower():
                active_filter = "isActive == true"
                if filter_expr:
                    filter_expr = f"{filter_expr} && {active_filter}"
                else:
                    filter_expr = active_filter

            # Vector search using LangChain wrapper (vector similarity)
            vector_results = wrapper.similarity_search(
                query=query,
                k=k * 2,  # Get more results for combining
                expr=filter_expr
            )

            # BM25 search using direct PyMilvus (only for BM25)
            bm25_results = []
            if self.bm25_function:
                try:
                    bm25_results = collection.search(
                        data=[query],
                        anns_field=text_field,
                        param={"metric_type": "BM25"},
                        limit=k * 2,
                        expr=filter_expr,
                        output_fields=[text_field, "metadata"]
                    )
                except Exception:
                    pass

            # Combine and score results
            doc_scores = {}

            # Process vector results (from LangChain)
            for lc_doc in vector_results:
                doc_id = lc_doc.metadata.get('id')
                if doc_id:
                    vector_score = lc_doc.metadata.get('score', 0.0)
                    doc_scores[doc_id] = {
                        'doc': lc_doc,
                        'vector_score': vector_score,
                        'bm25_score': 0.0,
                        'combined_score': vector_score * 0.7  # Vector weight: 70%
                    }

            # Process BM25 results (from direct PyMilvus)
            for hits in bm25_results:
                for hit in hits:
                    doc_id = hit.id
                    bm25_score = hit.score
                    if doc_id in doc_scores:
                        # Document already in results from vector search
                        doc_scores[doc_id]['bm25_score'] = bm25_score
                        doc_scores[doc_id]['combined_score'] += bm25_score * 0.3  # BM25 weight: 30%
                    else:
                        # New document from BM25 only - convert to LangChain Document
                        content = hit.entity.get(text_field, "")
                        metadata = hit.entity.get("metadata", {})
                        if isinstance(metadata, str):
                            import json
                            try:
                                metadata = json.loads(metadata)
                            except:
                                metadata = {}

                        lc_doc = LangchainDocument(
                            page_content=content,
                            metadata={**metadata, 'id': doc_id}
                        )
                        doc_scores[doc_id] = {
                            'doc': lc_doc,
                            'vector_score': 0.0,
                            'bm25_score': bm25_score,
                            'combined_score': bm25_score * 0.3  # BM25 only: 30%
                        }

            # Sort by combined score and take top_k
            sorted_results = sorted(
                doc_scores.values(),
                key=lambda x: x['combined_score'],
                reverse=True
            )[:k]

            # Convert to SearchResultDTO
            search_results = []
            for result in sorted_results:
                lc_doc = result['doc']
                metadata = lc_doc.metadata

                search_metadata = SearchMetadataDTO(
                    id=metadata.get('id'),
                    category=metadata.get('category'),
                    source=metadata.get('source'),
                    brand_name=metadata.get('brand_name') or metadata.get('brandName'),
                    collection_name=collection_name,
                    updated_time=metadata.get('updated_time') or metadata.get('updatedTime'),
                    hybrid_score=result['combined_score'],
                    vector_score=result['vector_score'],
                    bm25_score=result['bm25_score']
                )

                search_result = SearchResultDTO(
                    content=lc_doc.page_content,
                    metadata=search_metadata,
                    score=result['combined_score']
                )
                search_results.append(search_result)

            return search_results

        except Exception as e:
            raise RuntimeError(f"Hybrid search failed: {e}")

    async def get_document(
        self,
        document_id: str,
        collection_name: Optional[str] = None
    ) -> Optional[DocumentDTO]:
        """
        Get a document by ID (interface method)

        Args:
            document_id: Document ID
            collection_name: Name of collection

        Returns:
            Document if found, None otherwise
        """
        try:
            # Get collection
            collection, _, text_field = self._get_collection_by_name(collection_name)

            if not collection:
                return None

            # Query by ID
            collection.load()
            results = collection.query(
                expr=f"id == '{document_id}'",
                output_fields=[text_field, "metadata", "vector"]
            )

            if not results:
                return None

            result = results[0]

            # Extract metadata
            metadata_dict = result.get("metadata", {})
            if isinstance(metadata_dict, str):
                import json
                try:
                    metadata_dict = json.loads(metadata_dict)
                except:
                    metadata_dict = {}

            doc_metadata = DocumentMetadataDTO(
                id=document_id,
                source=metadata_dict.get('source'),
                category=metadata_dict.get('category'),
                brand_name=metadata_dict.get('brand_name') or metadata_dict.get('brandName'),
                custom_fields=metadata_dict
            )

            doc_dto = DocumentDTO(
                id=document_id,
                content=result.get(text_field, ""),
                metadata=doc_metadata,
                vector=result.get("vector")
            )

            return doc_dto

        except Exception as e:
            raise RuntimeError(f"Failed to get document: {e}")

    async def health_check(self) -> bool:
        """Check Milvus health"""
        try:
            return self.is_connected and self.company_collection is not None
        except Exception:
            return False

