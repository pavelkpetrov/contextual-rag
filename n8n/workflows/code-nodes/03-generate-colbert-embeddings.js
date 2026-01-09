/**
 * n8n Code Node: Generate ColBERT Late Interaction Embeddings
 *
 * This node generates ColBERT late interaction embeddings using the local fastembed-colbert service.
 * ColBERT produces multiple vectors (one per token) for fine-grained reranking.
 *
 * Input: { text: "document content" }
 * Output: { text: "...", colbert_embedding: [[...], [...], ...] }
 */

// Generate ColBERT Embedding
const text = $input.item.json.text;

const data = await this.helpers.httpRequest({
  method: 'POST',
  url: 'http://fastembed-colbert:8000/embed/single',
  headers: { 'Content-Type': 'application/json' },
  body: { texts: text },
  json: true
});

const colbertEmbedding = data.embedding;

return {
  json: {
    ...$input.item.json,
    colbert_embedding: colbertEmbedding,
    colbert_num_vectors: colbertEmbedding.length
  }
};