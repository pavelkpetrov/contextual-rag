/**
 * n8n Code Node: Create Qdrant Collection with Multiple Vector Types
 *
 * This node creates a Qdrant collection configured for hybrid search with:
 * - Dense embeddings (semantic search)
 * - BM25 sparse embeddings (keyword search)
 * - ColBERT late interaction embeddings (reranking)
 *
 * Input: { collection_name: "my_collection" }
 * Output: { collection_name: "...", created: true }
 */
// Create Qdrant Collection
const collectionName = $input.item.json.collection_name;
const qdrantUrl = 'http://qdrant:6333';

const collectionConfig = {
  vectors: {
    dense: {
      size: 768,
      distance: 'Cosine'
    }
  },
  sparse_vectors: {
    bm25: {}
  }
};

// Check if exists
try {
  await this.helpers.httpRequest({
    method: 'GET',
    url: `${qdrantUrl}/collections/${collectionName}`,
    headers: { 'Content-Type': 'application/json' }
  });

  return { json: { collection_name: collectionName, created: false, message: 'Already exists' } };
} catch (error) {
  // Collection doesn't exist, continue to create
}

// Create collection
await this.helpers.httpRequest({
  method: 'PUT',
  url: `${qdrantUrl}/collections/${collectionName}`,
  headers: { 'Content-Type': 'application/json' },
  body: collectionConfig,
  json: true
});

return { json: { collection_name: collectionName, created: true } };