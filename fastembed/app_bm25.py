import os
import logging
from typing import List, Union
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastembed import SparseTextEmbedding

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global model instance
model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the model on startup and cleanup on shutdown."""
    global model
    model_name = os.getenv("MODEL_NAME", "Qdrant/bm25")
    logger.info(f"Loading model: {model_name}")
    try:
        model = SparseTextEmbedding(model_name=model_name)
        logger.info(f"Model {model_name} loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

    yield

    # Cleanup
    logger.info("Shutting down...")

app = FastAPI(
    title="FastEmbed BM25 Service",
    description="API for generating BM25 sparse embeddings using FastEmbed",
    version="1.0.0",
    lifespan=lifespan
)

class EmbeddingRequest(BaseModel):
    """Request model for embedding generation."""
    texts: Union[str, List[str]] = Field(
        ...,
        description="Single text or list of texts to embed"
    )

class SparseValue(BaseModel):
    """Sparse vector value with index and value."""
    indices: List[int]
    values: List[float]

class EmbeddingResponse(BaseModel):
    """Response model for embeddings."""
    embeddings: List[SparseValue]
    model: str
    count: int

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model": os.getenv("MODEL_NAME", "Qdrant/bm25"),
        "service": "FastEmbed BM25"
    }

@app.get("/health")
async def health():
    """Detailed health check endpoint."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    return {
        "status": "healthy",
        "model": os.getenv("MODEL_NAME", "Qdrant/bm25"),
        "model_loaded": model is not None
    }

@app.post("/embed", response_model=EmbeddingResponse)
async def embed_text(request: EmbeddingRequest):
    """
    Generate BM25 sparse embeddings for the provided text(s).

    Args:
        request: EmbeddingRequest containing text(s) to embed

    Returns:
        EmbeddingResponse with sparse embeddings
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # Ensure texts is a list
        texts = request.texts if isinstance(request.texts, list) else [request.texts]

        logger.info(f"Generating embeddings for {len(texts)} text(s)")

        # Generate embeddings
        embeddings_generator = model.embed(texts)
        embeddings = list(embeddings_generator)

        # Convert to response format
        sparse_embeddings = []
        for embedding in embeddings:
            sparse_embeddings.append(
                SparseValue(
                    indices=embedding.indices.tolist(),
                    values=embedding.values.tolist()
                )
            )

        logger.info(f"Successfully generated {len(sparse_embeddings)} embedding(s)")

        return EmbeddingResponse(
            embeddings=sparse_embeddings,
            model=os.getenv("MODEL_NAME", "Qdrant/bm25"),
            count=len(sparse_embeddings)
        )

    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating embeddings: {str(e)}")

@app.post("/embed/single")
async def embed_single_text(request: EmbeddingRequest):
    """
    Generate BM25 sparse embedding for a single text.
    Convenience endpoint that returns a single embedding object.

    Args:
        request: EmbeddingRequest containing a single text

    Returns:
        Single sparse embedding
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # Ensure we're working with a single text
        text = request.texts if isinstance(request.texts, str) else request.texts[0]

        logger.info(f"Generating embedding for single text")

        # Generate embedding
        embeddings_generator = model.embed([text])
        embedding = next(embeddings_generator)

        result = {
            "embedding": {
                "indices": embedding.indices.tolist(),
                "values": embedding.values.tolist()
            },
            "model": os.getenv("MODEL_NAME", "Qdrant/bm25")
        }

        logger.info("Successfully generated single embedding")
        return result

    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating embedding: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)