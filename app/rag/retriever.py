from typing import List, Dict, Any, Optional
from langchain_openai import AzureOpenAIEmbeddings
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
import faiss
import numpy as np
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings
from app.core.logging import logger
import pickle
import asyncio

class RAGRetriever:
    def __init__(self, embeddings: Optional[AzureOpenAIEmbeddings] = None):
        self.embeddings = embeddings
        self.dimension = settings.embedding_dimension
        # Use rag/ subfolder for RAG knowledge base
        self.store_path = Path(settings.vector_store_path) / "rag"
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        self.index: Optional[faiss.IndexFlatL2] = None
        self.documents: List[Dict[str, Any]] = []
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # Only load existing index if no embeddings provided (backward compatibility)
        # When embeddings are provided, start fresh and let caller load documents
        if embeddings is None:
            self._load_index()
        else:
            self._initialize_index()
    
    def set_embeddings(self, embeddings: AzureOpenAIEmbeddings):
        """
        Set or update embeddings model after initialization.
        Allows lazy initialization when embeddings are not available at construction time.
        """
        self.embeddings = embeddings
        logger.info_structured("RAGRetriever embeddings configured")
    
    def _get_index_path(self) -> Path:
        return self.store_path / "rag_index.faiss"
    
    def _get_docs_path(self) -> Path:
        return self.store_path / "rag_documents.pkl"
    
    def _load_index(self):
        index_path = self._get_index_path()
        docs_path = self._get_docs_path()
        
        if index_path.exists() and docs_path.exists():
            try:
                self.index = faiss.read_index(str(index_path))
                with open(docs_path, 'rb') as f:
                    self.documents = pickle.load(f)
                
                logger.info_structured(
                    "Loaded RAG index",
                    doc_count=len(self.documents),
                    index_size=self.index.ntotal if self.index else 0
                )
            except Exception as e:
                logger.error_structured("Failed to load RAG index", error=str(e))
                self._initialize_index()
        else:
            self._initialize_index()
    
    def _initialize_index(self):
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []
        logger.info_structured("Initialized new RAG index")
    
    def _save_index(self):
        try:
            index_path = self._get_index_path()
            docs_path = self._get_docs_path()
            
            if self.index:
                faiss.write_index(self.index, str(index_path))
            
            with open(docs_path, 'wb') as f:
                pickle.dump(self.documents, f)
            
            logger.info_structured("Saved RAG index", doc_count=len(self.documents))
        except Exception as e:
            logger.error_structured("Failed to save RAG index", error=str(e))
    
    async def add_documents(self, documents: List[Dict[str, Any]]):
        for doc in documents:
            await self.add_document(doc)
    
    async def add_document(self, document: Dict[str, Any], max_retries: int = 3):
        try:
            if not self.embeddings:
                logger.warning_structured(
                    "Cannot add document - embeddings not configured",
                    document_id=document.get("id")
                )
                return
            
            content = document.get("content", "")
            if not content:
                return
            
            chunks = self.text_splitter.split_text(content)
            
            for i, chunk in enumerate(chunks):
                # Retry logic for embedding generation
                embedding = None
                for attempt in range(max_retries):
                    try:
                        embedding = await self.embeddings.aembed_query(chunk)
                        break
                    except Exception as embed_error:
                        if attempt < max_retries - 1:
                            logger.warning_structured(
                                "Embedding generation failed, retrying",
                                attempt=attempt + 1,
                                error=str(embed_error)
                            )
                            await asyncio.sleep(1 * (attempt + 1))
                        else:
                            logger.error_structured(
                                "Embedding generation failed after retries",
                                document_id=document.get("id"),
                                chunk_index=i,
                                error=str(embed_error)
                            )
                            raise
                
                if embedding is None:
                    continue
                
                embedding_array = np.array([embedding], dtype=np.float32)
                
                if self.index is None:
                    self._initialize_index()
                
                self.index.add(embedding_array)
                
                chunk_doc = {
                    "content": chunk,
                    "metadata": document.get("metadata", {}),
                    "document_id": document.get("id", f"doc_{len(self.documents)}"),
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
                self.documents.append(chunk_doc)
            
            self._save_index()
            
            logger.info_structured(
                "Added document to RAG",
                document_id=document.get("id"),
                chunks=len(chunks)
            )
        except Exception as e:
            logger.error_structured(
                "Failed to add document",
                document_id=document.get("id"),
                error=str(e),
                error_type=type(e).__name__
            )
    
    async def search(
        self,
        query: str,
        k: int = 5,
        filter: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        if not self.embeddings:
            logger.warning_structured("Cannot search - embeddings not configured")
            return []
        
        if not self.index or self.index.ntotal == 0:
            logger.warning_structured("RAG index is empty")
            return []
        
        try:
            query_embedding = await self.embeddings.aembed_query(query)
            query_array = np.array([query_embedding], dtype=np.float32)
            
            k = min(k, self.index.ntotal)
            distances, indices = self.index.search(query_array, k)
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.documents):
                    doc = self.documents[idx].copy()
                    doc["score"] = float(distances[0][i])
                    doc["rank"] = i + 1
                    
                    if filter:
                        if all(doc.get("metadata", {}).get(k) == v for k, v in filter.items()):
                            results.append(doc)
                    else:
                        results.append(doc)
            
            logger.info_structured(
                "RAG search completed",
                query_length=len(query),
                results_found=len(results)
            )
            
            return results
        except Exception as e:
            logger.error_structured("RAG search failed", error=str(e))
            return []
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        for doc in self.documents:
            if doc.get("document_id") == document_id:
                return doc
        return None
    
    async def load_documents_from_directory(self, docs_dir: str = "data/docs", force_reload: bool = False):
        """
        Load markdown documents from the specified directory.
        
        Args:
            docs_dir: Path to directory containing markdown files
            force_reload: If True, reload documents even if index already exists
        """
        if not self.embeddings:
            logger.warning_structured("Cannot load documents - embeddings not configured")
            return
        
        # Check if we already have data (skip if force_reload is True)
        if not force_reload and self.index and self.index.ntotal > 0:
            logger.info_structured(
                "RAG already initialized with data",
                doc_count=len(self.documents)
            )
            return
        
        # If force_reload, clear existing data
        if force_reload:
            self._initialize_index()
            logger.info_structured("Force reloading RAG documents")
        
        docs_path = Path(docs_dir)
        if not docs_path.exists():
            logger.warning_structured(
                "Documents directory not found",
                path=str(docs_path)
            )
            return
        
        try:
            success_count = 0
            total_files = 0
            
            # Load all markdown, text, and SQL files from directory
            doc_files = list(docs_path.glob("*.md")) + list(docs_path.glob("*.txt")) + list(docs_path.glob("*.sql"))
            
            # Also load SQL files from database init scripts directory
            db_init_path = Path("databases/init-scripts")
            if db_init_path.exists():
                for sql_file in db_init_path.rglob("01-init.sql"):  # Only load schema files, not data files
                    doc_files.append(sql_file)
            
            for doc_file in doc_files:
                total_files += 1
                try:
                    with open(doc_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Determine document type and category from filename
                    filename = doc_file.stem
                    doc_type = "documentation"
                    category = "general"
                    
                    if "architecture" in filename.lower():
                        doc_type = "architecture"
                        category = "system_design"
                    elif "runbook" in filename.lower():
                        doc_type = "runbook"
                        category = "operations"
                    elif "slo" in filename.lower() or "policy" in filename.lower():
                        doc_type = "policy"
                        category = "slo"
                    elif "langgraph" in filename.lower():
                        doc_type = "framework"
                        category = "technology"
                    elif doc_file.suffix == ".sql":
                        doc_type = "database_schema"
                        category = "database"
                        # Determine which database from path
                        if "sales" in str(doc_file).lower():
                            category = "database_sales"
                        elif "inventory" in str(doc_file).lower():
                            category = "database_inventory"
                    
                    document = {
                        "id": filename,
                        "content": content,
                        "metadata": {
                            "type": doc_type,
                            "category": category,
                            "filename": doc_file.name,
                            "source": str(doc_file)
                        }
                    }
                    
                    await self.add_document(document)
                    success_count += 1
                    
                    logger.info_structured(
                        "Loaded document into RAG",
                        filename=doc_file.name,
                        type=doc_type,
                        category=category
                    )
                    
                except Exception as doc_error:
                    logger.warning_structured(
                        "Failed to load document, continuing",
                        filename=doc_file.name,
                        error=str(doc_error)
                    )
            
            logger.info_structured(
                "Initialized RAG with documents from directory",
                doc_count=success_count,
                total_files=total_files,
                docs_dir=str(docs_path)
            )
        except Exception as e:
            logger.error_structured(
                "Failed to load documents from directory",
                error=str(e),
                error_type=type(e).__name__,
                docs_dir=str(docs_path)
            )
    
    async def initialize_with_sample_data(self):
        """
        Initialize RAG with documents from data/docs directory.
        This method is kept for backward compatibility.
        """
        await self.load_documents_from_directory("data/docs")
