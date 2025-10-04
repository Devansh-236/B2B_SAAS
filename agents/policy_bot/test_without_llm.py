"""
Test script that works without LLM API key - tests document processing and vector store creation.
"""

import os
import sys
import logging

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from document_processor import document_processor
from config import KNOWLEDGE_BASE_DIR, VECTOR_DB_PATH

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_vector_store_creation():
    """Test creating a vector store without LLM."""
    print("🧪 Testing Vector Store Creation (without LLM)...")
    
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_chroma import Chroma
        
        # Initialize embeddings (this will download the model)
        print("📥 Downloading embedding model...")
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        print("✅ Embedding model loaded successfully")
        
        # Load and process documents
        print("📚 Loading and processing documents...")
        documents = document_processor.load_documents_from_directory()
        chunked_docs = document_processor.chunk_documents(documents)
        
        if not chunked_docs:
            print("❌ No documents to process")
            return False
        
        print(f"✅ Processed {len(chunked_docs)} document chunks")
        
        # Create vector store
        print("🗄️ Creating vector store...")
        vectorstore = Chroma.from_documents(
            documents=chunked_docs,
            embedding=embeddings,
            persist_directory=VECTOR_DB_PATH
        )
        
        # Vector store is automatically persisted
        print(f"✅ Vector store created and saved to {VECTOR_DB_PATH}")
        
        # Test retrieval
        print("🔍 Testing document retrieval...")
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        
        test_queries = [
            "remote work policy",
            "vacation days",
            "dress code",
            "working hours"
        ]
        
        for query in test_queries:
            print(f"\n   Query: '{query}'")
            docs = retriever.invoke(query)
            print(f"   Found {len(docs)} relevant documents")
            
            for i, doc in enumerate(docs):
                print(f"     {i+1}. {doc.metadata.get('filename', 'Unknown')} - {len(doc.page_content)} chars")
                print(f"        Preview: {doc.page_content[:100]}...")
        
        print("\n✅ Vector store creation and retrieval test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating vector store: {e}")
        logger.error(f"Vector store creation error: {e}", exc_info=True)
        return False


def test_document_search():
    """Test document search functionality."""
    print("\n🧪 Testing Document Search...")
    
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_chroma import Chroma
        
        # Load existing vector store
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        vectorstore = Chroma(
            persist_directory=VECTOR_DB_PATH,
            embedding_function=embeddings
        )
        
        # Test similarity search
        test_questions = [
            "What is the company policy on remote work?",
            "How many vacation days do employees get?",
            "What are the working hours?",
            "What is the dress code policy?",
            "How do I report harassment?"
        ]
        
        print("🔍 Testing similarity search...")
        for question in test_questions:
            print(f"\n   Question: {question}")
            
            # Get similar documents
            similar_docs = vectorstore.similarity_search(question, k=2)
            
            print(f"   Found {len(similar_docs)} similar documents:")
            for i, doc in enumerate(similar_docs):
                print(f"     {i+1}. {doc.metadata.get('filename', 'Unknown')}")
                print(f"        Content: {doc.page_content[:150]}...")
        
        print("\n✅ Document search test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing document search: {e}")
        logger.error(f"Document search error: {e}", exc_info=True)
        return False


def main():
    """Run tests that don't require LLM API key."""
    print("🧪 Policy Bot Tests (Without LLM)")
    print("=" * 50)
    print("This test will:")
    print("1. Download and test the embedding model")
    print("2. Process your documents")
    print("3. Create a vector database")
    print("4. Test document retrieval")
    print("=" * 50)
    
    tests = [
        ("Vector Store Creation", test_vector_store_creation),
        ("Document Search", test_document_search)
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
        print("🎉 All tests passed!")
        print("✅ Your knowledge base is ready!")
        print("📝 Next step: Configure your Google API key to test the full RAG pipeline")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    main()
