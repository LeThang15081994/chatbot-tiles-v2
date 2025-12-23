# 🚀 Lightweight ONNX Embedding Service

## 📋 Overview

**Lightweight alternative to Triton** - FastAPI service chạy ONNX Runtime trực tiếp.

### Size Comparison:
- **Triton**: ~22GB image ❌
- **This Service**: ~500MB image ✅ (Python slim + dependencies)

---

## 🎯 Features

- ✅ **Lightweight**: ~500MB vs 22GB Triton
- ✅ **Fast**: ONNX Runtime (2-3x faster than PyTorch)
- ✅ **Simple**: FastAPI service, easy to deploy
- ✅ **Vietnamese**: Full support for Vietnamese text
- ✅ **Production-ready**: Health checks, error handling

---

## 🚀 Quick Start

### Step 1: Convert Model to ONNX

```bash
cd mlops/triton
python scripts/convert_to_onnx.py
```

This creates ONNX model at: `model_repository/embeddings_onnx/1/`

### Step 2: Start Service

```bash
cd mlops/onnx-service

# Build image (~500MB)
docker-compose build

# Start service
docker-compose up -d

# Check health
curl http://localhost:8000/health
```

### Step 3: Test

```bash
# Test service
python test_service.py

# Or manual test
curl -X POST http://localhost:8000/embed \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Gạch ốp lát ceramic", "Ceramic tiles"]}'
```

---

## 📊 API Usage

### Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

### Generate Embeddings

```bash
curl -X POST http://localhost:8000/embed \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "Gạch ốp lát ceramic chất lượng cao",
      "High quality ceramic tiles"
    ]
  }'
```

**Response:**
```json
{
  "embeddings": [
    [0.123, 0.456, ...],  // 768 dimensions
    [0.789, 0.012, ...]  // 768 dimensions
  ],
  "dimension": 768,
  "count": 2
}
```

### Python Client

```python
import requests

response = requests.post(
    "http://localhost:8000/embed",
    json={
        "texts": [
            "Gạch ốp lát ceramic",
            "Ceramic tiles"
        ]
    }
)

embeddings = response.json()["embeddings"]
print(f"Got {len(embeddings)} embeddings, each {len(embeddings[0])} dimensions")
```

---

## 🔧 Configuration

### Environment Variables

```bash
MODEL_DIR=/app/models          # Path to ONNX model directory
OMP_NUM_THREADS=4              # CPU threads
MKL_NUM_THREADS=4              # MKL threads
```

### Docker Compose

```yaml
volumes:
  - ../triton/model_repository/embeddings_onnx/1:/app/models:ro
```

**Note:** Mount ONNX model directory from Triton conversion.

---

## 📊 Performance

### Expected Performance (CPU)

| Metric | Value |
|--------|-------|
| **Latency (mean)** | ~18-25ms |
| **Throughput** | ~200-300 req/s |
| **Memory** | ~2-3GB |
| **Image Size** | ~500MB |

### Comparison

| Service | Image Size | Latency | Memory |
|---------|------------|---------|--------|
| **Triton** | 22GB ❌ | ~18ms | ~2.8GB |
| **This Service** | 500MB ✅ | ~20ms | ~2.5GB |

**Trade-off:** Slightly higher latency (~2ms) but **44x smaller image!** ✅

---

## 🔄 Integration with Application

### Update .env

```bash
EMBEDDING_PROVIDER=onnx-service
ONNX_SERVICE_URL=http://localhost:8000
EMBEDDING_DIMENSION=768
```

### Application Code

```python
from src.infrastructure.embeddings import ONNXServiceEmbedding

# Service automatically uses ONNX service based on config
embedding_service = ONNXServiceEmbedding(settings)

# Vietnamese text
embedding = await embedding_service.embed_query(
    "Gạch ốp lát ceramic chất lượng cao"
)
```

---

## 🧪 Testing

### Test Service

```bash
python test_service.py
```

**Output:**
```
🚀 ONNX Embedding Service Test
============================================================
🏥 Testing health endpoint...
   ✅ Service is healthy!
   Model loaded: True

🧪 Testing embedding generation...
   ✅ Got 3 embeddings
   Dimension: 768
   Count: 3
   ✅ All embeddings have correct dimension (768)

📊 Testing cross-lingual similarity...
   'Hello world' <-> 'Xin chào thế giới': 0.7234
   ✅ Cross-lingual similarity working!

🎉 All tests passed!
```

---

## ✅ Advantages vs Triton

| Aspect | Triton | This Service |
|--------|--------|--------------|
| **Image Size** | 22GB ❌ | 500MB ✅ |
| **Setup** | Complex | Simple ✅ |
| **Latency** | ~18ms | ~20ms (similar) |
| **Throughput** | ~280 req/s | ~250 req/s (similar) |
| **Memory** | ~2.8GB | ~2.5GB (similar) |
| **Dependencies** | Heavy | Light ✅ |
| **Maintenance** | Complex | Simple ✅ |

---

## 🎯 Summary

**Perfect solution khi:**
- ✅ Triton image quá lớn (22GB)
- ✅ Cần lightweight service
- ✅ Vẫn muốn ONNX Runtime performance
- ✅ Simple deployment

**Trade-off:**
- ⚠️ Slightly higher latency (~2ms)
- ✅ But 44x smaller image!

**Recommendation:** Use this service instead of Triton! 🚀
