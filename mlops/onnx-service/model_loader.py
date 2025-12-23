"""
ONNX Model Loader
Loads and manages ONNX model for embedding inference
"""
from pathlib import Path
import onnxruntime as ort
from transformers import AutoTokenizer
import numpy as np


class ONNXEmbeddingModel:
    """
    ONNX Runtime embedding model
    Provides sentence-transformers compatible interface
    """

    def __init__(self, model_dir: str):
        """
        Initialize ONNX model

        Args:
            model_dir: Directory containing model.onnx and tokenizer files
        """
        self.model_dir = Path(model_dir)
        self.onnx_path = self.model_dir / "model.onnx"

        if not self.onnx_path.exists():
            raise FileNotFoundError(f"ONNX model not found: {self.onnx_path}")

        # Load ONNX Runtime session
        self.session = ort.InferenceSession(
            str(self.onnx_path),
            providers=['CPUExecutionProvider']
        )

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir))

        # Model info
        self.dimension = 768
        self.max_length = 128

        print(f"✅ ONNX model loaded: {self.onnx_path}")
        print(f"   Providers: {self.session.get_providers()}")
        print(f"   Input names: {[i.name for i in self.session.get_inputs()]}")
        print(f"   Output names: {[o.name for o in self.session.get_outputs()]}")

    def embed(self, texts: list[str]) -> np.ndarray:
        """
        Generate embeddings for texts

        Args:
            texts: List of text strings

        Returns:
            embeddings: numpy array of shape (batch_size, 768)
        """
        # Tokenize
        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="np"
        )

        # Run ONNX inference
        ort_inputs = {
            "input_ids": inputs["input_ids"].astype(np.int64),
            "attention_mask": inputs["attention_mask"].astype(np.int64)
        }

        # Get hidden states
        outputs = self.session.run(["last_hidden_state"], ort_inputs)
        hidden_states = outputs[0]  # [batch, seq_len, 768]

        # Mean pooling
        embeddings = self._mean_pooling(hidden_states, inputs["attention_mask"])

        # Normalize
        embeddings = self._normalize(embeddings)

        return embeddings.astype(np.float32)

    def _mean_pooling(self, hidden_states: np.ndarray, attention_mask: np.ndarray) -> np.ndarray:
        """Mean pooling with attention mask"""
        input_mask_expanded = np.expand_dims(attention_mask, axis=-1)
        sum_embeddings = np.sum(hidden_states * input_mask_expanded, axis=1)
        sum_mask = np.clip(input_mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
        return sum_embeddings / sum_mask

    def _normalize(self, embeddings: np.ndarray) -> np.ndarray:
        """L2 normalization"""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings / norms

