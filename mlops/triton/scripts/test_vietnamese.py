"""
Test Vietnamese & Cross-lingual Support
Direct ONNX Runtime testing (no Triton server needed)
Tests with Vietnamese text using local ONNX model
"""

from pathlib import Path
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer

MODEL_DIR = Path("model_repository/embeddings_onnx/1")
ONNX_PATH = MODEL_DIR / "model.onnx"
MAX_LENGTH = 128

# Global session and tokenizer (loaded once)
_session = None
_tokenizer = None


def load_model():
    """Load ONNX model and tokenizer"""
    global _session, _tokenizer

    if _session is None:
        if not ONNX_PATH.exists():
            raise FileNotFoundError(
                f"ONNX model not found: {ONNX_PATH}\n"
                f"Run: python scripts/convert_to_onnx.py"
            )

        print(f"📥 Loading ONNX model: {ONNX_PATH}")
        _session = ort.InferenceSession(
            str(ONNX_PATH),
            providers=['CPUExecutionProvider']
        )
        print(f"   ✅ ONNX model loaded")
        print(f"   Input names: {[i.name for i in _session.get_inputs()]}")
        print(f"   Output names: {[o.name for o in _session.get_outputs()]}")

    if _tokenizer is None:
        print(f"📥 Loading tokenizer from: {MODEL_DIR}")
        _tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
        print(f"   ✅ Tokenizer loaded")

    return _session, _tokenizer


