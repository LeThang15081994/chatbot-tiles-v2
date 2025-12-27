"""
Milvus Configuration Settings
"""
from typing import Optional
from pydantic_settings import BaseSettings

from pydantic import Field

class MilvusSettings(BaseSettings):
    """Milvus configuration"""

    MILVUS_HOST: str = Field(default="localhost", description="Milvus IP")
    MILVUS_PORT: int = Field(default=19530, description="Milvus Port")
    MILVUS_ALIAS: str = Field(default="default", description="Milvus Alias")
    MILVUS_DB: str = Field(default="chatbot_gachai", description="Milvus Database Name")

    # Authentication (optional - only needed if Milvus requires auth)
    MILVUS_USER: Optional[str] = Field(default="root", description="Milvus Username")
    MILVUS_PASSWORD: Optional[str] = Field(default="Milvus", description="Milvus Password")

    MILVUS_COLLECTION_COMPANY_DOCUMENT: str = Field(default="company_document_info", description="Milvus Company Document Collection Name")
    MILVUS_COLLECTION_PRODUCTS: str = Field(default="products", description="Milvus Products Collection Name")
    MILVUS_COLLECTION_PRODUCTS_INFO: str = Field(default="products_info", description="Milvus Products Info Collection Name")
    MILVUS_COLLECTION_COLLECTION_INFO: str = Field(default="collection_info", description="Milvus Collection Info Collection Name")
    MILVUS_DIMENSION: int = Field(default=1536, description="Milvus Dimension")
    MILVUS_INDEX_TYPE: str = Field(default="IVF_FLAT", description="Milvus Index Type")
    MILVUS_METRIC_TYPE: str = Field(default="IP", description="Milvus Metric Type")
    MILVUS_NLIST: int = Field(default=128, description="Milvus NList")

    class Config:
        env_file = ".env"
        case_sensitive = True

