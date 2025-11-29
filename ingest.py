import json
import chromadb
from chromadb.utils import embedding_functions

# ---------------------------------------
# 1) Connect to Chroma persistence
# ---------------------------------------
client = chromadb.PersistentClient(path="./hr_db")

# Create or load collection
collection = client.get_or_create_collection(
    name="hr_agents",
    metadata={"hnsw:space": "cosine"},
)

# OPTIONAL: Use OpenAI or other embedding model
# Replace with your embedding model or keep none 
# if using Chroma default.
try:
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key="YOUR_OPENAI_API_KEY",
        model_name="text-embedding-3-small"
    )
    collection = client.get_or_create_collection(
        "hr_agents",
        embedding_function=openai_ef
    )
except Exception:
    print("⚠️ Using default embedding function (no external API)")


# ---------------------------------------
# 2) Load and append JSONL dataset
# ---------------------------------------
dataset_file = "hr_agents_dataset.jsonl"
docs, ids, metas = [], [], []

with open(dataset_file, "r", encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue
        record = json.loads(line)

        docs.append(record["content"])
        ids.append(record["id"])
        metas.append(record["metadata"])

# ---------------------------------------
# 3) Append to Chroma (safe add)
# ---------------------------------------
print(f"📌 Appending {len(docs)} documents to Chroma...")

# Chroma allows incremental appending
# This will add ONLY new IDs
collection.add(
    documents=docs,
    metadatas=metas,
    ids=ids
)

print("✅ Data successfully appended to Chroma DB!")
print("🎉 Collection size:", collection.count())
