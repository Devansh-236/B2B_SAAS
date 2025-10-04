"""
Setup script for the Policy Bot knowledge base.

This script helps you set up the knowledge base by processing documents
and creating the vector database.
"""

import os
import sys
import logging
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from document_processor import document_processor
from policy_agent import policy_bot
from config import KNOWLEDGE_BASE_DIR

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_knowledge_base():
    """Set up the knowledge base by processing documents."""
    
    print("🤖 Policy Bot Knowledge Base Setup")
    print("=" * 50)
    
    # Check if documents directory exists
    docs_dir = Path(KNOWLEDGE_BASE_DIR)
    if not docs_dir.exists():
        print(f"❌ Documents directory not found: {docs_dir}")
        print(f"📁 Creating directory: {docs_dir}")
        docs_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Please add your policy documents to: {docs_dir}")
        print("   Supported formats: PDF, DOCX, DOC, TXT")
        return False
    
    # Check if there are any documents
    supported_files = []
    for ext in ['.pdf', '.docx', '.doc', '.txt']:
        supported_files.extend(list(docs_dir.glob(f"*{ext}")))
    
    if not supported_files:
        print(f"❌ No supported documents found in: {docs_dir}")
        print("   Supported formats: PDF, DOCX, DOC, TXT")
        return False
    
    print(f"📚 Found {len(supported_files)} documents to process:")
    for file in supported_files:
        print(f"   - {file.name}")
    
    # Process documents
    print("\n🔄 Processing documents...")
    try:
        documents = document_processor.process_documents_from_directory()
        
        if not documents:
            print("❌ No documents were successfully processed")
            return False
        
        # Get document info
        doc_info = document_processor.get_document_info(documents)
        print(f"✅ Successfully processed {doc_info['total_chunks']} chunks from {doc_info['total_documents']} documents")
        
        # Validate documents
        validation = document_processor.validate_documents(documents)
        if not validation['valid']:
            print("⚠️  Validation issues found:")
            for error in validation['errors']:
                print(f"   - {error}")
        
        if validation['warnings']:
            print("⚠️  Warnings:")
            for warning in validation['warnings']:
                print(f"   - {warning}")
        
        # Add documents to vector store
        print("\n🔄 Creating vector database...")
        policy_bot.add_documents(documents)
        
        # Test the setup
        print("\n🧪 Testing the setup...")
        test_response = policy_bot.ask_question("What is the company policy on remote work?")
        
        if test_response['status'] == 'success':
            print("✅ Knowledge base setup completed successfully!")
            print(f"📊 Vector database created with {policy_bot.get_knowledge_base_stats()['total_documents']} documents")
            return True
        else:
            print("❌ Test failed. Please check your configuration.")
            return False
            
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        logger.error(f"Setup error: {e}", exc_info=True)
        return False


def main():
    """Main function to run the setup."""
    print("Starting Policy Bot Knowledge Base Setup...")
    
    # Check if API key is configured
    from config import LLM_API_KEY
    if LLM_API_KEY == "YOUR_GOOGLE_API_KEY_HERE":
        print("❌ Please configure your Google API key first!")
        print("1. Copy env_template.txt to .env")
        print("2. Add your Google API key to the .env file")
        print("3. Get your API key from: https://makersuite.google.com/app/apikey")
        return
    
    success = setup_knowledge_base()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("You can now use the Policy Bot to answer questions.")
        print("\nNext steps:")
        print("1. Run: python api_server.py (to start the API server)")
        print("2. Or use the Policy Bot directly in your code")
    else:
        print("\n❌ Setup failed. Please check the errors above.")


if __name__ == "__main__":
    main()
