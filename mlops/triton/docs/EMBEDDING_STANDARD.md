# 📘 EMBEDDING_STANDARD.md
## Triton + ONNX Embedding Deployment & Inference Standard

---

## 1. Purpose

Tài liệu này định nghĩa **chuẩn kỹ thuật chính thức** cho hệ thống embedding nhằm:

- Chuẩn hoá quy trình convert model → ONNX
- Chuẩn hoá deploy & inference embedding model trên Triton
- Đảm bảo backend **ổn định, không breaking change**
- Tránh lỗi phổ biến khi dùng Optimum / ONNX / Triton
- Làm **single source of truth** cho Backend & MLOps

---

## 2. Scope

Áp dụng cho:
- Triton Inference Server
- Embedding models (Sentence-Transformers)
- Backend Python / FastAPI
- Vector DB (Milvus, FAISS, Qdrant…)

Không áp dụng cho:
- Vision models
- LLM text generation
- Training / fine-tuning pipeline

---

## 3. Repository Structure (Standard)

```
mlops/
└── triton/
    ├── model_repository/
    │   ├── embeddings/
    │   └── embeddings_onnx/
    ├── scripts/
    ├── docker-compose.onnx.yml
    ├── requirements.txt
    └── docs/
        └── EMBEDDING_STANDARD.md
```

---

## 4. Architecture Standard (MANDATORY)

```
Client
  ↓ text (STRING)
Triton Python Backend
  ↓ tokenization
ONNX Runtime
  ↓ last_hidden_state
Mean Pooling + L2 Normalization
  ↓
Embedding [768] FP32
```

---

## 5. Triton Inference Deployment (STANDARD)

### 5.1 Docker Compose – ONNX Runtime Backend

```yaml
version: '3.8'

services:
  triton-onnx:
    image: nvcr.io/nvidia/tritonserver:24.01-py3
    container_name: triton-embedding-onnx
    command: |
      tritonserver
      --model-repository=/models
      --log-verbose=1
      --strict-model-config=false
      --backend-config=onnxruntime,default-max-batch-size=32
    ports:
      - "7000:8000"  # HTTP
      - "7001:8001"  # gRPC
      - "7002:8002"  # Metrics
    volumes:
      - ./model_repository:/models
    environment:
      - CUDA_VISIBLE_DEVICES=
      - OMP_NUM_THREADS=4
      - MKL_NUM_THREADS=4
    shm_size: 2g
    ulimits:
      memlock: -1
      stack: 67108864
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7000/v2/health/ready"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G

networks:
  default:
    name: triton-onnx-network
```

### Notes
- CPU-only: để `CUDA_VISIBLE_DEVICES=` rỗng
- GPU: set `CUDA_VISIBLE_DEVICES=0` và enable `nvidia` runtime
- Port 7000 dùng cho HTTP inference (recommended)

---

## 6. Inference API Contract

### 6.1 Health Check
```bash
curl http://localhost:7000/v2/health/ready
```

### 6.2 Model Ready
```bash
curl http://localhost:7000/v2/models/embeddings_onnx/ready
```

### 6.3 Inference Request (HTTP)

```json
POST /v2/models/embeddings_onnx/infer
{
  "inputs": [
    {
      "name": "text",
      "datatype": "BYTES",
      "shape": [1],
      "data": ["Gạch ốp lát ceramic chất lượng cao"]
    }
  ]
}
```

### 6.4 Inference Response (Expected)

```json
{
  "outputs": [
    {
      "name": "embeddings",
      "datatype": "FP32",
      "shape": [1, 768],
      "data": [0.0123, 0.4567, ...]
    }
  ]
}
```

---

## 7. Performance & Runtime Rules

- Output embedding **luôn FP32**
- ONNX nội bộ có thể FP16
- Dynamic batching bật trong `config.pbtxt`
- Warmup bắt buộc để tránh cold-start

---

## 8. Golden Rules (TL;DR)

1. Python backend + ONNX Runtime
2. Input = `text`, Output = `embeddings[768]`
3. ONNX export bằng `torch.onnx.export`
4. Pooling + normalize ở backend
5. Không phá interface khi đã production

---

**Status:** Production Standard
**Last updated:** 2025-12-20
