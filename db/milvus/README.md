
# Milvus Data Structure & Backup Guide

## 1. Collection: `embedding_image_gachai_v1`

### Field Descriptions:

| Field Name    | Data Type      | Meaning / Note |
|-------------- |---------------|----------------|
| image_id      | VarChar(64)   | Primary key, unique identifier for the image |
| product_id    | VarChar(32)   | Product code associated with the image |
| product_type  | VarChar(32)   | Product type, has Trie index for fast filtering |
| vector        | FloatVector(512) | 512-dim image embedding vector for similarity search, HNSW (COSINE) index |
| fileName      | VarChar(32)   | Original file name of the image |
| brand_id      | VarChar(32)   | Brand code of the product |
| is_active     | Bool          | Mark if the image is active (default: true) |
| created_at    | VarChar(32)   | Record creation time |
| updated_at    | VarChar(32)   | Record update time |

#### Indexes:
- `product_type`: Trie index (optimized for product type filtering)
- `vector`: HNSW index (optimized for vector search, COSINE metric)

## 2. Backup & Storage Structure

### Main directories:
- `backup/backup.yaml`: Milvus backup/restore configuration file

### Backup config file: `backup.yaml`
- Configure log, Milvus endpoint, MinIO, data and backup buckets
- Parallel backup parameters, keep temp files, pause GC for data safety

#### Example MinIO config:
```yaml
minio:
  storageType: "minio"
  address: milvus-minio
  port: 9000
  accessKeyID: minioadmin
  secretAccessKey: minioadmin
  bucketName: "milvus-data"
  backupBucketName: "milvus-backup"
```

### Backup/Restore Procedure:
1. Make sure Milvus, MinIO, and Etcd are running (via docker-compose)
2. Use Milvus backup script/tool, referencing `backup.yaml`
3. Backup data will be stored in the `milvus-backup` bucket on MinIO

### Further references:
- [Milvus Backup Tool](https://milvus.io/docs/backup.md)
- [Milvus Storage Architecture](https://milvus.io/docs/storage_architecture.md)

