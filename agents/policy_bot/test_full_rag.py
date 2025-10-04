"""
Test script for the full RAG pipeline with LLM integration.
"""

import os
import sys
import logging

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from policy_agent import policy_bot
from config import LLM_API_KEY

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_policy_bot_initialization():
    """Test Policy Bot initialization."""
    print("🧪 Testing Policy Bot Initialization...")
    
    try:
        # Check if API key is configured
        if LLM_API_KEY == "YOUR_GOOGLE_API_KEY_HERE":
            print("❌ Google API key not configured!")
            print("Please edit .env file and add your Google API key")
            return False
        
        # Test health check
        health = policy_bot.health_check()
        print(f"📊 Health Status: {health['status']}")
        
        if health['status'] == 'unhealthy':
            print("❌ Policy Bot is unhealthy")
            print(f"Error: {health.get('error', 'Unknown error')}")
            return False
        
        # Test knowledge base stats
        stats = policy_bot.get_knowledge_base_stats()
        print(f"📚 Knowledge Base: {stats['total_documents']} documents")
        
        if stats['total_documents'] == 0:
            print("❌ No documents in knowledge base")
            return False
        
        print("✅ Policy Bot initialized successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing Policy Bot: {e}")
        logger.error(f"Policy Bot initialization error: {e}", exc_info=True)
        return False


def test_question_answering():
    """Test question answering functionality."""
    print("\n🧪 Testing Question Answering...")
    
    test_questions = [
        "What is the company policy on remote work?",
        "How many vacation days do employees get?",
        "What are the working hours?",
        "What is the dress code policy?",
        "How do I report harassment?",
        "What is the parental leave policy?",
        "What are the health insurance benefits?"
    ]
    
    results = []
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n   {i}. Question: {question}")
        
        try:
            response = policy_bot.ask_question(question, user_id="test_user")
            
            if response['status'] == 'success':
                print(f"   ✅ Answer: {response['answer'][:200]}...")
                print(f"   📚 Sources: {response['num_sources']} documents")
                results.append(True)
            else:
                print(f"   ❌ Error: {response.get('error', 'Unknown error')}")
                results.append(False)
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Question Answering Results: {passed}/{total} questions answered successfully")
    return passed == total


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n🧪 Testing Edge Cases...")
    
    edge_cases = [
        "",  # Empty question
        "What is the meaning of life?",  # Question not in documents
        "Tell me about the company's policy on unicorns",  # Nonsensical question
        "a" * 1000,  # Very long question
    ]
    
    results = []
    
    for i, question in enumerate(edge_cases, 1):
        print(f"\n   {i}. Edge case: '{question[:50]}{'...' if len(question) > 50 else ''}'")
        
        try:
            response = policy_bot.ask_question(question, user_id="test_user")
            
            if response['status'] == 'success':
                print(f"   ✅ Handled gracefully: {response['answer'][:100]}...")
                results.append(True)
            else:
                print(f"   ✅ Error handled: {response.get('error', 'Unknown error')}")
                results.append(True)  # Error handling is also success
                
        except Exception as e:
            print(f"   ❌ Exception not handled: {e}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Edge Case Results: {passed}/{total} cases handled properly")
    return passed == total


def main():
    """Run all RAG pipeline tests."""
    print("🧪 Full RAG Pipeline Test Suite")
    print("=" * 50)
    
    # Check API key first
    if LLM_API_KEY == "YOUR_GOOGLE_API_KEY_HERE":
        print("❌ Google API key not configured!")
        print("\nTo configure your API key:")
        print("1. Get your API key from: https://makersuite.google.com/app/apikey")
        print("2. Edit the .env file")
        print("3. Replace 'your_google_api_key_here' with your actual key")
        print("4. Run this test again")
        return
    
    tests = [
        ("Policy Bot Initialization", test_policy_bot_initialization),
        ("Question Answering", test_question_answering),
        ("Edge Cases", test_edge_cases)
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
        print("🎉 All RAG pipeline tests passed!")
        print("✅ Your Policy Bot is ready for production!")
        print("\nNext steps:")
        print("1. Run: python api_server.py (to start the API server)")
        print("2. Run: python web_interface.py (to start the web interface)")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    main()
