#!/usr/bin/env python3
"""
Embedding API 테스트 스크립트
"""
import sys
import os

# 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brian_coder/src'))

from llm_client import get_embedding, get_embedding_dimension

def test_embedding():
    print("=" * 50)
    print("Embedding API Test")
    print("=" * 50)
    
    # 1. Dimension 확인
    print("\n1. Getting embedding dimension...")
    try:
        dim = get_embedding_dimension()
        print(f"   ✅ Dimension: {dim}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # 2. 단일 텍스트 임베딩
    print("\n2. Testing single text embedding...")
    try:
        text = "PCIe Transaction Layer Protocol"
        emb = get_embedding(text)
        print(f"   ✅ Text: '{text}'")
        print(f"   ✅ Embedding length: {len(emb)}")
        print(f"   ✅ First 5 values: {emb[:5]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. 한글 텍스트
    print("\n3. Testing Korean text...")
    try:
        text_kr = "메모리 읽기 요청"
        emb_kr = get_embedding(text_kr)
        print(f"   ✅ Text: '{text_kr}'")
        print(f"   ✅ Embedding length: {len(emb_kr)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("All tests passed! ✅")
    print("=" * 50)

if __name__ == "__main__":
    test_embedding()
