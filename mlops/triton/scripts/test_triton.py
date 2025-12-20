"""
Test Triton Inference Server
"""
import requests
import numpy as np
import json

TRITON_URL = "http://localhost:8000"

def test_health():
    """Test server health"""
    print("🏥 Testing server health...")
    response = requests.get(f"{TRITON_URL}/v2/health/ready")
    if response.status_code == 200:
        print("✅ Server is ready!")
    else:
        print(f"❌ Server not ready: {response.status_code}")
        return False
    return True

def test_model_ready():
    """Test model availability"""
    print("\n🔍 Testing model availability...")
    response = requests.get(f"{TRITON_URL}/v2/models/embeddings/ready")
    if response.status_code == 200:
        print("✅ Model is ready!")
    else:
        print(f"❌ Model not ready: {response.status_code}")
        return False
    return True

def test_inference():
    """Test inference"""
    print("\n🧪 Testing inference...")

    # Test texts
    texts = [
        "Hello world",
        "Natural language processing",
        "Machine learning is awesome"
    ]

    # Prepare request
    payload = {
        "inputs": [{
            "name": "text",
            "datatype": "BYTES",
            "shape": [len(texts)],
            "data": texts
        }]
    }

    # Send request
    response = requests.post(
        f"{TRITON_URL}/v2/models/embeddings/infer",
        json=payload
    )

    if response.status_code == 200:
        result = response.json()
        embeddings = np.array(result["outputs"][0]["data"])
        embeddings = embeddings.reshape(len(texts), 768)

        print("✅ Inference successful!")
        print(f"   - Input texts: {len(texts)}")
        print(f"   - Output shape: {embeddings.shape}")
        print(f"   - Embedding sample (first 5 dims): {embeddings[0, :5]}")

        # Test similarity
        from numpy.linalg import norm

        def cosine_similarity(a, b):
            return np.dot(a, b) / (norm(a) * norm(b))

        sim_01 = cosine_similarity(embeddings[0], embeddings[1])
        sim_02 = cosine_similarity(embeddings[0], embeddings[2])
        sim_12 = cosine_similarity(embeddings[1], embeddings[2])

        print(f"\n📊 Similarity scores:")
        print(f"   - Text 0 vs Text 1: {sim_01:.4f}")
        print(f"   - Text 0 vs Text 2: {sim_02:.4f}")
        print(f"   - Text 1 vs Text 2: {sim_12:.4f}")

        return True
    else:
        print(f"❌ Inference failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_model_stats():
    """Test model statistics"""
    print("\n📊 Getting model statistics...")
    response = requests.get(f"{TRITON_URL}/v2/models/embeddings/stats")
    if response.status_code == 200:
        stats = response.json()
        print("✅ Model statistics:")
        print(json.dumps(stats, indent=2))
    else:
        print(f"❌ Failed to get stats: {response.status_code}")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Triton Inference Server Test Suite")
    print("=" * 60)

    if not test_health():
        print("\n❌ Server health check failed. Is Triton running?")
        print("   Start with: docker-compose up -d")
        exit(1)

    if not test_model_ready():
        print("\n❌ Model not loaded. Check Triton logs.")
        exit(1)

    if not test_inference():
        print("\n❌ Inference test failed.")
        exit(1)

    test_model_stats()

    print("\n" + "=" * 60)
    print("🎉 All tests passed!")
    print("=" * 60)

