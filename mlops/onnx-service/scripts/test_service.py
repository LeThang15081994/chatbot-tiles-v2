"""
Test ONNX Embedding Service
"""
import requests
import numpy as np
from typing import List

SERVICE_URL = "http://localhost:7000"


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity"""
    a_arr = np.array(a)
    b_arr = np.array(b)
    return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))


def test_health():
    """Test health endpoint"""
    print("🏥 Testing health endpoint...")
    response = requests.get(f"{SERVICE_URL}/health")

    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Service is healthy!")
        print(f"   Model loaded: {result.get('model_loaded', False)}")
        return True
    else:
        print(f"   ❌ Service unhealthy: {response.status_code}")
        return False


def test_embedding():
    """Test embedding generation"""
    print("\n🧪 Testing embedding generation...")

    texts = [
        "Hello world",
        "Xin chào thế giới",
        "Gạch ốp lát ceramic chất lượng cao"
    ]

    response = requests.post(
        f"{SERVICE_URL}/embed",
        json={"texts": texts}
    )

    if response.status_code != 200:
        print(f"   ❌ Request failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

    result = response.json()
    embeddings = result["embeddings"]

    print(f"   ✅ Got {len(embeddings)} embeddings")
    print(f"   Dimension: {result['dimension']}")
    print(f"   Count: {result['count']}")

    # Check dimensions
    for i, emb in enumerate(embeddings):
        if len(emb) != 768:
            print(f"   ❌ Embedding {i} has wrong dimension: {len(emb)}")
            return False

    print(f"   ✅ All embeddings have correct dimension (768)")

    # Test similarity
    print(f"\n📊 Testing cross-lingual similarity...")
    sim_01 = cosine_similarity(embeddings[0], embeddings[1])
    sim_02 = cosine_similarity(embeddings[0], embeddings[2])

    print(f"   'Hello world' <-> 'Xin chào thế giới': {sim_01:.4f}")
    print(f"   'Hello world' <-> 'Gạch ceramic': {sim_02:.4f}")

    if sim_01 > 0.5:
        print(f"   ✅ Cross-lingual similarity working!")
    else:
        print(f"   ⚠️  Low cross-lingual similarity")

    return True


def test_batch():
    """Test batch processing"""
    print("\n📦 Testing batch processing...")

    texts = [
        "Gạch ốp lát phòng khách",
        "Gạch ốp lát phòng tắm",
        "Gạch ốp lát phòng bếp",
    ]

    response = requests.post(
        f"{SERVICE_URL}/embed",
        json={"texts": texts}
    )

    if response.status_code != 200:
        print(f"   ❌ Batch request failed: {response.status_code}")
        return False

    result = response.json()
    embeddings = result["embeddings"]

    print(f"   ✅ Processed {len(embeddings)} texts")
    print(f"   All embeddings normalized: {all(len(emb) == 768 for emb in embeddings)}")

    return True


if __name__ == "__main__":
    print("🚀 ONNX Embedding Service Test")
    print("=" * 60)
    print(f"Service URL: {SERVICE_URL}")
    print("=" * 60)

    try:
        # Health check
        if not test_health():
            print("\n❌ Health check failed. Is service running?")
            print("   Start with: docker-compose up -d")
            exit(1)

        # Test embedding
        if not test_embedding():
            print("\n❌ Embedding test failed")
            exit(1)

        # Test batch
        if not test_batch():
            print("\n❌ Batch test failed")
            exit(1)

        print("\n" + "=" * 60)
        print("🎉 All tests passed!")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to service!")
        print("   Make sure service is running:")
        print("   docker-compose up -d")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

