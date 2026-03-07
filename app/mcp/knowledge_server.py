from app.mcp.base import BaseMCPServer, MCPTool, MCPResource, MCPPrompt
from typing import Dict, Any, List, Optional
from app.rag.retriever import RAGRetriever
from datetime import datetime, timedelta
import random


class KnowledgeMCPServer(BaseMCPServer):
    def __init__(self, rag_retriever: RAGRetriever):
        self.rag_retriever = rag_retriever
        super().__init__("knowledge")
    
    def _initialize(self):
        self.register_tool(MCPTool(
            name="semantic_search",
            description="Search documentation using semantic similarity",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "default": 5},
                    "filter": {"type": "object", "default": {}}
                },
                "required": ["query"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "results": {"type": "array"},
                    "total_found": {"type": "integer"}
                }
            },
            handler=self._semantic_search
        ))
        
                
        self.register_resource(MCPResource(
            uri="knowledge://docs/architecture",
            name="Architecture Documentation",
            description="System architecture and design documents",
            mime_type="text/markdown",
            content="""# System Architecture

## Overview
Our system follows a microservices architecture with the following key components:

- Auth Service: Handles authentication and authorization
- Payment Service: Processes payments and transactions
- User Service: Manages user profiles and preferences
- API Gateway: Routes requests to appropriate services

## Service Communication
Services communicate via REST APIs and message queues.

## Data Storage
- PostgreSQL for transactional data
- Redis for caching
- S3 for file storage
"""
        ))
        
        self.register_resource(MCPResource(
            uri="knowledge://docs/runbooks",
            name="Operational Runbooks",
            description="Runbooks for common operational tasks",
            mime_type="text/markdown",
            content="""# Operational Runbooks

## High Latency Response

1. Check service metrics
2. Review recent deployments
3. Check database query performance
4. Scale service if needed

## Service Down

1. Check service health endpoint
2. Review error logs
3. Restart service if needed
4. Escalate to on-call if issue persists
"""
        ))
        
        self.register_prompt(MCPPrompt(
            name="documentation_search",
            description="Search documentation with context",
            template="""Search the documentation for information about: {query}

Context: {context}

Provide relevant documentation excerpts and summaries.""",
            arguments=["query", "context"]
        ))
        
        # New Advanced Tools
        self.register_tool(MCPTool(
            name="document_versioning",
            description="Manage document versions and track changes",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["list_versions", "get_version", "compare_versions"]},
                    "document_id": {"type": "string"},
                    "version_id": {"type": "string"},
                    "compare_with": {"type": "string"}
                },
                "required": ["action", "document_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "versions": {"type": "array"},
                    "current_version": {"type": "string"},
                    "changes": {"type": "array"}
                }
            },
            handler=self._document_versioning
        ))
        
        self.register_tool(MCPTool(
            name="change_tracking",
            description="Track and audit document changes",
            input_schema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string"},
                    "time_range_days": {"type": "integer", "default": 30},
                    "author": {"type": "string"}
                },
                "required": ["document_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "changes": {"type": "array"},
                    "total_changes": {"type": "integer"},
                    "contributors": {"type": "array"}
                }
            },
            handler=self._change_tracking
        ))
        
        self.register_tool(MCPTool(
            name="recommendation_engine",
            description="Get document recommendations based on context",
            input_schema={
                "type": "object",
                "properties": {
                    "current_document": {"type": "string"},
                    "user_context": {"type": "object"},
                    "max_recommendations": {"type": "integer", "default": 5}
                },
                "required": ["current_document"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "recommendations": {"type": "array"},
                    "relevance_scores": {"type": "array"}
                }
            },
            handler=self._recommendation_engine
        ))
        
        self.register_tool(MCPTool(
            name="knowledge_graph_query",
            description="Query relationships between documents and concepts",
            input_schema={
                "type": "object",
                "properties": {
                    "entity": {"type": "string"},
                    "relationship_type": {"type": "string", "enum": ["related_to", "depends_on", "references", "all"]},
                    "depth": {"type": "integer", "default": 1}
                },
                "required": ["entity"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "nodes": {"type": "array"},
                    "edges": {"type": "array"},
                    "graph_summary": {"type": "string"}
                }
            },
            handler=self._knowledge_graph_query
        ))
    
    async def _semantic_search(
        self,
        query: str,
        top_k: int = 5,
        filter: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        results = await self.rag_retriever.search(query, k=top_k, filter=filter or {})
        
        return {
            "results": results,
            "total_found": len(results),
            "query": query
        }
    
        
    async def _document_versioning(
        self,
        action: str,
        document_id: str,
        version_id: Optional[str] = None,
        compare_with: Optional[str] = None
    ) -> Dict[str, Any]:
        if action == "list_versions":
            versions = []
            for i in range(random.randint(3, 8)):
                versions.append({
                    "version_id": f"v{i+1}.{random.randint(0, 9)}",
                    "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 90))).isoformat(),
                    "author": f"user_{random.randint(1, 10)}",
                    "changes_summary": f"Updated {random.choice(['content', 'metadata', 'structure'])}",
                    "size_bytes": random.randint(1000, 50000)
                })
            
            return {
                "versions": sorted(versions, key=lambda x: x["created_at"], reverse=True),
                "current_version": versions[0]["version_id"] if versions else "v1.0",
                "total_versions": len(versions),
                "document_id": document_id
            }
        
        elif action == "get_version":
            return {
                "version_id": version_id or "v1.0",
                "content": f"Document content for version {version_id}",
                "metadata": {
                    "created_at": datetime.utcnow().isoformat(),
                    "author": "user_1",
                    "tags": ["documentation", "api"]
                },
                "document_id": document_id
            }
        
        else:  # compare_versions
            changes = [
                {
                    "type": "addition",
                    "line": random.randint(10, 100),
                    "content": "+ New section added"
                },
                {
                    "type": "modification",
                    "line": random.randint(10, 100),
                    "content": "~ Updated description"
                },
                {
                    "type": "deletion",
                    "line": random.randint(10, 100),
                    "content": "- Removed deprecated info"
                }
            ]
            
            return {
                "version_1": version_id or "v1.0",
                "version_2": compare_with or "v2.0",
                "changes": changes,
                "total_changes": len(changes),
                "document_id": document_id
            }
    
    async def _change_tracking(
        self,
        document_id: str,
        time_range_days: int = 30,
        author: Optional[str] = None
    ) -> Dict[str, Any]:
        changes = []
        contributors = set()
        
        num_changes = random.randint(5, 20)
        
        for i in range(num_changes):
            change_author = author or f"user_{random.randint(1, 10)}"
            contributors.add(change_author)
            
            changes.append({
                "change_id": f"change_{i+1}",
                "timestamp": (datetime.utcnow() - timedelta(days=random.randint(0, time_range_days))).isoformat(),
                "author": change_author,
                "change_type": random.choice(["content_update", "metadata_update", "structure_change"]),
                "description": f"Change {i+1}: {random.choice(['Updated section', 'Fixed typo', 'Added example', 'Removed outdated info'])}",
                "lines_changed": random.randint(1, 50)
            })
        
        return {
            "changes": sorted(changes, key=lambda x: x["timestamp"], reverse=True),
            "total_changes": len(changes),
            "contributors": list(contributors),
            "document_id": document_id,
            "time_range_days": time_range_days
        }
    
    async def _recommendation_engine(
        self,
        current_document: str,
        user_context: Optional[Dict[str, Any]] = None,
        max_recommendations: int = 5
    ) -> Dict[str, Any]:
        recommendations = []
        relevance_scores = []
        
        doc_types = ["API Documentation", "Architecture Guide", "Tutorial", "Best Practices", "Troubleshooting Guide"]
        
        for i in range(min(max_recommendations, len(doc_types))):
            score = round(random.uniform(0.6, 0.95), 2)
            relevance_scores.append(score)
            
            recommendations.append({
                "document_id": f"doc_{i+1}",
                "title": f"{doc_types[i]} - Related Content",
                "type": doc_types[i],
                "relevance_score": score,
                "reason": random.choice([
                    "Frequently viewed together",
                    "Similar topics",
                    "Referenced in current document",
                    "Same category"
                ]),
                "preview": f"This document covers {doc_types[i].lower()} and is highly relevant..."
            })
        
        return {
            "recommendations": sorted(recommendations, key=lambda x: x["relevance_score"], reverse=True),
            "relevance_scores": sorted(relevance_scores, reverse=True),
            "current_document": current_document,
            "total_recommendations": len(recommendations)
        }
    
    async def _knowledge_graph_query(
        self,
        entity: str,
        relationship_type: str = "all",
        depth: int = 1
    ) -> Dict[str, Any]:
        nodes = [
            {
                "id": entity,
                "type": "primary",
                "label": entity,
                "properties": {"category": "service", "status": "active"}
            }
        ]
        
        edges = []
        
        # Generate related nodes
        related_entities = ["database", "cache", "api_gateway", "message_queue", "monitoring"]
        
        for i, related in enumerate(related_entities[:depth * 3]):
            node_id = f"{related}_{i}"
            nodes.append({
                "id": node_id,
                "type": "related",
                "label": related,
                "properties": {"category": "infrastructure"}
            })
            
            rel_type = random.choice(["depends_on", "references", "related_to"])
            if relationship_type != "all" and rel_type != relationship_type:
                continue
            
            edges.append({
                "source": entity,
                "target": node_id,
                "relationship": rel_type,
                "weight": round(random.uniform(0.5, 1.0), 2)
            })
        
        graph_summary = f"Found {len(nodes)} nodes and {len(edges)} relationships for '{entity}'"
        
        return {
            "nodes": nodes,
            "edges": edges,
            "graph_summary": graph_summary,
            "entity": entity,
            "depth": depth,
            "relationship_type": relationship_type
        }
