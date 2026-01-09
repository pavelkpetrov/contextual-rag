curl --location 'http://localhost:5678/webhook-test/process-document' \
--header 'Content-Type: application/json' \
--data '{
  "filename": "sample_tech_companies.pdf",
  "chunk_size": 512,
  "chunk_overlap": 128
}'