"""
Test script to verify document processing functionality.
"""

import os
import sys
import logging

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from document_processor import document_processor
from config import KNOWLEDGE_BASE_DIR

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_document_loading():
    """Test document loading functionality."""
    print("🧪 Testing Document Loading...")
    
    try:
        # Load documents from the knowledge base directory
        documents = document_processor.load_documents_from_directory()
        
        if not documents:
            print("❌ No documents loaded")
            return False
        
        print(f"✅ Successfully loaded {len(documents)} document pages")
        
        # Print document info
        for i, doc in enumerate(documents):
            print(f"   Document {i+1}:")
            print(f"     - Source: {doc.metadata.get('source', 'Unknown')}")
            print(f"     - Filename: {doc.metadata.get('filename', 'Unknown')}")
            print(f"     - File type: {doc.metadata.get('file_type', 'Unknown')}")
            print(f"     - Content length: {len(doc.page_content)} characters")
            print(f"     - Content preview: {doc.page_content[:100]}...")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading documents: {e}")
        logger.error(f"Document loading error: {e}", exc_info=True)
        return False


def test_document_chunking():
    """Test document chunking functionality."""
    print("🧪 Testing Document Chunking...")
    
    try:
        # Load documents first
        documents = document_processor.load_documents_from_directory()
        
        if not documents:
            print("❌ No documents to chunk")
            return False
        
        # Chunk the documents
        chunked_docs = document_processor.chunk_documents(documents)
        
        if not chunked_docs:
            print("❌ No chunks created")
            return False
        
        print(f"✅ Successfully created {len(chunked_docs)} chunks from {len(documents)} documents")
        
        # Print chunk info
        for i, chunk in enumerate(chunked_docs[:3]):  # Show first 3 chunks
            print(f"   Chunk {i+1}:")
            print(f"     - Chunk ID: {chunk.metadata.get('chunk_id', 'Unknown')}")
            print(f"     - Source: {chunk.metadata.get('filename', 'Unknown')}")
            print(f"     - Chunk size: {chunk.metadata.get('chunk_size', 'Unknown')} characters")
            print(f"     - Content preview: {chunk.page_content[:150]}...")
            print()
        
        if len(chunked_docs) > 3:
            print(f"   ... and {len(chunked_docs) - 3} more chunks")
        
        return True
        
    except Exception as e:
        print(f"❌ Error chunking documents: {e}")
        logger.error(f"Document chunking error: {e}", exc_info=True)
        return False


def test_document_validation():
    """Test document validation functionality."""
    print("🧪 Testing Document Validation...")
    
    try:
        # Load and chunk documents
        documents = document_processor.load_documents_from_directory()
        chunked_docs = document_processor.chunk_documents(documents)
        
        if not chunked_docs:
            print("❌ No chunks to validate")
            return False
        
        # Validate documents
        validation = document_processor.validate_documents(chunked_docs)
        
        print(f"✅ Validation completed for {validation['total_documents']} documents")
        print(f"   Valid: {validation['valid']}")
        
        if validation['errors']:
            print("   Errors:")
            for error in validation['errors']:
                print(f"     - {error}")
        
        if validation['warnings']:
            print("   Warnings:")
            for warning in validation['warnings']:
                print(f"     - {warning}")
        
        return validation['valid']
        
    except Exception as e:
        print(f"❌ Error validating documents: {e}")
        logger.error(f"Document validation error: {e}", exc_info=True)
        return False


def test_document_info():
    """Test document information functionality."""
    print("🧪 Testing Document Information...")
    
    try:
        # Load and chunk documents
        documents = document_processor.load_documents_from_directory()
        chunked_docs = document_processor.chunk_documents(documents)
        
        if not chunked_docs:
            print("❌ No chunks to analyze")
            return False
        
        # Get document info
        doc_info = document_processor.get_document_info(chunked_docs)
        
        print(f"✅ Document Information:")
        print(f"   Total documents: {doc_info['total_documents']}")
        print(f"   Total chunks: {doc_info['total_chunks']}")
        print(f"   File types: {doc_info['file_types']}")
        print(f"   Total size: {doc_info['total_size']} bytes")
        print(f"   Sources: {doc_info['sources']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error getting document info: {e}")
        logger.error(f"Document info error: {e}", exc_info=True)
        return False


def main():
    """Run all document processing tests."""
    print("🧪 Document Processing Test Suite")
    print("=" * 50)
    
    tests = [
        ("Document Loading", test_document_loading),
        ("Document Chunking", test_document_chunking),
        ("Document Validation", test_document_validation),
        ("Document Information", test_document_info)
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
        print("🎉 All document processing tests passed!")
        print("✅ Ready to proceed with knowledge base setup")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    main()
