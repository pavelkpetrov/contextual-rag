/**
 * n8n Code Node: Hybrid Search with ColBERT Reranking
 *
 * This node performs a hybrid search combining:
 * 1. Dense vector search (semantic similarity)
 * 2. BM25 sparse search (keyword matching)
 * 3. ColBERT reranking (fine-grained relevance scoring)
 *
 * Input: { query: "search query" }
 * Output: { query: "...", results: [...], scores: [...] }
 */

// Hybrid Search with Reranking
const query = $input.item.json.query;
const collectionName = $input.item.json.collection_name || 'hybrid_demo';
const topK = $input.item.json.top_k || 3;
const qdrantUrl = 'http://qdrant:6333';

// Generate query embeddings with Ollama
const denseData = await this.helpers.httpRequest({
  method: 'POST',
  url: 'http://host.docker.internal:11434/api/embeddings',
  headers: { 'Content-Type': 'application/json' },
  body: { model: 'nomic-embed-text', prompt: query },
  json: true
});
const queryDense = denseData.embedding;

// BM25
const bm25Data = await this.helpers.httpRequest({
  method: 'POST',
  url: 'http://fastembed-bm25:8000/embed/single',
  headers: { 'Content-Type': 'application/json' },
  body: { texts: query },
  json: true
});
const queryBm25 = bm25Data.embedding;

// ColBERT
const colbertData = await this.helpers.httpRequest({
  method: 'POST',
  url: 'http://fastembed-colbert:8000/embed/single',
  headers: { 'Content-Type': 'application/json' },
  body: { texts: query },
  json: true
});
const queryColbert = colbertData.embedding;

// Hybrid search
const searchData = await this.helpers.httpRequest({
  method: 'POST',
  url: `${qdrantUrl}/collections/${collectionName}/points/query`,
  headers: { 'Content-Type': 'application/json' },
  body: {
    query: { fusion: 'rrf' },
    prefetch: [
      { query: queryDense, using: 'dense', limit: topK * 5 }, // Increased prefetch for better reranking
      { query: { indices: queryBm25.indices, values: queryBm25.values }, using: 'bm25', limit: topK * 5 }
    ],
    limit: topK * 5, // Get more candidates for the ColBERT reranker to work with
    with_payload: true
  },
  json: true
});

// FIX: Access the .points array from the result object
const candidates = searchData.result && searchData.result.points ? searchData.result.points : [];

// ColBERT reranking function
function colbertScore(qVecs, dVecs) {
  let total = 0;
  for (const qv of qVecs) {
    let maxSim = -Infinity;
    for (const dv of dVecs) {
      let dot = 0, qNorm = 0, dNorm = 0;
      for (let i = 0; i < qv.length; i++) {
        dot += qv[i] * dv[i];
        qNorm += qv[i] * qv[i];
        dNorm += dv[i] * dv[i];
      }
      const denom = Math.sqrt(qNorm) * Math.sqrt(dNorm);
      const sim = denom === 0 ? 0 : dot / denom;
      maxSim = Math.max(maxSim, sim);
    }
    total += maxSim;
  }
  return total / qVecs.length;
}

const results = candidates
  .filter(c => c.payload && c.payload.colbert_embedding)
  .map(c => {
    const colbScore = colbertScore(queryColbert, c.payload.colbert_embedding);
    return {
      id: c.id,
      text: c.payload.text,
      hybrid_score: c.score, // This is the RRF score
      colbert_score: colbScore,
      final_score: (c.score * 0.4) + (colbScore * 0.6)
    };
  })
  .sort((a, b) => b.final_score - a.final_score)
  .slice(0, topK);

return {
  json: {
    query,
    results,
    method: 'hybrid_with_colbert_reranking',
    num_candidates: candidates.length,
    num_results: results.length
  }
};