"""
Test script for the Policy Bot.

This script provides basic tests to verify the Policy Bot is working correctly.
"""

import os
import sys
import logging
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from policy_agent import policy_bot
from document_processor import document_processor
from config import KNOWLEDGE_BASE_DIR

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_document_processing():
    """Test document processing functionality."""
    print("🧪 Testing Document Processing...")
    
    # Check if documents directory exists
    docs_dir = Path(KNOWLEDGE_BASE_DIR)
    if not docs_dir.exists():
        print("❌ Documents directory not found")
        return False
    
    # Check for documents
    supported_files = []
    for ext in ['.pdf', '.docx', '.doc', '.txt']:
        supported_files.extend(list(docs_dir.glob(f"*{ext}")))
    
    if not supported_files:
        print("❌ No documents found to test with")
        return False
    
    print(f"📚 Found {len(supported_files)} documents")
    
    # Test document loading
    try:
        documents = document_processor.load_documents_from_directory()
        if not documents:
            print("❌ Failed to load documents")
            return False
        
        print(f"✅ Successfully loaded {len(documents)} document pages")
        
        # Test document chunking
        chunked_docs = document_processor.chunk_documents(documents)
        if not chunked_docs:
            print("❌ Failed to chunk documents")
            return False
        
        print(f"✅ Successfully created {len(chunked_docs)} chunks")
        
        # Test document validation
        validation = document_processor.validate_documents(chunked_docs)
        if not validation['valid']:
            print("⚠️  Document validation issues:")
            for error in validation['errors']:
                print(f"   - {error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in document processing: {e}")
        return False


def test_policy_bot():
    """Test the Policy Bot functionality."""
    print("\n🤖 Testing Policy Bot...")
    
    try:
        # Test health check
        health = policy_bot.health_check()
        print(f"📊 Health Status: {health['status']}")
        
        if health['status'] == 'unhealthy':
            print("❌ Policy Bot is unhealthy")
            return False
        
        # Test knowledge base stats
        stats = policy_bot.get_knowledge_base_stats()
        print(f"📚 Knowledge Base: {stats['total_documents']} documents")
        
        if stats['total_documents'] == 0:
            print("⚠️  No documents in knowledge base")
            return False
        
        # Test question answering
        test_questions = [
            "What is the company policy on remote work?",
            "How many vacation days do employees get?",
            "What is the dress code policy?",
            "How do I report harassment?",
            "What are the working hours?"
        ]
        
        print("\n🔍 Testing question answering...")
        for question in test_questions:
            print(f"\n❓ Question: {question}")
            response = policy_bot.ask_question(question, user_id="test_user")
            
            if response['status'] == 'success':
                print(f"✅ Answer: {response['answer'][:100]}...")
                print(f"📚 Sources: {response['num_sources']} documents")
            else:
                print(f"❌ Error: {response.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Policy Bot: {e}")
        return False


def test_api_endpoints():
    """Test API endpoints (requires running server)."""
    print("\n🌐 Testing API Endpoints...")
    
    try:
        import requests
        
        base_url = "http://localhost:8000"
        
        # Test health endpoint
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        
        # Test stats endpoint
        response = requests.get(f"{base_url}/stats")
        if response.status_code == 200:
            print("✅ Stats endpoint working")
        else:
            print(f"❌ Stats endpoint failed: {response.status_code}")
            return False
        
        # Test ask endpoint
        test_data = {
            "question": "What is the company policy on remote work?",
            "user_id": "test_user"
        }
        
        response = requests.post(f"{base_url}/ask", json=test_data)
        if response.status_code == 200:
            print("✅ Ask endpoint working")
        else:
            print(f"❌ Ask endpoint failed: {response.status_code}")
            return False
        
        return True
        
    except ImportError:
        print("⚠️  requests library not available, skipping API tests")
        return True
    except Exception as e:
        print(f"❌ Error testing API endpoints: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Policy Bot Test Suite")
    print("=" * 50)
    
    # Check configuration
    from config import LLM_API_KEY
    if LLM_API_KEY == "YOUR_GOOGLE_API_KEY_HERE":
        print("❌ Please configure your Google API key first!")
        print("1. Copy env_template.txt to .env")
        print("2. Add your Google API key to the .env file")
        return
    
    tests = [
        ("Document Processing", test_document_processing),
        ("Policy Bot", test_policy_bot),
        ("API Endpoints", test_api_endpoints)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 Test Results Summary:")
    print("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Policy Bot is ready to use.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    main()
