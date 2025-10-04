"""
Policy Bot Agent

This agent specializes in answering employee questions by searching
a knowledge base of company policies using RAG (Retrieval-Augmented Generation).
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

from config import (
    LLM_API_KEY, LLM_MODEL_NAME, VECTOR_DB_PATH, EMBEDDING_MODEL,
    CHUNK_SIZE, CHUNK_OVERLAP, MAX_CHUNKS_RETRIEVED, COMPANY_NAME,
    BOT_NAME, MAX_ANSWER_LENGTH
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PolicyBot:
    """
    The Policy Bot agent that answers employee questions using RAG.
    """
    
    def __init__(self):
        """Initialize the Policy Bot with necessary components."""
        self.company_name = COMPANY_NAME
        self.bot_name = BOT_NAME
        self.vector_db_path = VECTOR_DB_PATH
        
        # Initialize components
        self.embeddings = None
        self.vectorstore = None
        self.llm = None
        self.retriever = None
        self.chain = None
        
        # Initialize the bot
        self._initialize_components()
        
    def _initialize_components(self):
        """Initialize all the necessary components for the RAG pipeline."""
        try:
            logger.info("Initializing Policy Bot components...")
            
            # Initialize embeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL,
                model_kwargs={'device': 'cpu'}
            )
            
            # Initialize LLM
            self.llm = ChatGoogleGenerativeAI(
                model=LLM_MODEL_NAME,
                google_api_key=LLM_API_KEY,
                temperature=0.1,
                max_output_tokens=MAX_ANSWER_LENGTH
            )
            
            # Load or create vector store
            self._load_vectorstore()
            
            # Create the RAG chain
            self._create_rag_chain()
            
            logger.info("Policy Bot components initialized successfully!")
            
        except Exception as e:
            logger.error(f"Error initializing Policy Bot components: {e}")
            raise
    
    def _load_vectorstore(self):
        """Load the existing vector store or create a new one."""
        try:
            # Try to load existing vector store
            self.vectorstore = Chroma(
                persist_directory=self.vector_db_path,
                embedding_function=self.embeddings
            )
            
            # Check if vector store has documents
            if self.vectorstore._collection.count() == 0:
                logger.warning("Vector store is empty. Please add documents first.")
                self.vectorstore = None
            else:
                logger.info(f"Loaded vector store with {self.vectorstore._collection.count()} documents")
                
        except Exception as e:
            logger.warning(f"Could not load existing vector store: {e}")
            self.vectorstore = None
    
    def _create_rag_chain(self):
        """Create the RAG chain for question answering."""
        if not self.vectorstore:
            logger.warning("Cannot create RAG chain: No vector store available")
            return
            
        # Create retriever
        self.retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": MAX_CHUNKS_RETRIEVED}
        )

        # Create prompt template with bot_name and company_name pre-filled
        prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template=f"""You are {self.bot_name}, an internal HR Policy Bot for {self.company_name}. 
        Your role is to answer employee questions accurately based ONLY on the provided context from official policy documents.

        Instructions:
        1. Answer the question using ONLY the information provided in the context
        2. If the answer is not in the context, say "I cannot find the answer in the official policy documents. Please contact HR for assistance."
        3. Be concise but complete in your answers
        4. Always cite which document or section the information comes from when possible
        5. If the question is unclear, ask for clarification

        Context from policy documents:
        {{context}}

        Question: {{question}}

        Answer:"""
        )

        # Create the chain
        self.chain = (
            {"context": self.retriever, "question": RunnablePassthrough()}
            | prompt_template
            | self.llm
            | StrOutputParser()
        )
    
    def add_documents(self, documents: List[Document]):
        """Add documents to the knowledge base."""
        try:
            if not self.vectorstore:
                # Create new vector store
                self.vectorstore = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    persist_directory=self.vector_db_path
                )
            else:
                # Add to existing vector store
                self.vectorstore.add_documents(documents)
            
            # Persist the changes
            self.vectorstore.persist()
            
            # Recreate the RAG chain with updated vector store
            self._create_rag_chain()
            
            logger.info(f"Successfully added {len(documents)} documents to knowledge base")
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    def ask_question(self, question: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Answer a policy question using the RAG pipeline.
        
        Args:
            question: The employee's question
            user_id: Optional user identifier for logging
            
        Returns:
            Dictionary containing the answer and metadata
        """
        try:
            if not self.chain:
                return {
                    "answer": "I'm sorry, but I don't have access to the policy documents yet. Please contact HR for assistance.",
                    "status": "error",
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id
                }
            
            logger.info(f"Processing question from user {user_id}: {question}")
            
            # Get answer from RAG chain
            answer = self.chain.invoke(question)
            
            # Get retrieved documents for context
            retrieved_docs = self.retriever.invoke(question)
            
            response = {
                "answer": answer,
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "question": question,
                "sources": [
                    {
                        "content": doc.page_content[:200] + "...",
                        "metadata": doc.metadata
                    }
                    for doc in retrieved_docs
                ],
                "num_sources": len(retrieved_docs)
            }
            
            logger.info(f"Successfully answered question for user {user_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {
                "answer": "I'm sorry, I encountered an error while processing your question. Please try again or contact HR for assistance.",
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "error": str(e)
            }
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base."""
        try:
            if not self.vectorstore:
                return {
                    "total_documents": 0,
                    "status": "no_vectorstore"
                }
            
            count = self.vectorstore._collection.count()
            return {
                "total_documents": count,
                "status": "active",
                "vector_db_path": self.vector_db_path
            }
            
        except Exception as e:
            logger.error(f"Error getting knowledge base stats: {e}")
            return {
                "total_documents": 0,
                "status": "error",
                "error": str(e)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the Policy Bot."""
        try:
            stats = self.get_knowledge_base_stats()
            
            # Test with a simple question
            test_response = self.ask_question("What is the company policy on remote work?")
            
            return {
                "status": "healthy" if test_response["status"] == "success" else "degraded",
                "knowledge_base": stats,
                "llm_available": self.llm is not None,
                "vectorstore_available": self.vectorstore is not None,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Global instance
policy_bot = PolicyBot()
