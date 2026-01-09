import os
import logging
from typing import List, Union
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastembed import LateInteractionTextEmbedding

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
    model_name = os.getenv("MODEL_NAME", "colbert-ir/colbertv2.0")
    logger.info(f"Loading model: {model_name}")
    try:
        model = LateInteractionTextEmbedding(model_name=model_name)
        logger.info(f"Model {model_name} loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

    yield

    # Cleanup
    logger.info("Shutting down...")

app = FastAPI(
    title="FastEmbed ColBERT Service",
    description="API for generating ColBERT late interaction embeddings using FastEmbed",
    version="1.0.0",
    lifespan=lifespan
)

class EmbeddingRequest(BaseModel):
    """Request model for embedding generation."""
    texts: Union[str, List[str]] = Field(
        ...,
        description="Single text or list of texts to embed"
    )

class MultiVectorValue(BaseModel):
    """Multi-vector embedding value."""
    embeddings: List[List[float]]  # List of token embeddings

class EmbeddingResponse(BaseModel):
    """Response model for embeddings."""
    embeddings: List[MultiVectorValue]
    model: str
    count: int

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model": os.getenv("MODEL_NAME", "colbert-ir/colbertv2.0"),
        "service": "FastEmbed ColBERT"
    }

@app.get("/health")
async def health():
    """Detailed health check endpoint."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    return {
        "status": "healthy",
        "model": os.getenv("MODEL_NAME", "colbert-ir/colbertv2.0"),
        "model_loaded": model is not None
    }

@app.post("/embed", response_model=EmbeddingResponse)
async def embed_text(request: EmbeddingRequest):
    """
    Generate ColBERT late interaction embeddings for the provided text(s).

    Args:
        request: EmbeddingRequest containing text(s) to embed

    Returns:
        EmbeddingResponse with multi-vector embeddings
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
        multi_vector_embeddings = []
        for embedding in embeddings:
            # ColBERT produces multiple vectors (one per token)
            multi_vector_embeddings.append(
                MultiVectorValue(
                    embeddings=embedding.tolist()
                )
            )

        logger.info(f"Successfully generated {len(multi_vector_embeddings)} embedding(s)")

        return EmbeddingResponse(
            embeddings=multi_vector_embeddings,
            model=os.getenv("MODEL_NAME", "colbert-ir/colbertv2.0"),
            count=len(multi_vector_embeddings)
        )

    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating embeddings: {str(e)}")

@app.post("/embed/single")
async def embed_single_text(request: EmbeddingRequest):
    """
    Generate ColBERT late interaction embedding for a single text.
    Convenience endpoint that returns a single embedding object.

    Args:
        request: EmbeddingRequest containing a single text

    Returns:
        Single multi-vector embedding
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
            "embedding": embedding.tolist(),
            "model": os.getenv("MODEL_NAME", "colbert-ir/colbertv2.0"),
            "num_vectors": len(embedding)
        }

        logger.info(f"Successfully generated single embedding with {len(embedding)} vectors")
        return result

    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating embedding: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)