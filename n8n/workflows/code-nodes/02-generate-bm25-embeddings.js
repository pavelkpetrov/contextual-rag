/**
 * n8n Code Node: Generate BM25 Sparse Embeddings
 *
 * This node generates BM25 sparse embeddings using the local fastembed-bm25 service.
 * Sparse embeddings are memory-efficient and great for keyword-based search.
 *
 * Input: { text: "document content" }
 * Output: { text: "...", bm25_embedding: { indices: [...], values: [...] } }
 */

// Generate BM25 Sparse Embedding
const text = $input.item.json.text;

const data = await this.helpers.httpRequest({
  method: 'POST',
  url: 'http://fastembed-bm25:8000/embed/single',
  headers: { 'Content-Type': 'application/json' },
  body: { texts: text },
  json: true
});

const bm25Embedding = data.embedding;

return {
  json: {
    ...$input.item.json,
    bm25_embedding: bm25Embedding,
    bm25_nnz: bm25Embedding.indices.length
  }
};