"""
Advanced Memory System with ChromaDB for SMARTII
Provides conversation history and semantic memory
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except (ImportError, AttributeError) as e:
    # Catch both ImportError and AttributeError (numpy compatibility issues)
    logger.warning(f"ChromaDB not available ({type(e).__name__}), using mock memory")
    CHROMADB_AVAILABLE = False


class AdvancedMemory:
    """Advanced memory system with vector search"""
    
    def __init__(self, persist_directory: str = "./data/memory"):
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        if CHROMADB_AVAILABLE:
            try:
                self.client = chromadb.Client(Settings(
                    persist_directory=persist_directory,
                    anonymized_telemetry=False
                ))
                
                # Create collections
                self.conversations = self.client.get_or_create_collection(
                    name="conversations",
                    metadata={"description": "Conversation history"}
                )
                
                self.facts = self.client.get_or_create_collection(
                    name="facts",
                    metadata={"description": "User facts and preferences"}
                )
                
                self.enabled = True
                logger.info("ChromaDB memory system initialized")
                
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB: {e}")
                self.enabled = False
                self._init_fallback()
        else:
            self.enabled = False
            self._init_fallback()
    
    def _init_fallback(self):
        """Initialize fallback JSON-based storage"""
        self.conversations_file = os.path.join(self.persist_directory, "conversations.json")
        self.facts_file = os.path.join(self.persist_directory, "facts.json")
        
        # Load existing data
        self._conversation_history = self._load_json(self.conversations_file, [])
        self._user_facts = self._load_json(self.facts_file, {})
    
    def _load_json(self, filepath: str, default: Any) -> Any:
        """Load JSON file"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
        return default
    
    def _save_json(self, filepath: str, data: Any):
        """Save JSON file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving {filepath}: {e}")
    
    def store_conversation(self, user_message: str, ai_response: str, client_id: str, metadata: Optional[Dict] = None):
        """Store conversation in memory"""
        try:
            timestamp = datetime.now().isoformat()
            
            if self.enabled and CHROMADB_AVAILABLE:
                # Store in ChromaDB
                doc_id = f"{client_id}_{timestamp}"
                
                self.conversations.add(
                    documents=[f"User: {user_message}\nAI: {ai_response}"],
                    metadatas=[{
                        "timestamp": timestamp,
                        "client_id": client_id,
                        "user_message": user_message,
                        "ai_response": ai_response,
                        **(metadata or {})
                    }],
                    ids=[doc_id]
                )
            else:
                # Fallback to JSON
                entry = {
                    "timestamp": timestamp,
                    "client_id": client_id,
                    "user_message": user_message,
                    "ai_response": ai_response,
                    "metadata": metadata or {}
                }
                
                self._conversation_history.append(entry)
                
                # Keep last 1000 conversations
                if len(self._conversation_history) > 1000:
                    self._conversation_history = self._conversation_history[-1000:]
                
                self._save_json(self.conversations_file, self._conversation_history)
            
            logger.debug(f"Stored conversation for {client_id}")
            
        except Exception as e:
            logger.error(f"Error storing conversation: {e}")
    
    def search_conversations(self, query: str, client_id: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Search past conversations"""
        try:
            if self.enabled and CHROMADB_AVAILABLE:
                # Vector search
                where_filter = {"client_id": client_id} if client_id else None
                
                results = self.conversations.query(
                    query_texts=[query],
                    n_results=limit,
                    where=where_filter
                )
                
                conversations = []
                if results and results['documents']:
                    for i, doc in enumerate(results['documents'][0]):
                        metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                        conversations.append({
                            "content": doc,
                            "timestamp": metadata.get("timestamp"),
                            "user_message": metadata.get("user_message"),
                            "ai_response": metadata.get("ai_response"),
                            "relevance": results['distances'][0][i] if results.get('distances') else 0
                        })
                
                return conversations
            else:
                # Fallback: simple keyword search
                results = []
                query_lower = query.lower()
                
                for entry in reversed(self._conversation_history):
                    if client_id and entry["client_id"] != client_id:
                        continue
                    
                    if query_lower in entry["user_message"].lower() or query_lower in entry["ai_response"].lower():
                        results.append({
                            "content": f"User: {entry['user_message']}\nAI: {entry['ai_response']}",
                            "timestamp": entry["timestamp"],
                            "user_message": entry["user_message"],
                            "ai_response": entry["ai_response"]
                        })
                        
                        if len(results) >= limit:
                            break
                
                return results
                
        except Exception as e:
            logger.error(f"Error searching conversations: {e}")
            return []
    
    def store_fact(self, fact: str, category: str, client_id: str):
        """Store a fact about the user"""
        try:
            timestamp = datetime.now().isoformat()
            
            if self.enabled and CHROMADB_AVAILABLE:
                doc_id = f"{client_id}_{category}_{timestamp}"
                
                self.facts.add(
                    documents=[fact],
                    metadatas=[{
                        "timestamp": timestamp,
                        "client_id": client_id,
                        "category": category
                    }],
                    ids=[doc_id]
                )
            else:
                # Fallback to JSON
                if client_id not in self._user_facts:
                    self._user_facts[client_id] = {}
                
                if category not in self._user_facts[client_id]:
                    self._user_facts[client_id][category] = []
                
                self._user_facts[client_id][category].append({
                    "fact": fact,
                    "timestamp": timestamp
                })
                
                self._save_json(self.facts_file, self._user_facts)
            
            logger.info(f"Stored fact for {client_id}: {fact}")
            
        except Exception as e:
            logger.error(f"Error storing fact: {e}")
    
    def get_facts(self, client_id: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve stored facts"""
        try:
            if self.enabled and CHROMADB_AVAILABLE:
                where_filter = {"client_id": client_id}
                if category:
                    where_filter["category"] = category
                
                results = self.facts.get(where=where_filter)
                
                facts = []
                if results and results['documents']:
                    for i, doc in enumerate(results['documents']):
                        metadata = results['metadatas'][i] if results['metadatas'] else {}
                        facts.append({
                            "fact": doc,
                            "category": metadata.get("category"),
                            "timestamp": metadata.get("timestamp")
                        })
                
                return facts
            else:
                # Fallback to JSON
                if client_id not in self._user_facts:
                    return []
                
                facts = []
                user_data = self._user_facts[client_id]
                
                if category:
                    facts = user_data.get(category, [])
                else:
                    for cat, cat_facts in user_data.items():
                        facts.extend([{**f, "category": cat} for f in cat_facts])
                
                return facts
                
        except Exception as e:
            logger.error(f"Error retrieving facts: {e}")
            return []
    
    def get_recent_context(self, client_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent conversation context"""
        try:
            if self.enabled and CHROMADB_AVAILABLE:
                results = self.conversations.get(
                    where={"client_id": client_id},
                    limit=limit
                )
                
                conversations = []
                if results and results['documents']:
                    for i, doc in enumerate(results['documents']):
                        metadata = results['metadatas'][i] if results['metadatas'] else {}
                        conversations.append({
                            "user_message": metadata.get("user_message"),
                            "ai_response": metadata.get("ai_response"),
                            "timestamp": metadata.get("timestamp")
                        })
                
                # Sort by timestamp (most recent first)
                conversations.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                return conversations[:limit]
            else:
                # Fallback to JSON
                recent = []
                for entry in reversed(self._conversation_history):
                    if entry["client_id"] == client_id:
                        recent.append({
                            "user_message": entry["user_message"],
                            "ai_response": entry["ai_response"],
                            "timestamp": entry["timestamp"]
                        })
                        
                        if len(recent) >= limit:
                            break
                
                return recent
                
        except Exception as e:
            logger.error(f"Error getting recent context: {e}")
            return []


# Global instance
_advanced_memory = None


def get_advanced_memory() -> AdvancedMemory:
    """Get or create global memory instance"""
    global _advanced_memory
    if _advanced_memory is None:
        _advanced_memory = AdvancedMemory()
    return _advanced_memory
