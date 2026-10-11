"""
Script to update the knowledge base with new documents.
Run this whenever you add new policy documents.
"""

import os
import sys
import logging
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from document_processor import document_processor
from config import KNOWLEDGE_BASE_DIR, VECTOR_DB_PATH

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_knowledge_base(verbose=True):
    """Update the knowledge base with all documents in the documents directory.
    
    Args:
        verbose (bool): Whether to print progress messages
        
    Returns:
        bool: True if update successful, False otherwise
    """
    
    if verbose:
        print("🔄 Updating Knowledge Base...")
        print("=" * 50)
    
    # Check if documents directory exists
    docs_dir = Path(KNOWLEDGE_BASE_DIR)
    if not docs_dir.exists():
        if verbose:
            print(f"❌ Documents directory not found: {docs_dir}")
        return False
    
    # List all documents
    supported_files = document_processor.find_supported_files(docs_dir)
    
    if not supported_files:
        if verbose:
            print(f"❌ No supported documents found in: {docs_dir}")
            print("   Supported formats: PDF, DOCX, TXT")
        return False
    
    if verbose:
        print(f"📚 Found {len(supported_files)} documents:")
        for file in supported_files:
            print(f"   - {file.name}")
    
    # Process documents
    if verbose:
        print("\n🔄 Processing documents...")
    try:
        documents = document_processor.process_documents_from_directory()
        
        if not documents:
            if verbose:
                print("❌ No documents were successfully processed")
            return False
        
        # Get document info
        doc_info = document_processor.get_document_info(documents)
        if verbose:
            print(f"✅ Successfully processed {doc_info['total_chunks']} chunks from {doc_info['total_documents']} documents")
        
        # Validate documents
        validation = document_processor.validate_documents(documents)
        if not validation['valid']:
            if verbose:
                print("⚠️  Validation issues found:")
                for error in validation['errors']:
                    print(f"   - {error}")
        
        if validation['warnings'] and verbose:
            print("⚠️  Warnings:")
            for warning in validation['warnings']:
                print(f"   - {warning}")
        
        # Rebuild the vector store in place (same embedding model the bot queries with)
        if verbose:
            print("\n🗄️ Rebuilding vector database...")
        from langchain_chroma import Chroma
        from policy_agent import build_embeddings, chunk_id

        vectorstore = Chroma(
            persist_directory=VECTOR_DB_PATH,
            embedding_function=build_embeddings()
        )
        vectorstore.reset_collection()
        unique = {chunk_id(doc): doc for doc in documents}
        vectorstore.add_documents(list(unique.values()), ids=list(unique.keys()))

        if verbose:
            print(f"✅ New vector database created at {VECTOR_DB_PATH}")
        
        # Test the new database
        if verbose:
            print("\n🧪 Testing new knowledge base...")
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        
        test_queries = [
            "remote work policy",
            "vacation days",
            "dress code",
            "working hours"
        ]
        
        for query in test_queries:
            docs = retriever.invoke(query)
            if verbose:
                print(f"   Query: '{query}' → Found {len(docs)} relevant documents")
        
        if verbose:
            print("\n🎉 Knowledge base updated successfully!")
            print("✅ Your Policy Bot now has access to all the latest documents")
        
        return True
        
    except Exception as e:
        if verbose:
            print(f"❌ Error updating knowledge base: {e}")
        logger.error(f"Knowledge base update error: {e}", exc_info=True)
        return False


def main():
    """Main function to update the knowledge base."""
    print("🔄 Policy Bot Knowledge Base Updater")
    print("=" * 50)
    print("This script will:")
    print("1. Scan the documents directory for new files")
    print("2. Process all documents and create chunks")
    print("3. Create a new vector database")
    print("4. Test the updated knowledge base")
    print("=" * 50)
    
    success = update_knowledge_base()
    
    if success:
        print("\n🎉 Knowledge base update completed successfully!")
        print("📝 Next steps:")
        print("1. Configure your Google API key in .env file")
        print("2. Restart the API server so it picks up the new index: python api_server.py")
    else:
        print("\n❌ Knowledge base update failed. Please check the errors above.")


if __name__ == "__main__":
    main()
