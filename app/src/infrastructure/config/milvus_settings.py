"""
Milvus Configuration Settings
"""
from pydantic_settings import BaseSettings


class MilvusSettings(BaseSettings):
    """Milvus configuration"""

    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_ALIAS: str = "default"
    MILVUS_DB: str = "chatbot_gachai"  # Database name
    MILVUS_COLLECTION_COMPANY_DOCUMENT: str = "company_document_info"  # Legacy collection name
    MILVUS_COLLECTION_PRODUCTS: str = "products"  # Legacy collection name
    MILVUS_COLLECTION_PRODUCTS_INFO: str = "products_info"  # Collection for company info search
    MILVUS_COLLECTION_COLLECTION_INFO: str = "collection_info"  # Collection for collection info search
    MILVUS_DIMENSION: int = 1536
    MILVUS_INDEX_TYPE: str = "IVF_FLAT"
    MILVUS_METRIC_TYPE: str = "IP"
    MILVUS_NLIST: int = 128

    class Config:
        env_file = ".env"
        case_sensitive = True

