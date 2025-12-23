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
MILVUS_ALIAS = "collection_info"
MILVUS_COLLECTION_NAME = "collection_info"

BAND = "gach.ai"

# =========================
# COLLECTION CONTEXTS (SEMANTIC-READY)
# =========================

COLLECTIONS: List[Dict] = [
    {
        "collection_id": "L03",
        "collection_name": "Wooden",
        "context": (
            "Wooden Look Tile represents the warmth and natural feeling of real wood "
            "in modern interiors. Inspired by authentic wood grain textures and warm tones, "
            "this collection creates a cozy, relaxing, and elegant atmosphere while "
            "maintaining the durability and water resistance of porcelain tiles. "
            "It fits Scandinavian, Rustic, and Minimalist interior styles and is suitable "
            "for bedrooms, living rooms, kitchens, cafés, spas, and showrooms."
        )
    },
    {
        "collection_id": "L02",
        "collection_name": "Decor",
        "context": (
            "Decor Look Tile focuses on creativity and artistic expression. Featuring decorative "
            "patterns and diverse color palettes, this collection transforms walls and floors "
            "into visual highlights. It fits Art Deco, Bohemian, and Modern Chic styles and "
            "is suitable for living rooms, bathrooms, restaurants, boutiques, bars, and "
            "interior showrooms."
        )
    },
    {
        "collection_id": "L01",
        "collection_name": "Concrete",
        "context": (
            "Concrete Look Tile embodies minimalism and modern strength inspired by raw cement "
            "surfaces. With smooth textures and cool tones, it creates a clean and contemporary "
            "atmosphere. This collection fits Industrial and Minimalist styles and is suitable "
            "for living rooms, offices, studios, and modern commercial spaces."
        )
    },
    {
        "collection_id": "L04",
        "collection_name": "Marble",
        "context": (
            "Marble Look Tile represents timeless elegance and luxury inspired by natural marble. "
            "With delicate veins and soft reflections, it creates a refined and sophisticated "
            "atmosphere. This collection fits Classic, Luxury, and Contemporary styles and is "
            "suitable for villas, hotels, large living areas, foyers, and bathrooms."
        )
    },
    {
        "collection_id": "L05",
        "collection_name": "Mono",
        "context": (
            "Mono Look Tile focuses on pure simplicity and minimalist aesthetics. With neutral "
            "and monochrome tones, it creates a calm and balanced atmosphere that highlights "
            "light and architecture. This collection fits Minimalist and Zen-inspired interiors "
            "and is suitable for offices, bedrooms, studios, and bathrooms."
        )
    },
    {
        "collection_id": "L06",
        "collection_name": "Stone",
        "context": (
            "Stone Look Tile reflects the strength and grounded beauty of natural stone. "
            "Featuring deep textures and neutral hues, it balances luxury and nature. "
            "This collection is suitable for both indoor and outdoor spaces, including "
            "entryways, hallways, gardens, resorts, and villas."
        )
    },
    {
        "collection_id": "L07",
        "collection_name": "Mosaic",
        "context": (
            "Mosaic Look Tile emphasizes creativity and flexible design expression. "
            "Composed of small tiles with varied colors, it allows artistic compositions "
            "and decorative accents. This collection is suitable for bathrooms, kitchens, "
            "swimming pools, spas, and artistic cafés."
        )
    },
    {
        "collection_id": "L08",
        "collection_name": "Subway",
        "context": (
            "Subway Tile represents timeless simplicity inspired by classic metro tiles. "
            "Its rectangular format supports versatile layouts such as horizontal, vertical, "
            "and herringbone patterns. This collection fits modern and retro interiors and is "
            "suitable for kitchen backsplashes, bathrooms, bars, and hygienic spaces."
        )
    },
    {
        "collection_id": "L09",
        "collection_name": "Terrazzo",
        "context": (
            "Terrazzo Look Tile blends tradition and modern creativity through multicolored "
            "stone fragments embedded in a solid surface. Its dynamic appearance creates an "
            "energetic and artistic atmosphere. This collection is suitable for floors, "
            "boutique shops, creative studios, and both indoor and outdoor spaces."
        )
    },
    {
        "collection_id": "L10",
        "collection_name": "Travertine",
        "context": (
            "Travertine Look Tile offers understated luxury inspired by classic natural stone. "
            "With soft veins and neutral tones, it creates a warm and tranquil atmosphere. "
            "This collection is suitable for villas, resorts, spas, and high-end retreats "
            "that emphasize timeless elegance."
        )
    },
    {
        "collection_id": "L11",
        "collection_name": "Tile_adhesive",
        "context": (
            "Tile Adhesive is a professional-grade porcelain tile adhesive designed to ensure "
            "strong bonding and long-term durability. With water absorption below 0.5%, "
            "it supports aesthetic consistency and structural performance for all tile "
            "collections in both residential and commercial projects."
        )
    }
]

# =========================
# FUNCTIONS
# =========================

def now_iso_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_embedding(text: str) -> List[float]:
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
        alias=MILVUS_ALIAS,
        host=MILVUS_HOST,
        port=MILVUS_PORT,
        user="root",
        password="Milvus",
        db_name=MILVUS_DB
    )


def insert_collections(collection: Collection, collections: List[Dict]):
    rows = []

    for item in collections:
        embedding = get_embedding(item["context"])

        row = {
            "id": str(uuid.uuid4()),
            "collection_id": item["collection_id"],
            "collection_name": item["collection_name"],
            "band": BAND,
            "context": item["context"],
            "vector": embedding,
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

    collection = Collection(MILVUS_COLLECTION_NAME, using=MILVUS_ALIAS)
    collection.load()

    print(f"📥 Inserting {len(COLLECTIONS)} collections...")
    insert_collections(collection, COLLECTIONS)

    print("✅ Done. collection_info inserted successfully.")


if __name__ == "__main__":
    main()
