from typing import List, Dict, Any, Optional
import faiss
import numpy as np
import pickle
import os
from pathlib import Path
from langchain_core.messages import BaseMessage
from langchain_openai import AzureOpenAIEmbeddings
from app.core.config import settings
from app.core.logging import logger


class VectorMemoryStore:
    def __init__(self, embeddings: AzureOpenAIEmbeddings):
        self.embeddings = embeddings
        self.dimension = settings.embedding_dimension
        # Use conversations/ subfolder for conversation memory
        self.store_path = Path(settings.vector_store_path) / "conversations"
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        self.indices: Dict[str, faiss.IndexFlatL2] = {}
        self.documents: Dict[str, List[Dict[str, Any]]] = {}
        
        self._load_stores()
    
    def _get_index_path(self, conversation_id: str) -> Path:
        return self.store_path / f"{conversation_id}.index"
    
    def _get_docs_path(self, conversation_id: str) -> Path:
        return self.store_path / f"{conversation_id}.pkl"
    
    def _load_stores(self):
        for index_file in self.store_path.glob("*.index"):
            conversation_id = index_file.stem
            try:
                index = faiss.read_index(str(index_file))
                self.indices[conversation_id] = index
                
                docs_file = self._get_docs_path(conversation_id)
                if docs_file.exists():
                    with open(docs_file, 'rb') as f:
                        self.documents[conversation_id] = pickle.load(f)
                
                logger.info_structured(
                    "Loaded vector store",
                    conversation_id=conversation_id,
                    doc_count=len(self.documents.get(conversation_id, []))
                )
            except Exception as e:
                logger.error_structured(
                    "Failed to load vector store",
                    conversation_id=conversation_id,
                    error=str(e)
                )
    
    def _save_store(self, conversation_id: str):
        try:
            if conversation_id in self.indices:
                index_path = self._get_index_path(conversation_id)
                faiss.write_index(self.indices[conversation_id], str(index_path))
            
            if conversation_id in self.documents:
                docs_path = self._get_docs_path(conversation_id)
                with open(docs_path, 'wb') as f:
                    pickle.dump(self.documents[conversation_id], f)
            
            logger.debug_structured("Saved vector store", conversation_id=conversation_id)
        except Exception as e:
            logger.error_structured(
                "Failed to save vector store",
                conversation_id=conversation_id,
                error=str(e)
            )
    
    def _get_or_create_index(self, conversation_id: str) -> faiss.IndexFlatL2:
        if conversation_id not in self.indices:
            self.indices[conversation_id] = faiss.IndexFlatL2(self.dimension)
            self.documents[conversation_id] = []
        
        return self.indices[conversation_id]
    
    async def add_message(
        self,
        conversation_id: str,
        message: BaseMessage,
        metadata: Optional[Dict[str, Any]] = None
    ):
        try:
            content = message.content
            if not content or not isinstance(content, str):
                return
            
            embedding = await self.embeddings.aembed_query(content)
            embedding_array = np.array([embedding], dtype=np.float32)
            
            index = self._get_or_create_index(conversation_id)
            index.add(embedding_array)
            
            doc = {
                "content": content,
                "type": message.__class__.__name__,
                "metadata": metadata or {}
            }
            self.documents[conversation_id].append(doc)
            
            self._save_store(conversation_id)
            
            logger.debug_structured(
                "Added message to vector store",
                conversation_id=conversation_id,
                message_type=message.__class__.__name__
            )
        except Exception as e:
            logger.error_structured(
                "Failed to add message to vector store",
                error=str(e),
                conversation_id=conversation_id
            )
    
    async def search(
        self,
        conversation_id: str,
        query: str,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        if conversation_id not in self.indices:
            return []
        
        try:
            query_embedding = await self.embeddings.aembed_query(query)
            query_array = np.array([query_embedding], dtype=np.float32)
            
            index = self.indices[conversation_id]
            docs = self.documents[conversation_id]
            
            if index.ntotal == 0:
                return []
            
            k = min(k, index.ntotal)
            distances, indices = index.search(query_array, k)
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(docs):
                    result = docs[idx].copy()
                    result["score"] = float(distances[0][i])
                    results.append(result)
            
            return results
        except Exception as e:
            logger.error_structured(
                "Vector search failed",
                error=str(e),
                conversation_id=conversation_id
            )
            return []