def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors"""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def mean_pooling(hidden_states, attention_mask):
    """Mean pooling with attention mask"""
    input_mask_expanded = np.expand_dims(attention_mask, axis=-1)
    sum_embeddings = np.sum(hidden_states * input_mask_expanded, axis=1)
    sum_mask = np.clip(input_mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
    return sum_embeddings / sum_mask


def get_embeddings(texts):
    """
    Get embeddings for text strings using local ONNX model

    Args:
        texts: List of text strings (Vietnamese or English)

    Returns:
        embeddings: numpy array of shape (batch_size, 768)
    """
    session, tokenizer = load_model()

    # Tokenize
    inputs = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=MAX_LENGTH,
        return_tensors="np"
    )

    # Run ONNX inference
    ort_inputs = {
        "input_ids": inputs["input_ids"].astype(np.int64),
        "attention_mask": inputs["attention_mask"].astype(np.int64)
    }

    # Get hidden states from ONNX
    outputs = session.run(["last_hidden_state"], ort_inputs)
    hidden_states = outputs[0]  # [batch, seq_len, 768]

    # Mean pooling
    embeddings = mean_pooling(hidden_states, inputs["attention_mask"])

    # Normalize
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / norms

    return embeddings.astype(np.float32)


def test_cross_lingual():
    """Test cross-lingual similarity between Vietnamese and English"""
    print("\n🌍 Cross-lingual Vietnamese ↔ English")
    print("=" * 60)

    cases = [
        ("Gạch ốp lát ceramic chất lượng cao", "High quality ceramic tiles"),
        ("Gạch phòng tắm chống trơn", "Non-slip bathroom tiles"),
        ("Sản phẩm gạch ốp lát hiện đại", "Modern tile products"),
        ("Gạch men sứ cao cấp", "Premium porcelain tiles"),
        ("Hướng dẫn lắp đặt gạch", "Tile installation guide"),
    ]

    similarities = []

    for i, (vi, en) in enumerate(cases, 1):
        print(f"\n🧪 Test Case {i}")
        print(f"   🇻🇳 Vietnamese: {vi}")
        print(f"   🇬🇧 English:    {en}")

        # Get embeddings from ONNX model
        embeddings = get_embeddings([vi, en])

        print(f"   📊 Embeddings shape: {embeddings.shape}")
        print(f"   ✅ Expected: (2, 768)")

        # Calculate similarity
        sim = cosine_similarity(embeddings[0], embeddings[1])
        similarities.append(sim)
        print(f"   📈 Similarity: {sim:.4f}")

        if sim > 0.75:
            print("   ✅ Excellent cross-lingual match!")
        elif sim > 0.60:
            print("   👍 Good cross-lingual match")
        elif sim > 0.40:
            print("   ⚠️  Moderate similarity")
        else:
            print("   ❌ Low similarity - may need review")

    # Summary
    avg_sim = np.mean(similarities)
    print(f"\n📊 Summary:")
    print(f"   Average similarity: {avg_sim:.4f}")
    print(f"   Min similarity: {min(similarities):.4f}")
    print(f"   Max similarity: {max(similarities):.4f}")

    if avg_sim > 0.70:
        print("   ✅ Excellent Vietnamese-English cross-lingual support!")
    elif avg_sim > 0.55:
        print("   👍 Good cross-lingual support")
    else:
        print("   ⚠️  Cross-lingual support may need improvement")


def test_vietnamese_semantic():
    """Test Vietnamese semantic similarity within same domain"""
    print("\n🇻🇳 Vietnamese Semantic Similarity")
    print("=" * 60)

    base = "Gạch ốp lát ceramic"
    samples = [
        ("Gạch ceramic ốp lát", "Very similar (word order)"),
        ("Gạch men sứ cao cấp", "Similar (same domain)"),
        ("Sản phẩm xây dựng", "Related (construction)"),
        ("Điện thoại di động", "Unrelated (phone)"),
    ]

    print(f"\n📌 Base text: '{base}'")
    print(f"\n🔍 Comparing with:")

    # Get all embeddings
    texts = [base] + [s[0] for s in samples]
    embeddings = get_embeddings(texts)

    print(f"   Embeddings shape: {embeddings.shape}")
    print(f"   ✅ Expected: ({len(texts)}, 768)")

    base_emb = embeddings[0]

    print(f"\n📊 Similarity Results:")
    for i, (text, description) in enumerate(samples, 1):
        sim = cosine_similarity(base_emb, embeddings[i])
        status = "✅" if sim > 0.5 else "⚠️" if sim > 0.3 else "❌"
        print(f"   {i}. '{text}'")
        print(f"      Similarity: {sim:.4f} {status} ({description})")

    # Check semantic understanding
    very_similar = cosine_similarity(base_emb, embeddings[1])  # Word order
    similar = cosine_similarity(base_emb, embeddings[2])  # Same domain
    unrelated = cosine_similarity(base_emb, embeddings[4])  # Unrelated

    print(f"\n🧠 Semantic Understanding Check:")
    if very_similar > similar > unrelated:
        print(f"   ✅ Correct semantic hierarchy!")
        print(f"      Very similar ({very_similar:.4f}) > Similar ({similar:.4f}) > Unrelated ({unrelated:.4f})")
    else:
        print(f"   ⚠️  Semantic hierarchy may need review")


def test_vietnamese_batch():
    """Test batch processing with Vietnamese texts"""
    print("\n📦 Vietnamese Batch Processing")
    print("=" * 60)

    texts = [
        "Gạch ốp lát phòng khách",
        "Gạch ốp lát phòng tắm",
        "Gạch ốp lát phòng bếp",
        "Gạch ốp lát sân vườn",
        "Gạch ốp lát ban công",
    ]

    print(f"\n📝 Processing {len(texts)} Vietnamese texts...")
    for i, text in enumerate(texts, 1):
        print(f"   {i}. {text}")

    # Get embeddings
    embeddings = get_embeddings(texts)

    print(f"\n✅ Batch processing successful!")
    print(f"   Embeddings shape: {embeddings.shape}")
    print(f"   Expected: ({len(texts)}, 768)")

    # Check that all embeddings are normalized
    norms = np.linalg.norm(embeddings, axis=1)
    print(f"\n🔍 Normalization check:")
    print(f"   Norms: {norms}")
    if np.allclose(norms, 1.0, atol=1e-5):
        print("   ✅ All embeddings are normalized (L2 norm ≈ 1.0)")
    else:
        print("   ⚠️  Some embeddings may not be normalized")

    # Test similarity within batch
    print(f"\n📊 Similarity within batch:")
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            print(f"   '{texts[i][:20]}...' <-> '{texts[j][:20]}...': {sim:.4f}")


if __name__ == "__main__":
    print("🚀 Vietnamese Embedding Test Suite (Direct ONNX)")
    print("=" * 60)
    print(f"Model: {ONNX_PATH}")
    print(f"Mode: Direct ONNX Runtime (no Triton server needed)")
    print("=" * 60)

    # Check ONNX file exists
    print("\n🔍 Checking ONNX model...")
    if not ONNX_PATH.exists():
        print(f"   ❌ ONNX model not found: {ONNX_PATH}")
        print(f"   💡 Run: python scripts/convert_to_onnx.py")
        exit(1)
    print(f"   ✅ ONNX model found: {ONNX_PATH}")

    # Check tokenizer files
    tokenizer_files = ["tokenizer_config.json", "vocab.txt"]
    missing = [f for f in tokenizer_files if not (MODEL_DIR / f).exists()]
    if missing:
        print(f"   ⚠️  Missing tokenizer files: {missing}")
        print(f"   💡 Run: python scripts/convert_to_onnx.py")
    else:
        print(f"   ✅ Tokenizer files found")

    # Load model once (will be reused in tests)
    print("\n📥 Initializing model...")
    try:
        load_model()
        print("   ✅ Model ready for testing!")
    except Exception as e:
        print(f"   ❌ Failed to load model: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

    # Run tests
    print("\n" + "=" * 60)
    try:
        test_cross_lingual()
        test_vietnamese_semantic()
        test_vietnamese_batch()

        print("\n" + "=" * 60)
        print("🎉 All Vietnamese tests completed successfully!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
