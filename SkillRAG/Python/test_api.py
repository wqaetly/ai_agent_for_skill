"""
Test the SkillRAG API
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8765"

def test_health():
    """Test health check"""
    print("Testing health check...")
    r = requests.get(f"{BASE_URL}/health")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}\n")

def test_search(query, top_k=3):
    """Test search"""
    print(f"Testing search with query: '{query}'...")
    r = requests.get(f"{BASE_URL}/search", params={'q': query, 'top_k': top_k})
    print(f"Status: {r.status_code}")
    result = r.json()
    print(f"Found {result['count']} results:")
    for i, skill in enumerate(result['results'], 1):
        print(f"  {i}. {skill['skill_name']} (similarity: {skill['similarity']:.3f})")
    print()
    return result

def test_stats():
    """Test statistics"""
    print("Testing statistics...")
    r = requests.get(f"{BASE_URL}/stats")
    print(f"Status: {r.status_code}")
    stats = r.json()['statistics']
    print(f"Total indexed: {stats['engine_stats']['total_indexed']}")
    print(f"Total queries: {stats['engine_stats']['total_queries']}")
    print(f"Vector store count: {stats['vector_store']['count']}")
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("SkillRAG API Test")
    print("=" * 60)
    print()

    # Test health
    test_health()

    # Test search with different queries
    test_search("flame damage attack", top_k=3)
    test_search("shield protect", top_k=3)
    test_search("movement dash", top_k=3)

    # Test statistics
    test_stats()

    print("=" * 60)
    print("Tests completed!")
    print("=" * 60)
