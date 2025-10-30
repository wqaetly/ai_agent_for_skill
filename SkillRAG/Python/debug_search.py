"""
Debug search issues
"""

import yaml
import logging
from rag_engine import RAGEngine
from embeddings import EmbeddingGenerator

logging.basicConfig(level=logging.INFO)

# Load config
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# Create RAG engine
engine = RAGEngine(config)

print("=" * 60)
print("Debug Search Issues")
print("=" * 60)

# Check what's in the vector store
print("\n1. Vector Store Stats:")
stats = engine.vector_store.get_statistics()
print(f"   Count: {stats.get('count', 'N/A')}")
print(f"   Collection: {stats.get('collection_name', 'N/A')}")

# Try to get all documents
print("\n2. Getting all documents...")
try:
    result = engine.vector_store.collection.get()
    print(f"   Total documents: {len(result['ids']) if result and 'ids' in result else 0}")
    if result and 'ids' in result and len(result['ids']) > 0:
        print(f"   First document ID: {result['ids'][0]}")
        if 'metadatas' in result:
            print(f"   First metadata: {result['metadatas'][0]}")
        if 'documents' in result:
            print(f"   First document (preview): {result['documents'][0][:200]}...")
except Exception as e:
    print(f"   Error: {e}")

# Test query with embedding
print("\n3. Testing query embedding...")
query = "flame damage attack"
query_embedding = engine.embedding_generator.encode(query)
print(f"   Query: '{query}'")
print(f"   Embedding length: {len(query_embedding)}")
print(f"   First 5 values: {query_embedding[:5]}")

# Try direct query with lower threshold
print("\n4. Direct vector store query...")
try:
    results = engine.vector_store.query(
        query_embeddings=[query_embedding],
        top_k=5,
        where=None
    )
    print(f"   Results: {results}")
    if results and 'ids' in results and results['ids'] and len(results['ids'][0]) > 0:
        print(f"   Found {len(results['ids'][0])} results:")
        for i in range(len(results['ids'][0])):
            print(f"      - {results['metadatas'][0][i]['skill_name']}: distance={results['distances'][0][i]:.3f}, similarity={1-results['distances'][0][i]:.3f}")
    else:
        print("   No results found")
except Exception as e:
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()

# Try RAG engine search with very low threshold
print("\n5. RAG engine search (threshold=0.3)...")
engine.similarity_threshold = 0.0  # Temporarily set to 0
results = engine.search_skills(query, top_k=5)
print(f"   Found {len(results)} results:")
for skill in results:
    print(f"      - {skill['skill_name']}: similarity={skill['similarity']:.3f}")

print("\n" + "=" * 60)
