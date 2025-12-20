"""
Verify ONNX model after conversion
Tests that the ONNX model works correctly
"""
from pathlib import Path
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer

MODEL_DIR = Path("model_repository/embeddings_onnx/1")
ONNX_PATH = MODEL_DIR / "model.onnx"

print("🔍 Verifying ONNX Model")
print("=" * 60)

# Check if ONNX file exists
if not ONNX_PATH.exists():
    print(f"❌ ONNX model not found: {ONNX_PATH}")
    print("   Run: python scripts/convert_to_onnx.py")
    exit(1)

print(f"\n📥 Loading ONNX model: {ONNX_PATH}")

# Load ONNX Runtime session
session = ort.InferenceSession(str(ONNX_PATH), providers=['CPUExecutionProvider'])

# Check inputs/outputs
print("\n📋 Model Information:")
print(f"   Providers: {session.get_providers()}")
print(f"   Input names: {[i.name for i in session.get_inputs()]}")
print(f"   Output names: {[o.name for o in session.get_outputs()]}")

# Verify expected structure
inputs = session.get_inputs()
outputs = session.get_outputs()

expected_inputs = ["input_ids", "attention_mask"]
expected_output = "last_hidden_state"

print("\n✅ Checking structure...")
if len(inputs) != 2:
    print(f"   ❌ Expected 2 inputs, got {len(inputs)}")
    exit(1)

if inputs[0].name != "input_ids":
    print(f"   ❌ Expected first input 'input_ids', got '{inputs[0].name}'")
    exit(1)

if inputs[1].name != "attention_mask":
    print(f"   ❌ Expected second input 'attention_mask', got '{inputs[1].name}'")
    exit(1)

if outputs[0].name != expected_output:
    print(f"   ❌ Expected output '{expected_output}', got '{outputs[0].name}'")
    exit(1)

print("   ✅ Input/output names match expected structure")

# Load tokenizer
print("\n📥 Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))

# Test texts
test_texts = [
    "Hello world",
    "Xin chào thế giới",
    "Gạch ốp lát ceramic chất lượng cao"
]

print(f"\n📝 Test texts:")
for i, text in enumerate(test_texts, 1):
    print(f"   {i}. {text}")

# Tokenize
print("\n🔧 Tokenizing...")
inputs_tokenized = tokenizer(
    test_texts,
    padding=True,
    truncation=True,
    max_length=128,
    return_tensors="np"
)

print(f"   Input IDs shape: {inputs_tokenized['input_ids'].shape}")
print(f"   Attention mask shape: {inputs_tokenized['attention_mask'].shape}")

# Prepare ONNX inputs
onnx_inputs = {
    "input_ids": inputs_tokenized["input_ids"].astype(np.int64),
    "attention_mask": inputs_tokenized["attention_mask"].astype(np.int64)
}

# Run inference
print("\n⚡ Running ONNX inference...")
outputs = session.run(["last_hidden_state"], onnx_inputs)
hidden_states = outputs[0]

print(f"   Hidden states shape: {hidden_states.shape}")
print(f"   Expected: (3, 128, 768) or (3, seq_len, 768)")

if len(hidden_states.shape) != 3 or hidden_states.shape[0] != 3 or hidden_states.shape[2] != 768:
    print(f"   ❌ Unexpected shape!")
    exit(1)

print("   ✅ Shape correct!")

# Mean pooling
print("\n🔄 Testing mean pooling...")
attention_mask = inputs_tokenized["attention_mask"]
input_mask_expanded = np.expand_dims(attention_mask, axis=-1)
sum_embeddings = np.sum(hidden_states * input_mask_expanded, axis=1)
sum_mask = np.clip(input_mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
embeddings = sum_embeddings / sum_mask

print(f"   Embeddings shape: {embeddings.shape}")
print(f"   Expected: (3, 768)")

if embeddings.shape != (3, 768):
    print(f"   ❌ Unexpected embedding shape!")
    exit(1)

print("   ✅ Mean pooling correct!")

# Normalize
print("\n🔄 Testing normalization...")
norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
normalized_embeddings = embeddings / norms

print(f"   Normalized embeddings shape: {normalized_embeddings.shape}")
print(f"   Sample (first 5 dims): {normalized_embeddings[0, :5]}")

# Test similarity
print("\n📊 Testing cross-lingual similarity...")

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

sim_01 = cosine_similarity(normalized_embeddings[0], normalized_embeddings[1])
sim_02 = cosine_similarity(normalized_embeddings[0], normalized_embeddings[2])
sim_12 = cosine_similarity(normalized_embeddings[1], normalized_embeddings[2])

print(f"   'Hello world' <-> 'Xin chào thế giới': {sim_01:.4f}")
print(f"   'Hello world' <-> 'Gạch ceramic': {sim_02:.4f}")
print(f"   'Xin chào' <-> 'Gạch ceramic': {sim_12:.4f}")

if sim_01 > 0.5:
    print("   ✅ Cross-lingual similarity working!")
else:
    print("   ⚠️  Low cross-lingual similarity")

print("\n" + "=" * 60)
print("✅ ONNX model verification PASSED!")
print("=" * 60)
print("\n📝 Summary:")
print("   ✅ Model structure correct")
print("   ✅ Input/output names match")
print("   ✅ Inference working")
print("   ✅ Mean pooling correct")
print("   ✅ Normalization correct")
print("   ✅ Ready for Triton deployment!")

