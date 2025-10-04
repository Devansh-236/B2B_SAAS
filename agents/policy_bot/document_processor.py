"""
Document processing utilities for the Policy Bot.

This module handles loading, parsing, and chunking of various document formats
to prepare them for the RAG pipeline.
"""

import os
import logging
from typing import List, Dict, Any
from pathlib import Path

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    DirectoryLoader
)

from config import (
    KNOWLEDGE_BASE_DIR, CHUNK_SIZE, CHUNK_OVERLAP
)

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Handles document loading, parsing, and chunking for the Policy Bot.
    """
    
    def __init__(self):
        """Initialize the document processor."""
        self.knowledge_base_dir = Path(KNOWLEDGE_BASE_DIR)
        self.knowledge_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Supported file extensions
        self.supported_extensions = {
            '.pdf': PyPDFLoader,
            '.docx': Docx2txtLoader,
            '.doc': Docx2txtLoader,
            '.txt': TextLoader
        }
    
    def load_documents_from_directory(self, directory_path: str = None) -> List[Document]:
        """
        Load all supported documents from a directory.
        
        Args:
            directory_path: Path to directory containing documents
            
        Returns:
            List of Document objects
        """
        if directory_path is None:
            directory_path = self.knowledge_base_dir
        
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            logger.warning(f"Directory {directory_path} does not exist")
            return []
        
        documents = []
        
        # Load documents by extension
        for ext, loader_class in self.supported_extensions.items():
            try:
                # Find all files with this extension
                files = list(directory_path.glob(f"*{ext}"))
                
                for file_path in files:
                    try:
                        logger.info(f"Loading document: {file_path}")
                        loader = loader_class(str(file_path))
                        docs = loader.load()
                        
                        # Add metadata
                        for doc in docs:
                            doc.metadata.update({
                                'source': str(file_path),
                                'filename': file_path.name,
                                'file_type': ext[1:],  # Remove the dot
                                'file_size': file_path.stat().st_size
                            })
                        
                        documents.extend(docs)
                        logger.info(f"Successfully loaded {len(docs)} pages from {file_path}")
                        
                    except Exception as e:
                        logger.error(f"Error loading {file_path}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error processing {ext} files: {e}")
                continue
        
        logger.info(f"Total documents loaded: {len(documents)}")
        return documents
    
    def load_single_document(self, file_path: str) -> List[Document]:
        """
        Load a single document.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List of Document objects
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File {file_path} does not exist")
            return []
        
        ext = file_path.suffix.lower()
        
        if ext not in self.supported_extensions:
            logger.error(f"Unsupported file type: {ext}")
            return []
        
        try:
            logger.info(f"Loading document: {file_path}")
            loader_class = self.supported_extensions[ext]
            loader = loader_class(str(file_path))
            documents = loader.load()
            
            # Add metadata
            for doc in documents:
                doc.metadata.update({
                    'source': str(file_path),
                    'filename': file_path.name,
                    'file_type': ext[1:],
                    'file_size': file_path.stat().st_size
                })
            
            logger.info(f"Successfully loaded {len(documents)} pages from {file_path}")
            return documents
            
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return []
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into smaller chunks for better retrieval.
        
        Args:
            documents: List of Document objects to chunk
            
        Returns:
            List of chunked Document objects
        """
        if not documents:
            logger.warning("No documents to chunk")
            return []
        
        try:
            logger.info(f"Chunking {len(documents)} documents...")
            chunked_docs = self.text_splitter.split_documents(documents)
            
            # Add chunk metadata
            for i, doc in enumerate(chunked_docs):
                doc.metadata.update({
                    'chunk_id': i,
                    'chunk_size': len(doc.page_content)
                })
            
            logger.info(f"Created {len(chunked_docs)} chunks from {len(documents)} documents")
            return chunked_docs
            
        except Exception as e:
            logger.error(f"Error chunking documents: {e}")
            return []
    
    def process_documents_from_directory(self, directory_path: str = None) -> List[Document]:
        """
        Complete pipeline: load and chunk documents from a directory.
        
        Args:
            directory_path: Path to directory containing documents
            
        Returns:
            List of processed Document objects ready for vector store
        """
        # Load documents
        documents = self.load_documents_from_directory(directory_path)
        
        if not documents:
            logger.warning("No documents found to process")
            return []
        
        # Chunk documents
        chunked_documents = self.chunk_documents(documents)
        
        return chunked_documents
    
    def get_document_info(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Get information about processed documents.
        
        Args:
            documents: List of Document objects
            
        Returns:
            Dictionary with document statistics
        """
        if not documents:
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "file_types": {},
                "total_size": 0
            }
        
        file_types = {}
        total_size = 0
        sources = set()
        
        for doc in documents:
            # Count file types
            file_type = doc.metadata.get('file_type', 'unknown')
            file_types[file_type] = file_types.get(file_type, 0) + 1
            
            # Sum file sizes
            file_size = doc.metadata.get('file_size', 0)
            total_size += file_size
            
            # Collect sources
            source = doc.metadata.get('source', 'unknown')
            sources.add(source)
        
        return {
            "total_documents": len(sources),
            "total_chunks": len(documents),
            "file_types": file_types,
            "total_size": total_size,
            "sources": list(sources)
        }
    
    def validate_documents(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Validate processed documents for quality.
        
        Args:
            documents: List of Document objects
            
        Returns:
            Dictionary with validation results
        """
        if not documents:
            return {
                "valid": False,
                "errors": ["No documents to validate"],
                "warnings": []
            }
        
        errors = []
        warnings = []
        
        for i, doc in enumerate(documents):
            # Check for empty content
            if not doc.page_content.strip():
                errors.append(f"Document {i} has empty content")
            
            # Check for very short content
            elif len(doc.page_content.strip()) < 50:
                warnings.append(f"Document {i} has very short content ({len(doc.page_content)} chars)")
            
            # Check for missing metadata
            if not doc.metadata.get('source'):
                warnings.append(f"Document {i} missing source metadata")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "total_documents": len(documents)
        }


# Global instance
document_processor = DocumentProcessor()
