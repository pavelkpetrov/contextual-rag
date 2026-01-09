# n8n Hybrid Search with Reranking Workflows

This directory contains n8n code nodes and workflows for implementing hybrid search with ColBERT reranking, following the [Qdrant hybrid search tutorial](https://qdrant.tech/documentation/advanced-tutorials/reranking-hybrid-search/).

## Overview

The workflow implements a three-stage search approach:

1. **Dense Embeddings** - Semantic search using OpenAI embeddings (1536 dimensions)
2. **BM25 Sparse Embeddings** - Keyword-based search using BM25 algorithm
3. **ColBERT Late Interaction** - Fine-grained reranking using token-level embeddings

## Architecture

```
Document Text
    ↓
    ├─→ Dense Embedding (OpenAI)
    ├─→ BM25 Embedding (fastembed-bm25)
    └─→ ColBERT Embedding (fastembed-colbert)
    ↓
Qdrant Collection
    ↓
Query → [Dense + BM25 Hybrid Search] → Candidates
    ↓
ColBERT Reranking → Final Results
```

## Services Required

Ensure these services are running:

- **n8n** (localhost:5678) - Workflow automation
- **qdrant** (localhost:6333) - Vector database
- **fastembed-bm25** (localhost:8003) - BM25 embeddings
- **fastembed-colbert** (localhost:8004) - ColBERT embeddings
- **OpenAI API** - Dense embeddings (requires API key)

Start all services:
```bash
docker-compose up -d
```

## Code Nodes

Individual code nodes are available in the `code-nodes/` directory:

### 01. Generate Dense Embeddings
**File**: `01-generate-dense-embeddings.js`

Generates dense semantic embeddings using OpenAI's `text-embedding-3-small` model.

**Input**:
```json
{
  "text": "Your document content here"
}
```

**Output**:
```json
{
  "text": "Your document content here",
  "dense_embedding": [0.123, -0.456, ...],
  "dense_dimensions": 1536
}
```

**Configuration**:
- Set `OPENAI_API_KEY` environment variable in n8n
- Or modify the code to use your API key

### 02. Generate BM25 Embeddings
**File**: `02-generate-bm25-embeddings.js`

Generates sparse BM25 embeddings for keyword-based search.

**Input**:
```json
{
  "text": "Your document content here"
}
```

**Output**:
```json
{
  "text": "Your document content here",
  "bm25_embedding": {
    "indices": [12, 45, 78, ...],
    "values": [0.523, 0.312, ...]
  },
  "bm25_nnz": 42
}
```

**Service**: `http://fastembed-bm25:8000`

### 03. Generate ColBERT Embeddings
**File**: `03-generate-colbert-embeddings.js`

Generates multi-vector ColBERT embeddings for reranking.

**Input**:
```json
{
  "text": "Your document content here"
}
```

**Output**:
```json
{
  "text": "Your document content here",
  "colbert_embedding": [[0.1, 0.2, ...], [0.3, 0.4, ...], ...],
  "colbert_num_vectors": 32,
  "colbert_vector_dim": 128
}
```

**Service**: `http://fastembed-colbert:8000`

### 04. Create Qdrant Collection
**File**: `04-create-qdrant-collection.js`

Creates a Qdrant collection configured for hybrid search.

**Input**:
```json
{
  "collection_name": "my_collection"
}
```

**Collection Configuration**:
- **Dense vectors**: 1536 dimensions, Cosine distance
- **Sparse vectors**: BM25 (no size limit)

### 05. Insert Document to Qdrant
**File**: `05-insert-document-to-qdrant.js`

Inserts a document with all three embedding types into Qdrant.

**Input**:
```json
{
  "id": "doc_1",
  "text": "document content",
  "dense_embedding": [...],
  "bm25_embedding": { "indices": [...], "values": [...] },
  "colbert_embedding": [[...], [...], ...],
  "collection_name": "my_collection"
}
```

**Storage**:
- Dense & BM25: Stored as vector fields
- ColBERT: Stored in payload for reranking

### 06. Hybrid Search with Reranking
**File**: `06-hybrid-search-with-reranking.js`

Performs hybrid search with ColBERT reranking.

**Input**:
```json
{
  "query": "What is retrieval augmented generation?",
  "collection_name": "my_collection",
  "top_k": 10
}
```

**Output**:
```json
{
  "query": "What is retrieval augmented generation?",
  "num_results": 10,
  "results": [
    {
      "id": "doc_1",
      "text": "...",
      "original_score": 0.85,
      "colbert_score": 0.92,
      "final_score": 0.89
    }
  ],
  "search_method": "hybrid_with_colbert_reranking"
}
```

**Process**:
1. Generate query embeddings (dense, BM25, ColBERT)
2. Execute hybrid search using Qdrant's prefetch + fusion
3. Rerank candidates using ColBERT MaxSim scoring
4. Return top-K results

## Complete Workflow

**File**: `hybrid-search-workflow.json`

A complete end-to-end workflow demonstrating:

1. Create collection
2. Add sample document with all embeddings
3. Perform hybrid search with reranking

### Import Instructions

1. Open n8n (http://localhost:5678)
2. Go to **Workflows** → **Add Workflow** → **Import from File**
3. Select `hybrid-search-workflow.json`
4. Configure environment variables:
   - `OPENAI_API_KEY` - Your OpenAI API key
5. Click **Execute Workflow**

### Workflow Nodes

```
Manual Trigger
  ↓
Set Collection Name (collection: "hybrid_demo")
  ↓
Create Collection (Qdrant)
  ↓
Set Sample Document (RAG definition)
  ↓
Generate Dense Embedding (OpenAI)
  ↓
Generate BM25 Embedding (fastembed-bm25)
  ↓
Generate ColBERT Embedding (fastembed-colbert)
  ↓
Insert to Qdrant
  ↓
Set Search Query ("What is RAG?")
  ↓
Hybrid Search with Reranking
  ↓
Results
```

## Usage Example

### Step 1: Start Services

```bash
cd /path/to/contextual-rag
docker-compose up -d
```

Verify services:
```bash
curl http://localhost:6333/collections
curl http://localhost:8003/health
curl http://localhost:8004/health
```

### Step 2: Import Workflow

1. Import `hybrid-search-workflow.json` into n8n
2. Set `OPENAI_API_KEY` in n8n settings

### Step 3: Execute Workflow

Click **"Execute Workflow"** button in n8n

### Step 4: View Results

Check the output of the "Hybrid Search" node to see ranked results.

## Customization

### Using Different Models

**Dense Embeddings**:
```javascript
// Change OpenAI model
model: 'text-embedding-3-large'  // 3072 dimensions

// Or use local model (requires additional service)
// model: 'sentence-transformers/all-MiniLM-L6-v2'
```

Update collection configuration if dimensions change.

**BM25 Parameters**:
The BM25 model is pre-configured. To adjust parameters, modify the fastembed service.

**ColBERT Reranking**:
Adjust the scoring weights in the search node:
```javascript
final_score: candidate.score * 0.4 + colbertRelevance * 0.6
//                          ↑ hybrid weight    ↑ reranking weight
```

### Processing Multiple Documents

Use n8n's **Split In Batches** node:

```
Read Documents
  ↓
Split In Batches (batch size: 10)
  ↓
Generate Embeddings (all 3 types)
  ↓
Insert to Qdrant
  ↓
Loop until done
```

### Adding Metadata

Modify the insert node to include metadata:

```javascript
payload: {
  text: inputData.text,
  colbert_embedding: inputData.colbert_embedding,
  metadata: {
    source: inputData.source,
    category: inputData.category,
    timestamp: new Date().toISOString(),
    author: inputData.author
  }
}
```

## Advanced Features

### Filtered Search

Add filters to the search query:

```javascript
const searchQuery = {
  query: { fusion: 'rrf' },
  prefetch: [...],
  filter: {
    must: [
      {
        key: 'metadata.category',
        match: { value: 'technical' }
      }
    ]
  },
  limit: topK * 2,
  with_payload: true
};
```

### Adjusting Fusion Strategy

Change the fusion method:

```javascript
query: {
  fusion: 'rrf'  // Options: 'rrf' (Reciprocal Rank Fusion)
}
```

### Custom Reranking

Implement different reranking strategies:

```javascript
// Option 1: Use only ColBERT (ignore hybrid score)
final_score: colbertRelevance

// Option 2: Weighted combination
final_score: hybridScore * 0.3 + colbertScore * 0.7

// Option 3: Maximum score
final_score: Math.max(hybridScore, colbertScore)
```

## Performance Tips

1. **Batch Processing**: Process documents in batches (10-50) for better throughput
2. **Candidate Count**: Use `topK * 2` or `topK * 3` candidates for reranking
3. **Caching**: Enable n8n's caching for frequently used queries
4. **Async Operations**: Use n8n's **Execute Workflow** node for parallel processing

## Troubleshooting

### Services Not Responding

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs fastembed-bm25
docker-compose logs fastembed-colbert

# Restart services
docker-compose restart fastembed-bm25 fastembed-colbert
```

### Collection Already Exists Error

Delete the collection first:
```bash
curl -X DELETE http://localhost:6333/collections/hybrid_demo
```

### OpenAI API Errors

- Verify API key is set correctly
- Check rate limits and quota
- Try using a different model

### Empty Search Results

- Verify documents were inserted successfully
- Check that embeddings are not null
- Inspect Qdrant collection: `curl http://localhost:6333/collections/hybrid_demo`

## References

- [Qdrant Hybrid Search Tutorial](https://qdrant.tech/documentation/advanced-tutorials/reranking-hybrid-search/)
- [FastEmbed Documentation](https://qdrant.github.io/fastembed/)
- [n8n Code Node Documentation](https://docs.n8n.io/code-examples/)
- [ColBERT Paper](https://arxiv.org/abs/2004.12832)

## Examples

### Example 1: Simple Document Indexing

```javascript
// In n8n Code Node
const documents = [
  { id: 'doc1', text: 'Machine learning is...' },
  { id: 'doc2', text: 'Neural networks are...' },
  { id: 'doc3', text: 'Deep learning involves...' }
];

const results = [];

for (const doc of documents) {
  // Generate embeddings for each document
  // (Use separate nodes for each embedding type)
  results.push({
    id: doc.id,
    text: doc.text
  });
}

return results.map(r => ({ json: r }));
```

### Example 2: Batch Search

```javascript
// In n8n Code Node
const queries = [
  'What is machine learning?',
  'Explain neural networks',
  'How does deep learning work?'
];

const allResults = [];

for (const query of queries) {
  // Perform search for each query
  const results = await hybridSearch(query);
  allResults.push({
    query: query,
    results: results
  });
}

return allResults.map(r => ({ json: r }));
```

## License

This workflow is provided as-is for educational and commercial use.