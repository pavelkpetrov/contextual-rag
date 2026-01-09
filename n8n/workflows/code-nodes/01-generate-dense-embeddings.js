/**
 * n8n Code Node: Generate Dense Embeddings with Ollama
 *
 * This node generates dense (semantic) embeddings using Ollama's nomic-embed-text model.
 * nomic-embed-text produces 768-dimensional embeddings and runs locally.
 *
 * Input: { text: "document content" }
 * Output: { text: "...", dense_embedding: [0.123, ...] }
 */

// Generate Dense Embedding with Ollama
const text = $input.item.json.text;

const data = await this.helpers.httpRequest({
  method: 'POST',
  url: 'http://ollama:11434/api/embeddings',
  headers: { 'Content-Type': 'application/json' },
  body: {
    model: 'nomic-embed-text',
    prompt: text
  },
  json: true
});

const denseEmbedding = data.embedding;

return {
  json: {
    ...$input.item.json,
    dense_embedding: denseEmbedding,
    dense_dimensions: denseEmbedding.length
  }
};