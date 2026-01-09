# Contextual RAG with Hybrid Search

A comprehensive Retrieval-Augmented Generation (RAG) system using n8n workflows, featuring hybrid search capabilities with multiple embedding strategies (dense, sparse, and late interaction).

## Key Features

✅ **100% Local Processing** - All operations run on your local computer
✅ **No Cloud Dependencies** - No API keys or external LLM services required
✅ **Free & Open Source** - Uses only free, locally-hosted models
✅ **Privacy-First** - Your documents never leave your machine
✅ **Contextual Chunk Enrichment** - Each chunk is enhanced with AI-generated context using local Llama 3.2
✅ **Hybrid Search** - Combines dense, sparse, and late interaction embeddings for superior retrieval

## Architecture Overview

This project combines several technologies to create a powerful RAG pipeline:

- **n8n**: Workflow automation and orchestration
- **Docling**: Document parsing and chunking
- **Ollama (Llama 3.2)**: Local LLM for contextual enrichment and chat completion
- **Ollama (nomic-embed-text)**: Dense embeddings for semantic vector representation
- **FastEmbed (BM25)**: Sparse embeddings for keyword matching
- **FastEmbed (ColBERT)**: Late interaction embeddings for contextual relevance
- **Qdrant**: Vector database for hybrid search and storage

### Models Used

| Model | Purpose | Type | Running On |
|-------|---------|------|------------|
| **llama3.2** | Contextual enrichment & chat | LLM | Ollama (local) |
| **nomic-embed-text** | Dense vector embeddings | Embedding | Ollama (local) |
| **Qdrant/bm25** | Sparse embeddings (BM25) | Embedding | FastEmbed (local) |
| **colbert-ir/colbertv2.0** | Late interaction embeddings | Embedding | FastEmbed (local) |

All models run locally - no external API calls or cloud services required.

## Services

The stack includes the following services:

| Service | Port | Description |
|---------|------|-------------|
| n8n | 5678 | Workflow orchestration platform |
| Docling | 8002 | Document parsing and chunking service |
| Ollama | 11434 | Local LLM and embedding model runtime |
| FastEmbed-BM25 | 8003 | BM25 sparse embeddings service |
| FastEmbed-ColBERT | 8004 | ColBERT late interaction embeddings |
| Qdrant | 6333 (HTTP), 6334 (gRPC) | Vector database |

## Prerequisites

- Docker and Docker Compose installed
- At least 8GB of RAM available for Docker
- Sufficient disk space for model downloads (~5GB)

## Getting Started

### 1. Start the Stack

Run all services using Docker Compose:

```bash
docker-compose up -d
```

This will start all services in detached mode. Initial startup may take several minutes as models are downloaded.

### 2. Important: HuggingFace Model Cache

**⚠️ Critical Note:** The following services require access to `/huggingface` directory to download and cache their models:

- **docling** - Downloads document parsing models (`sentence-transformers/all-MiniLM-L6-v2`)
- **fastembed-bm25** - Downloads BM25 sparse embedding model (`Qdrant/bm25`)
- **fastembed-colbert** - Downloads ColBERT model (`colbert-ir/colbertv2.0`)

The models are cached in Docker volumes to persist between container restarts:
- `fastembed_bm25_cache` → `/root/.cache/fastembed` (in fastembed-bm25 container)
- `fastembed_colbert_cache` → `/root/.cache/fastembed` (in fastembed-colbert container)

On first startup, these services will automatically download models from HuggingFace. Monitor logs to ensure successful downloads:

```bash
# Check fastembed-bm25 logs
docker logs -f fastembed-bm25

# Check fastembed-colbert logs
docker logs -f fastembed-colbert

# Check docling logs
docker logs -f docling
```

### 3. Verify Services

Check that all services are running:

```bash
docker-compose ps
```

All services should show status as "Up".

Access the web interfaces:
- n8n: http://localhost:5678
- Qdrant Dashboard: http://localhost:6333/dashboard
- Docling UI: http://localhost:8002/ui

## Workflows

The project includes two main n8n workflows:

### Workflow 1: Contextual RAG with Qdrant

**File:** `n8n/workflows/Contextual RAG Qdrant.json`

**Purpose:** Process a single document through the complete RAG pipeline with contextual chunking and vector storage.

**Services & Models Used:**
- **Docling**: Document parsing and chunking
- **Ollama (llama3.2)**: Contextual enrichment for each chunk
- **Ollama (nomic-embed-text)**: Dense vector embeddings
- **Qdrant**: Vector storage and retrieval

