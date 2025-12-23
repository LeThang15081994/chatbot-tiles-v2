import uuid
from datetime import datetime, timezone
import requests
from typing import List, Dict

from pymilvus import (
    connections,
    Collection
)

# =========================
# CONFIG
# =========================

EMBEDDING_API_URL = "http://localhost:7000/embed"

MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
MILVUS_DB = "chatbot_gachai"
MILVUS_ALIAS = "company_document"
MILVUS_COLLECTION_NAME = "company_document_info"

BAND = "gach.ai"
SOURCE = "about_us.docx"

# =========================
# SAMPLE CHUNKS (đã chunk semantic)
# =========================

CHUNKS: List[Dict] = [
    # {
    #     "category": "about",
    #     "context": (
    #         "Gach.AI was founded from a simple question: why choosing tiles has to be "
    #         "complicated and time-consuming. With more than 15 years of experience "
    #         "in the premium tile market, Gach.AI combines industry expertise with "
    #         "artificial intelligence to deliver transparency, speed, and trust."
    #     ),
    #     "priority": 10,
    # },
    # {
    #     "category": "mission",
    #     "context": (
    #         "Gach.AI’s mission is to redefine how people choose tiles by making the "
    #         "process faster, smarter, and more inspiring through artificial intelligence."
    #     ),
    #     "priority": 9,
    # },
    # {
    #     "category": "vision",
    #     "context": (
    #         "Gach.AI aims to become Southeast Asia’s leading digital platform for the "
    #         "tile industry, where technology, design, and service converge."
    #     ),
    #     "priority": 9,
    # },
    # {
    #     "category": "contact",
    #     "context": (
    #         "Gach.AI is located at 161, Street No. 5, Lakeview Urban Area, Thu Duc City, "
    #         "Ho Chi Minh City, Vietnam. Customers can call +84 938 872 866 or email "
    #         "info.gach.ai@gmail.com."
    #     ),
    #     "priority": 10,
    # },
    # {
    #     "category": "showroom",
    #     "context": (
    #         "The Gach.AI showroom is open from 8:00 AM to 5:30 PM Monday to Friday, "
    #         "from 8:00 AM to 12:00 PM on Saturday, and closed on Sunday."
    #     ),
    #     "priority": 8,
    # },
    {
    "category": "values",
    "context": (
        "Gach.AI’s core values are built around customer centricity, transparency, "
        "and integrity. The company places customers at the heart of everything it does, "
        "committing to clear information, honest pricing, and delivering exactly what "
        "is promised. Gach.AI continuously innovates through artificial intelligence "
        "and data technology to improve every customer journey, believing that excellent "
        "service is the foundation for customer trust and peace of mind from tile "
        "selection to project completion."
    ),
    "priority": 9
}
]

# =========================
# FUNCTIONS
# =========================
def now_iso_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def get_embedding(text: str) -> List[float]:
    """
    Call embedding service and return vector
    """
    response = requests.post(
        EMBEDDING_API_URL,
        json={"texts": [text]},
        timeout=30
    )
    response.raise_for_status()

    data = response.json()

    if data["count"] != 1:
        raise ValueError("Embedding API returned invalid count")
    return data["embeddings"][0]


def connect_milvus():
    connections.connect(
        host=MILVUS_HOST,
        port=MILVUS_PORT,
        user="root",
        password="Milvus",
        db_name=MILVUS_DB
    )


def insert_chunks(collection: Collection, chunks: List[Dict]):
    rows = []

    for chunk in chunks:
        embedding = get_embedding(chunk["context"])

        row = {
            "id": str(uuid.uuid4()),
            "band": BAND,
            "source": SOURCE,
            "category": chunk["category"],
            "context": chunk["context"],
            "vector": embedding,
            "priority": chunk["priority"],
            "created_at": now_iso_utc()
        }
        rows.append(row)

    collection.insert(rows)
    collection.flush()


# =========================
# MAIN
# =========================

def main():
    print("🔌 Connecting to Milvus...")
    connect_milvus()

    collection = Collection(MILVUS_COLLECTION_NAME)
    collection.load()

    print(f"📥 Inserting {len(CHUNKS)} company document chunks...")
    insert_chunks(collection, CHUNKS)

    print("✅ Done. Data inserted successfully.")


if __name__ == "__main__":
    main()
