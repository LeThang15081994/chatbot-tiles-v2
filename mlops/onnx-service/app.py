"""
Lightweight ONNX Runtime Embedding Service
FastAPI service for embedding inference (no Triton needed)
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import numpy as np
from model_loader import ONNXEmbeddingModel
from pathlib import Path
import os

# Global model instance
_model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global _model

    # Startup
    model_dir = os.getenv("MODEL_DIR", "/app/models")
    print(f"📥 Loading ONNX model from: {model_dir}")
    try:
        _model = ONNXEmbeddingModel(model_dir)
        print("✅ Model loaded successfully!")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        raise

    yield

    # Shutdown (cleanup if needed)
    _model = None


app = FastAPI(
    title="ONNX Embedding Service",
    description="Lightweight embedding service using ONNX Runtime",
    version="1.0.0",
    lifespan=lifespan
)


class EmbedRequest(BaseModel):
    """Embedding request"""
    texts: List[str]


class EmbedResponse(BaseModel):
    """Embedding response"""
    embeddings: List[List[float]]
    dimension: int
    count: int


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "model_loaded": _model is not None
    }


@app.post("/embed", response_model=EmbedResponse)
async def embed(request: EmbedRequest):
    """
    Generate embeddings for texts

    Args:
        request: Embedding request with texts

    Returns:
        Embedding response with embeddings
    """
    if _model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if not request.texts:
        raise HTTPException(status_code=400, detail="Texts list cannot be empty")

    try:
        # Generate embeddings
        embeddings = _model.embed(request.texts)

        # Convert to list
        embeddings_list = embeddings.tolist()

        return EmbedResponse(
            embeddings=embeddings_list,
            dimension=_model.dimension,
            count=len(request.texts)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "7000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