**Features:**
- Document parsing with Docling
- AI-powered contextual enrichment using Llama 3.2
- Dense embeddings with nomic-embed-text
- Configurable chunk size and overlap
- Vector storage in Qdrant
- Webhook-based triggering

**How to use:**

1. **Import the workflow** into n8n (http://localhost:5678)
   - Go to Workflows → Import from File
   - Select `n8n/workflows/Contextual RAG Qdrant.json`

2. **Place your document** in the n8n work directory:
   ```bash
   cp your-document.pdf n8n/work/documents/
   ```

3. **Trigger the workflow** using the provided shell script:
   ```bash
   ./curl/start_workflow.sh
   ```

   Or use curl directly:
   ```bash
   curl --location 'http://localhost:5678/webhook-test/process-document' \
   --header 'Content-Type: application/json' \
   --data '{
     "filename": "sample_tech_companies.pdf",
     "chunk_size": 512,
     "chunk_overlap": 128
   }'
   ```

**Parameters:**
- `filename`: Name of the PDF file in `n8n/work/documents/`
- `chunk_size`: Size of text chunks (default: 512)
- `chunk_overlap`: Overlap between chunks (default: 128)

### Workflow 2: Hybrid Search with Ollama

**File:** `n8n/workflows/hybrid-search-workflow-ollama.json`

**Purpose:** Create hybrid embeddings using multiple strategies and perform advanced hybrid search queries.

**Services & Models Used:**
- **Ollama (nomic-embed-text)**: Dense embeddings for semantic understanding
- **FastEmbed (Qdrant/bm25)**: Sparse embeddings for keyword matching
- **FastEmbed (colbert-ir/colbertv2.0)**: Late interaction embeddings for contextual relevance
- **Qdrant**: Vector storage with hybrid search support

**Features:**
- **Dense embeddings** via Ollama nomic-embed-text (semantic understanding)
- **Sparse embeddings** via FastEmbed-BM25 (keyword matching)
- **Late interaction embeddings** via FastEmbed-ColBERT (contextual relevance)
- Persistence in Qdrant collection with hybrid search support
- Query interface with multi-vector search

**How to use:**

1. **Import the workflow** into n8n
   - Go to Workflows → Import from File
   - Select `n8n/workflows/hybrid-search-workflow-ollama.json`

2. **Configure the workflow** (if needed):
   - Set Qdrant collection name
   - Adjust embedding model parameters
   - Configure search weights for hybrid search

3. **Run the workflow** to:
   - Index documents with all three embedding types
   - Perform hybrid search queries combining dense, sparse, and late interaction vectors

**Hybrid Search Strategy:**
The workflow combines three complementary approaches:
- **Dense (nomic-embed-text)**: Captures semantic meaning and relationships (768-dimensional vectors)
- **Sparse (BM25)**: Excels at exact keyword matching and rare terms
- **Late Interaction (ColBERT)**: Provides fine-grained token-level matching (128-dimensional multi-vectors)

## Test Document

A sample document is provided for testing:

**Location:** `n8n/work/documents/sample_tech_companies.pdf`

This document contains information about technology companies and is ideal for testing the RAG pipeline and hybrid search capabilities.

## Project Structure

```
contextual-rag/
├── docker-compose.yml              # Main orchestration file
├── curl/
│   └── start_workflow.sh          # Helper script to trigger workflow
├── n8n/
│   ├── workflows/
│   │   ├── Contextual RAG Qdrant.json
│   │   └── hybrid-search-workflow-ollama.json
│   └── work/
│       └── documents/
│           └── sample_tech_companies.pdf
├── fastembed/
│   ├── Dockerfile.bm25            # BM25 service Dockerfile
│   ├── Dockerfile.colbert         # ColBERT service Dockerfile
│   ├── app_bm25.py               # BM25 embedding service
│   ├── app_colbert.py            # ColBERT embedding service
│   └── requirements.txt
└── docling/
    ├── data/                      # Input documents
    └── output/                    # Processed output
```

## Configuration
n8n node `Init constants` and `Init chat constants` in the `Contextual RAG Qdrant.json` have configuration 
values for services base urls and some initial values. 

### Environment Variables

Key environment variables can be adjusted in `docker-compose.yml`:

**Docling:**
- `DOCLING_CHUNKING_STRATEGY`: Strategy for chunking (default: `hybrid`)
- `DOCLING_CHUNK_SIZE`: Default chunk size (default: `200`)
- `DOCLING_CHUNK_OVERLAP`: Default overlap (default: `50`)

**FastEmbed Services:**
- `MODEL_NAME`: Embedding model to use
- `LOG_LEVEL`: Logging verbosity

**n8n:**
- `N8N_BLOCK_FILE_ACCESS_TO_N8N_FILES`: Set to `false` to allow workflow file access
- `N8N_FILE_ACCESS_ALLOW_LIST`: Directories accessible to workflows

### Ollama Models

The workflows require specific Ollama models. Pull them using these commands:

**Required for embeddings (Workflow 1 & 2):**
```bash
docker exec -it ollama ollama pull nomic-embed-text
```
This model generates 768-dimensional dense embeddings for semantic search.

**Required for contextual enrichment (Workflow 1):**
```bash
docker exec -it ollama ollama pull llama3.2
```
This model generates contextual summaries for each chunk, improving retrieval accuracy.

**Optional for chat/completion:**
```bash
docker exec -it ollama ollama pull llama3.2
```
Use this if you want to add chat completion capabilities to your workflows.

## Contextual Enrichment

This project implements **Contextual Retrieval**, an approach developed by Anthropic to significantly improve RAG accuracy by enriching each document chunk with relevant context before embedding.

### How It Works

Traditional RAG systems chunk documents and embed them directly, which can lose important context. This project enhances each chunk by:

1. **Context Generation**: For each chunk, the local Llama 3.2 model generates a succinct context that situates the chunk within the overall document
2. **Enhanced Embedding**: The chunk plus its generated context are embedded together
3. **Improved Retrieval**: Search queries can now match against both the chunk content and its contextual summary

### The Contextual Prompt

Each chunk is processed using the following prompt (from [Anthropic's Contextual Retrieval guide](https://www.anthropic.com/engineering/contextual-retrieval)):

```xml
<document>
{{WHOLE_DOCUMENT}}
</document>

Here is the chunk we want to situate within the whole document
<chunk>
{{CHUNK_CONTENT}}
</chunk>

Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else.
```

### Benefits

- **Better Semantic Understanding**: Chunks retain their relationship to the broader document
- **Improved Search Accuracy**: Queries match more relevant chunks even when key terms appear only in context
- **No External Dependencies**: All processing uses the local Llama 3.2 model
- **Privacy Preserved**: Document contents never leave your machine

### Example

**Original Chunk:**
```
The company reported $2.5B in revenue for Q4.
```

**Enriched Chunk with Context:**
```
Context: This financial data pertains to Apple Inc.'s fiscal year 2023 fourth quarter earnings.

The company reported $2.5B in revenue for Q4.
```

The enriched version makes it clear which company and time period are being discussed, dramatically improving retrieval accuracy.

## Usage Examples

### Example 1: Process a Custom Document

1. Add your PDF to the documents folder:
   ```bash
   cp my-research-paper.pdf n8n/work/documents/
   ```

2. Modify the curl command in `curl/start_workflow.sh`:
   ```bash
   curl --location 'http://localhost:5678/webhook-test/process-document' \
   --header 'Content-Type: application/json' \
   --data '{
     "filename": "my-research-paper.pdf",
     "chunk_size": 1024,
     "chunk_overlap": 256
   }'
   ```

3. Execute the script:
   ```bash
   ./curl/start_workflow.sh
   ```

### Example 2: Query with Hybrid Search

After indexing documents with the hybrid search workflow:

1. Open n8n workflow
2. Trigger the search node with your query
3. Results combine all three embedding strategies for optimal relevance

## Troubleshooting

### Services Not Starting

Check logs for specific services:
```bash
docker-compose logs <service-name>
```

### Model Download Issues

If FastEmbed services fail to download models:
```bash
# Check internet connectivity from container
docker exec fastembed-bm25 ping -c 3 huggingface.co

# Verify cache volume
docker volume inspect fastembed_bm25_cache
```

### Qdrant Connection Issues

Verify Qdrant is accessible:
```bash
curl http://localhost:6333/collections
```

### n8n Workflow Execution Failures

1. Check n8n logs: `docker logs -f n8n`
2. Verify webhook URL is accessible
3. Ensure file permissions on mounted volumes

## Stopping the Stack

To stop all services:
```bash
docker-compose down
```

To stop and remove volumes (⚠️ this deletes all data):
```bash
docker-compose down -v
```

## Performance Considerations

- **Initial startup**: First run takes 10-15 minutes for model downloads
- **Memory**: Allocate at least 8GB RAM to Docker
- **Disk space**: Models require ~5GB total
- **Concurrent requests**: FastEmbed services handle requests sequentially; scale by adding replicas if needed

## Support

For issues and questions:
- Check logs: `docker-compose logs -f`
- Review n8n workflow execution logs
- Verify service health: `docker-compose ps`