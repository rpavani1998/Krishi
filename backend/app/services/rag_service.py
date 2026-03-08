import os
import logging
from typing import List, Optional
import shutil

from langchain_community.document_loaders import TextLoader, PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

class RAGService:
    """
    RAG Implementation using Open Source Components:
    - Embeddings: all-MiniLM-L6-v2 (Sentence Transformers)
    - Vector Store: ChromaDB (Local, Persistent)
    - LLM: For now, returns relevant context snippets.
      (To be extended with local LLM like Llama2-7b-chat via llama.cpp)
    """
    
    def __init__(self, persist_directory="./chroma_db"):
        # Check if running in Lambda with downloaded ChromaDB
        lambda_chroma_path = os.environ.get('CHROMA_DB_PATH')
        if lambda_chroma_path:
            persist_directory = lambda_chroma_path
            logger.info(f"Using Lambda ChromaDB path: {persist_directory}")
        
        self.persist_directory = persist_directory
        self.vectordb = None
        self.embedding_function = None

        try:
            # Try to load embeddings (requires internet for first download)
            self.embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            
            # Initialize/Load Vector Store only if embeddings loaded
            if os.path.exists(persist_directory):
                self.vectordb = Chroma(persist_directory=persist_directory, embedding_function=self.embedding_function)
                logger.info(f"Loaded existing ChromaDB from {persist_directory}")
            else:
                logger.info("ChromaDB not found. Will be created upon first ingestion.")
                
        except Exception as e:
            logger.error(f"Failed to initialize RAG Service (Embeddings): {e}")
            logger.warning("RAG functionality will be disabled.")

    def ingest_documents(self, source_directory: str):
        """
        Load documents, split, embed, and store in ChromaDB.
        """
        if not self.embedding_function:
            logger.error("Cannot ingest documents: Embeddings model not loaded.")
            return

        logger.info(f"Ingesting documents from {source_directory}...")
        
        # Load .txt, .md, and .pdf files
        loaders = [
            DirectoryLoader(source_directory, glob="**/*.txt", loader_cls=TextLoader),
            DirectoryLoader(source_directory, glob="**/*.md", loader_cls=TextLoader),
            DirectoryLoader(source_directory, glob="**/*.pdf", loader_cls=PyPDFLoader),
        ]
        
        documents = []
        for loader in loaders:
            try:
                documents.extend(loader.load())
            except Exception as e:
                logger.warning(f"Loader failed: {e}")
                
        if not documents:
            logger.warning("No documents found to ingest.")
            return

        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        
        logger.info(f"Created {len(chunks)} chunks from {len(documents)} documents.")
        
        # Store in Vector DB
        if self.vectordb:
            self.vectordb.add_documents(chunks)
        else:
            self.vectordb = Chroma.from_documents(
                documents=chunks, 
                embedding=self.embedding_function,
                persist_directory=self.persist_directory
            )
            
        self.vectordb.persist()
        logger.info("Documents ingested and persisted successfully.")

    def query(self, query_text: str, k: int = 3) -> str:
        """
        Retrieve relevant context for a query.
        """
        if not self.embedding_function or not self.vectordb:
            return "" # Return empty context if RAG is disabled
            
        results = self.vectordb.similarity_search(query_text, k=k)
        
        context = "\n\n".join([doc.page_content for doc in results])
        
        # In a full RAG, we would feed this context + query to an LLM.
        # Since we are "building the base", returning the retrieved context is the first step.
        return context

# Singleton instance management could go here, but RAGService is heavy, so instantiate on demand.
