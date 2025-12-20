"""
Benchmark Python Backend vs ONNX Runtime Backend
"""
import time
import numpy as np
import requests
from statistics import mean, stdev

TRITON_URL = "http://localhost:8000"


def benchmark_python_backend():
    """Benchmark Python backend (sentence-transformers)"""
    print("🐍 Benchmarking Python Backend")
    print("=" * 60)

    test_texts = [
        "Gạch ốp lát ceramic chất lượng cao",
        "High quality ceramic tiles for bathroom",
        "Sản phẩm gạch men sứ hiện đại",
    ]

    latencies = []

    # Warmup
    for _ in range(5):
        payload = {
            "inputs": [{
                "name": "text",
                "datatype": "BYTES",
                "shape": [len(test_texts)],
                "data": test_texts
            }]
        }
        requests.post(f"{TRITON_URL}/v2/models/embeddings/infer", json=payload)

    # Benchmark
    for i in range(50):
        payload = {
            "inputs": [{
                "name": "text",
                "datatype": "BYTES",
                "shape": [len(test_texts)],
                "data": test_texts
            }]
        }

        start = time.time()
        response = requests.post(f"{TRITON_URL}/v2/models/embeddings/infer", json=payload)
        latency = (time.time() - start) * 1000

        if response.status_code == 200:
            latencies.append(latency)

    print(f"Requests: {len(latencies)}")
    print(f"Mean latency: {mean(latencies):.2f}ms")
    print(f"Std dev: {stdev(latencies):.2f}ms")
    print(f"Min: {min(latencies):.2f}ms")
    print(f"Max: {max(latencies):.2f}ms")
    print(f"P50: {np.percentile(latencies, 50):.2f}ms")
    print(f"P95: {np.percentile(latencies, 95):.2f}ms")
    print(f"P99: {np.percentile(latencies, 99):.2f}ms")

    return {
        "backend": "python",
        "mean": mean(latencies),
        "p50": np.percentile(latencies, 50),
        "p95": np.percentile(latencies, 95),
        "p99": np.percentile(latencies, 99),
    }


def benchmark_onnx_backend():
    """Benchmark ONNX Runtime backend (via Python wrapper)"""
    print("\n⚡ Benchmarking ONNX Runtime Backend")
    print("=" * 60)

    test_texts = [
        "Gạch ốp lát ceramic chất lượng cao",
        "High quality ceramic tiles for bathroom",
        "Sản phẩm gạch men sứ hiện đại",
    ]

    latencies = []

    # Warmup
    for _ in range(5):
        payload = {
            "inputs": [{
                "name": "text",
                "datatype": "BYTES",
                "shape": [len(test_texts)],
                "data": test_texts
            }]
        }
        requests.post(f"{TRITON_URL}/v2/models/embeddings_onnx/infer", json=payload)

    # Benchmark
    for i in range(50):
        payload = {
            "inputs": [{
                "name": "text",
                "datatype": "BYTES",
                "shape": [len(test_texts)],
                "data": test_texts
            }]
        }

        start = time.time()
        response = requests.post(f"{TRITON_URL}/v2/models/embeddings_onnx/infer", json=payload)
        latency = (time.time() - start) * 1000

        if response.status_code == 200:
            latencies.append(latency)

    print(f"Requests: {len(latencies)}")
    print(f"Mean latency: {mean(latencies):.2f}ms")
    print(f"Std dev: {stdev(latencies):.2f}ms")
    print(f"Min: {min(latencies):.2f}ms")
    print(f"Max: {max(latencies):.2f}ms")
    print(f"P50: {np.percentile(latencies, 50):.2f}ms")
    print(f"P95: {np.percentile(latencies, 95):.2f}ms")
    print(f"P99: {np.percentile(latencies, 99):.2f}ms")

    return {
        "backend": "onnx",
        "mean": mean(latencies),
        "p50": np.percentile(latencies, 50),
        "p95": np.percentile(latencies, 95),
        "p99": np.percentile(latencies, 99),
    }


def compare_results(python_results, onnx_results):
    """Compare benchmark results"""
    print("\n" + "=" * 60)
    print("📊 Performance Comparison")
    print("=" * 60)

    print(f"\n{'Metric':<15} {'Python':<15} {'ONNX':<15} {'Speedup':<10}")
    print("-" * 60)

    for metric in ["mean", "p50", "p95", "p99"]:
        python_val = python_results[metric]
        onnx_val = onnx_results[metric]
        speedup = python_val / onnx_val

        print(f"{metric.upper():<15} {python_val:>10.2f}ms {onnx_val:>10.2f}ms {speedup:>8.2f}x")

    print("\n" + "=" * 60)

    overall_speedup = python_results["mean"] / onnx_results["mean"]

    if overall_speedup > 2:
        print(f"🚀 ONNX is {overall_speedup:.2f}x FASTER! Excellent optimization!")
    elif overall_speedup > 1.5:
        print(f"⚡ ONNX is {overall_speedup:.2f}x FASTER! Good optimization!")
    elif overall_speedup > 1.0:
        print(f"👍 ONNX is {overall_speedup:.2f}x FASTER! Modest improvement.")
    else:
        print(f"⚠️  ONNX is {overall_speedup:.2f}x (slower). Check configuration!")


if __name__ == "__main__":
    try:
        print("🔬 Triton Backend Benchmark")
        print("=" * 60)
        print("Testing: paraphrase-multilingual-mpnet-base-v2")
        print("Batch size: 3")
        print("Requests: 50")
        print()

        # Check server
        response = requests.get(f"{TRITON_URL}/v2/health/ready")
        if response.status_code != 200:
            print("❌ Triton server not ready!")
            exit(1)

        # Benchmark both backends
        python_results = benchmark_python_backend()
        onnx_results = benchmark_onnx_backend()

        # Compare
        compare_results(python_results, onnx_results)

        print("\n✅ Benchmark complete!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

