/**
 * n8n Code Node: Insert Document with All Embeddings into Qdrant
 *
 * This node inserts a document into Qdrant with all three embedding types:
 * - Dense embeddings
 * - BM25 sparse embeddings
 * - ColBERT embeddings (stored in payload for reranking)
 *
 * Input: {
 *   id: "doc_1",
 *   text: "document content",
 *   dense_embedding: [...],
 *   bm25_embedding: { indices: [...], values: [...] },
 *   colbert_embedding: [[...], [...]]
 * }
 * Output: { id: "doc_1", inserted: true }
 */

const inputData = $input.item.json;
const collectionName = inputData.collection_name || 'hybrid_search_collection';
const qdrantUrl = 'http://qdrant:6333';

// Validate required fields
if (!inputData.id || !inputData.text) {
  throw new Error('Missing required fields: id and text');
}

// Prepare point for Qdrant
const point = {
  id: inputData.id,
  vector: {
    dense: inputData.dense_embedding,
    bm25: {
      indices: inputData.bm25_embedding.indices,
      values: inputData.bm25_embedding.values
    }
  },
  payload: {
    text: inputData.text,
    colbert_embedding: inputData.colbert_embedding || null,
    metadata: inputData.metadata || {},
    timestamp: new Date().toISOString()
  }
};

const requestBody = { points: [point] };

// LOG THE JSON TO CONSOLE
console.log('Sending JSON to Qdrant:', JSON.stringify(requestBody, null, 2));

// Insert point into Qdrant
try {
  const result = await this.helpers.httpRequest({
    method: 'PUT',
    url: `${qdrantUrl}/collections/${collectionName}/points?wait=true`,
    body: requestBody,
    json: true
  });

  return {
    json: {
      id: inputData.id,
      collection_name: collectionName,
      inserted: true,
      result: result
    }
  };
} catch (error) {
  // Log the error response body which often contains the specific Qdrant error message
  console.error('Qdrant Error Response:', error.response?.data || error.message);
  throw error;
}