"""
SMARTII Memory Engine - Episodic, Semantic, and Vector Memory
Handles user preferences, conversation history, task memory, and long-term learning.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import os

# Import vector database (will be installed via requirements.txt)
try:
    import faiss
    import chromadb
    from chromadb.config import Settings
except ImportError:
    logging.warning("Vector databases not available, using mock implementations")
    faiss = None
    chromadb = None

logger = logging.getLogger(__name__)

class MemoryEngine:
    """Advanced memory system with multiple memory types and vector search capabilities."""

    def __init__(self):
        self.episodic_memory = {}  # Event-based memories
        self.semantic_memory = {}  # Factual knowledge
        self.user_preferences = {}  # User-specific settings
        self.conversation_history = {}  # Chat history per user
        self.routines_memory = {}  # User routines and habits
        self.task_history = {}  # Completed tasks history
        self.user_habits = {}  # Learned behavioral patterns
        self.vector_store = None
        self.chroma_client = None
        self.initialized = False

    async def initialize(self):
        """Initialize the memory engine and databases."""
        try:
            # Initialize ChromaDB for vector storage
            if chromadb:
                self.chroma_client = chromadb.PersistentClient(
                    path="./data/chroma",
                    settings=Settings(anonymized_telemetry=False)
                )
                self.vector_store = self.chroma_client.get_or_create_collection(
                    name="smartii_memories",
                    metadata={"description": "Vector storage for SMARTII memories"}
                )

            # Initialize FAISS index
            if faiss:
                self.faiss_index = faiss.IndexFlatL2(384)  # 384-dimensional embeddings

            # Load existing data
            await self._load_persistent_data()

            self.initialized = True
            logger.info("Memory engine initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize memory engine: {e}")

    async def close(self):
        """Clean up resources."""
        if self.chroma_client:
            # ChromaDB handles persistence automatically
            pass

    async def save_memory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Save a memory with automatic categorization."""
        try:
            memory_id = data.get("id", str(asyncio.get_event_loop().time()))
            memory_type = data.get("type", "episodic")
            content = data.get("content", "")
            metadata = data.get("metadata", {})
            user_id = data.get("user_id", "default")

            # Add timestamp
            timestamp = datetime.now().isoformat()
            metadata["timestamp"] = timestamp
            metadata["user_id"] = user_id

            # Categorize memory
            if memory_type == "episodic":
                await self._save_episodic_memory(memory_id, content, metadata)
            elif memory_type == "semantic":
                await self._save_semantic_memory(memory_id, content, metadata)
            elif memory_type == "preference":
                await self._save_user_preference(user_id, data.get("key", ""), data.get("value", ""))

            # Store in vector database for semantic search
            if self.vector_store and content:
                await self._store_vector_memory(memory_id, content, metadata)

            return {"status": "saved", "memory_id": memory_id}

        except Exception as e:
            logger.error(f"Error saving memory: {e}")
            return {"status": "error", "message": str(e)}

    async def query_memory(self, query: str, user_id: str = "default", limit: int = 5) -> List[Dict[str, Any]]:
        """Query memories using semantic search."""
        try:
            results = []

            # Vector search
            if self.vector_store:
                try:
                    vector_results = self.vector_store.query(
                        query_texts=[query],
                        n_results=limit,
                        where={"user_id": user_id}
                    )
                    for doc, metadata, distance in zip(
                        vector_results["documents"][0],
                        vector_results["metadatas"][0],
                        vector_results["distances"][0]
                    ):
                        results.append({
                            "content": doc,
                            "metadata": metadata,
                            "similarity": 1 - distance,  # Convert distance to similarity
                            "type": "vector"
                        })
                except Exception as e:
                    logger.warning(f"Vector search failed: {e}")

            # Keyword search in episodic memory
            episodic_results = await self._search_episodic_memory(query, user_id, limit)
            results.extend(episodic_results)

            # Search semantic memory
            semantic_results = await self._search_semantic_memory(query, limit)
            results.extend(semantic_results)

            # Remove duplicates and sort by relevance
            unique_results = self._deduplicate_results(results)
            return unique_results[:limit]

        except Exception as e:
            logger.error(f"Error querying memory: {e}")
            return []

    async def delete_memory(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Delete memories based on criteria."""
        try:
            deleted_count = 0

            # Delete from episodic memory
            if "memory_id" in criteria:
                if criteria["memory_id"] in self.episodic_memory:
                    del self.episodic_memory[criteria["memory_id"]]
                    deleted_count += 1

            # Delete from semantic memory
            if "key" in criteria and criteria["key"] in self.semantic_memory:
                del self.semantic_memory[criteria["key"]]
                deleted_count += 1

            # Delete user preferences
            if "user_id" in criteria and "key" in criteria:
                user_prefs = self.user_preferences.get(criteria["user_id"], {})
                if criteria["key"] in user_prefs:
                    del user_prefs[criteria["key"]]
                    deleted_count += 1

            # Delete from vector store
            if self.vector_store and "memory_id" in criteria:
                self.vector_store.delete(ids=[criteria["memory_id"]])

            return {"status": "deleted", "count": deleted_count}

        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return {"status": "error", "message": str(e)}

    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences."""
        return self.user_preferences.get(user_id, {})

    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update user preferences."""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}

        self.user_preferences[user_id].update(preferences)
        await self._save_persistent_data()
        return {"status": "updated"}

    async def get_conversation_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history for a user."""
        history = self.conversation_history.get(user_id, [])
        return history[-limit:] if history else []

    async def add_conversation_entry(self, user_id: str, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Add an entry to conversation history."""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []

        # Add timestamp
        entry["timestamp"] = datetime.now().isoformat()
        self.conversation_history[user_id].append(entry)

        # Keep only recent history (last 1000 entries)
        if len(self.conversation_history[user_id]) > 1000:
            self.conversation_history[user_id] = self.conversation_history[user_id][-1000:]

        return {"status": "added"}

    async def _save_episodic_memory(self, memory_id: str, content: str, metadata: Dict[str, Any]):
        """Save episodic memory (events, experiences)."""
        self.episodic_memory[memory_id] = {
            "content": content,
            "metadata": metadata,
            "type": "episodic"
        }

    async def _save_semantic_memory(self, memory_id: str, content: str, metadata: Dict[str, Any]):
        """Save semantic memory (facts, knowledge)."""
        key = metadata.get("key", memory_id)
        self.semantic_memory[key] = {
            "content": content,
            "metadata": metadata,
            "type": "semantic"
        }

    async def _save_user_preference(self, user_id: str, key: str, value: Any):
        """Save user preference."""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
        self.user_preferences[user_id][key] = value

    async def _store_vector_memory(self, memory_id: str, content: str, metadata: Dict[str, Any]):
        """Store memory in vector database."""
        if self.vector_store:
            # In a real implementation, you'd generate embeddings here
            # For now, we'll use simple text as placeholder
            self.vector_store.add(
                documents=[content],
                metadatas=[metadata],
                ids=[memory_id]
            )

    async def _search_episodic_memory(self, query: str, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """Search episodic memories."""
        results = []
        query_lower = query.lower()

        for memory_id, memory in self.episodic_memory.items():
            if memory["metadata"].get("user_id") == user_id:
                if query_lower in memory["content"].lower():
                    results.append({
                        "content": memory["content"],
                        "metadata": memory["metadata"],
                        "type": "episodic",
                        "similarity": 0.8  # Placeholder similarity score
                    })

        return results[:limit]

    async def _search_semantic_memory(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search semantic memories."""
        results = []
        query_lower = query.lower()

        for key, memory in self.semantic_memory.items():
            if query_lower in memory["content"].lower() or query_lower in key.lower():
                results.append({
                    "content": memory["content"],
                    "metadata": memory["metadata"],
                    "type": "semantic",
                    "similarity": 0.9  # Higher similarity for semantic matches
                })

        return results[:limit]

    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results and sort by similarity."""
        seen = set()
        unique_results = []

        for result in results:
            content_hash = hash(result["content"])
            if content_hash not in seen:
                seen.add(content_hash)
                unique_results.append(result)

        # Sort by similarity (highest first)
        unique_results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        return unique_results

    async def _load_persistent_data(self):
        """Load persistent data from disk."""
        try:
            # Load user preferences
            if os.path.exists("./data/user_preferences.json"):
                with open("./data/user_preferences.json", "r") as f:
                    self.user_preferences = json.load(f)

            # Load semantic memory
            if os.path.exists("./data/semantic_memory.json"):
                with open("./data/semantic_memory.json", "r") as f:
                    self.semantic_memory = json.load(f)

        except Exception as e:
            logger.error(f"Error loading persistent data: {e}")

    async def _save_persistent_data(self):
        """Save persistent data to disk."""
        try:
            os.makedirs("./data", exist_ok=True)

            # Save user preferences
            with open("./data/user_preferences.json", "w") as f:
                json.dump(self.user_preferences, f, indent=2)

            # Save semantic memory
            with open("./data/semantic_memory.json", "w") as f:
                json.dump(self.semantic_memory, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving persistent data: {e}")

    async def cleanup_old_memories(self, days: int = 30):
        """Clean up old episodic memories."""
        cutoff_date = datetime.now() - timedelta(days=days)

        to_delete = []
        for memory_id, memory in self.episodic_memory.items():
            timestamp = memory["metadata"].get("timestamp")
            if timestamp:
                memory_date = datetime.fromisoformat(timestamp)
                if memory_date < cutoff_date:
                    to_delete.append(memory_id)

        for memory_id in to_delete:
            del self.episodic_memory[memory_id]

        logger.info(f"Cleaned up {len(to_delete)} old memories")
        return len(to_delete)

    async def save_routine(self, user_id: str, routine: Dict[str, Any]) -> Dict[str, Any]:
        """Save a user routine or habit."""
        try:
            if user_id not in self.routines_memory:
                self.routines_memory[user_id] = []
            
            routine['timestamp'] = datetime.now().isoformat()
            self.routines_memory[user_id].append(routine)
            
            return {"status": "saved", "routine_id": len(self.routines_memory[user_id]) - 1}
        except Exception as e:
            logger.error(f"Error saving routine: {e}")
            return {"status": "error", "message": str(e)}

    async def get_routines(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user routines."""
        return self.routines_memory.get(user_id, [])

    async def learn_pattern(self, user_id: str, action: str, context: Dict[str, Any]) -> bool:
        """Learn user behavioral patterns."""
        try:
            if user_id not in self.user_habits:
                self.user_habits[user_id] = {}
            
            # Create a pattern key based on time and context
            hour = datetime.now().hour
            day_of_week = datetime.now().strftime("%A")
            pattern_key = f"{day_of_week}_{hour}_{action}"
            
            if pattern_key not in self.user_habits[user_id]:
                self.user_habits[user_id][pattern_key] = {
                    "count": 0,
                    "last_occurrence": None,
                    "contexts": []
                }
            
            self.user_habits[user_id][pattern_key]["count"] += 1
            self.user_habits[user_id][pattern_key]["last_occurrence"] = datetime.now().isoformat()
            self.user_habits[user_id][pattern_key]["contexts"].append(context)
            
            # Keep only last 10 contexts
            if len(self.user_habits[user_id][pattern_key]["contexts"]) > 10:
                self.user_habits[user_id][pattern_key]["contexts"] = \
                    self.user_habits[user_id][pattern_key]["contexts"][-10:]
            
            return True
            
        except Exception as e:
            logger.error(f"Error learning pattern: {e}")
            return False

    async def predict_next_action(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Predict user's next likely action based on learned patterns."""
        try:
            if user_id not in self.user_habits:
                return None
            
            hour = datetime.now().hour
            day_of_week = datetime.now().strftime("%A")
            
            # Find patterns that match current context
            matching_patterns = []
            for pattern_key, pattern_data in self.user_habits[user_id].items():
                if f"{day_of_week}_{hour}" in pattern_key:
                    matching_patterns.append({
                        "pattern": pattern_key,
                        "count": pattern_data["count"],
                        "last_occurrence": pattern_data["last_occurrence"]
                    })
            
            # Return most frequent pattern
            if matching_patterns:
                matching_patterns.sort(key=lambda x: x["count"], reverse=True)
                return matching_patterns[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error predicting next action: {e}")
            return None

    async def save_task_history(self, user_id: str, task: Dict[str, Any]) -> bool:
        """Save completed task to history."""
        try:
            if user_id not in self.task_history:
                self.task_history[user_id] = []
            
            task['completed_at'] = datetime.now().isoformat()
            self.task_history[user_id].append(task)
            
            # Keep only last 100 tasks
            if len(self.task_history[user_id]) > 100:
                self.task_history[user_id] = self.task_history[user_id][-100:]
            
            return True
        except Exception as e:
            logger.error(f"Error saving task history: {e}")
            return False

    async def get_task_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's task history."""
        history = self.task_history.get(user_id, [])
        return history[-limit:] if history else []
