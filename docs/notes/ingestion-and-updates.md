# Learning Notes: Ingestion & Incremental Updates

These notes capture the technical findings and engineering decisions behind the ingestion and update components.

---

## Ingestion & File Filtering

*   **Filter Logic**: Codebase files are filtered in `should_ingest_file` based on extensions and blacklisted directories (e.g. ignoring `.git`, `node_modules`, `.venv`, and binary assets like `.png` or `.pdf`).
*   **Chunking strategy**: Uses a factory pattern to select a chunker. The default is `document_aware`, which splits text files into logical code blocks and attaches document parent IDs.

---

## Git Blob SHA-based Incremental Syncing

A naive approach to repository syncing deletes everything and re-ingests. However, generating semantic embeddings via APIs (like Voyage AI) has costs and rate limits. 

We implemented a **SHA-based incremental sync** utilizing GitHub's Git Tree API:
1.  GitHub's tree API returns a unique `sha` (Git blob SHA) for each file in the repository tree.
2.  During initial ingestion, we save this `sha` string in the `Document.content_hash` database column.
3.  During updates, we fetch the remote tree and retrieve existing database documents.
4.  By comparing the remote `sha` directly with the stored `content_hash` in memory, we categorize files:
    *   **Unchanged**: Remote SHA matches DB. **We skip chunking and embedding entirely**, saving API credits and network latency.
    *   **Modified/New**: Path exists with different SHA or is new. We delete the old document record (cascading chunk deletions automatically) and fetch the new content.
    *   **Deleted**: Document exists in DB but is no longer in the remote tree. We delete the document from the DB.
5.  After updates are complete, we run the `EmbeddingService` on the newly created chunks only.
