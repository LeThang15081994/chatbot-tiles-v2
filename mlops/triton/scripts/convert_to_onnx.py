"""
Convert sentence-transformers/paraphrase-multilingual-mpnet-base-v2
to ONNX for Triton usage (WITH correct pooling)
"""

from pathlib import Path
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer


MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
OUTPUT_DIR = Path("model_repository/embeddings_onnx/1")
MAX_SEQ_LENGTH = 128


def convert_to_onnx():
    print("🔄 Converting Sentence-Transformers model to ONNX")
    print(f"   Model : {MODEL_NAME}")
    print(f"   Output: {OUTPUT_DIR.resolve()}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # -----------------------------
    # Load Sentence-Transformers
    # -----------------------------
    print("\n📥 Loading SentenceTransformer...")
    st_model = SentenceTransformer(MODEL_NAME)
    st_model.max_seq_length = MAX_SEQ_LENGTH

    # Extract components
    transformer = st_model._first_module().auto_model
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    transformer.eval()

    # -----------------------------
    # Dummy input for tracing
    # -----------------------------
    print("\n🧪 Preparing dummy input...")
    dummy = tokenizer(
        ["Xin chào thế giới"],
        padding="max_length",
        truncation=True,
        max_length=MAX_SEQ_LENGTH,
        return_tensors="pt",
    )

    # -----------------------------
    # Export transformer to ONNX
    # -----------------------------
    onnx_path = OUTPUT_DIR / "model.onnx"

    print("\n📦 Exporting ONNX (transformer encoder)...")
    torch.onnx.export(
        transformer,
        (
            dummy["input_ids"],
            dummy["attention_mask"],
        ),
        onnx_path.as_posix(),
        input_names=["input_ids", "attention_mask"],
        output_names=["last_hidden_state"],
        dynamic_axes={
            "input_ids": {0: "batch", 1: "seq"},
            "attention_mask": {0: "batch", 1: "seq"},
            "last_hidden_state": {0: "batch", 1: "seq"},
        },
        opset_version=17,
        do_constant_folding=True,
    )

    print("✅ ONNX transformer exported")

    # -----------------------------
    # Save tokenizer
    # -----------------------------
    print("\n💾 Saving tokenizer...")
    tokenizer.save_pretrained(OUTPUT_DIR)

    # -----------------------------
    # Verify ONNX model
    # -----------------------------
    print("\n🔍 Verifying ONNX model...")
    import onnxruntime as ort

    session = ort.InferenceSession(str(onnx_path), providers=['CPUExecutionProvider'])
    input_names = [i.name for i in session.get_inputs()]
    output_names = [o.name for o in session.get_outputs()]

    print(f"   Input names: {input_names}")
    print(f"   Output names: {output_names}")

    if output_names[0] != "last_hidden_state":
        print(f"   ⚠️  Warning: Expected 'last_hidden_state', got '{output_names[0]}'")
    else:
        print("   ✅ Output name correct: 'last_hidden_state'")

    # -----------------------------
    # Info
    # -----------------------------
    print("\n🧠 IMPORTANT:")
    print("   - ONNX output: last_hidden_state [B, T, 768]")
    print("   - Pooling: MEAN pooling must be done in Triton Python backend")
    print("   - This matches Sentence-Transformers behavior")
    print("   - Model uses torch.onnx.export (not Optimum)")

    print("\n🎯 Conversion SUCCESS")
    print("\n💡 Next steps:")
    print("   1. Verify: python scripts/verify_onnx.py")
    print("   2. Deploy: docker-compose -f docker-compose.onnx.yml up -d")
    return True


if __name__ == "__main__":
    try:
        convert_to_onnx()
        print("\n✅ Ready for Triton")
    except Exception as e:
        print(f"\n❌ Conversion failed: {e}")
        raise
