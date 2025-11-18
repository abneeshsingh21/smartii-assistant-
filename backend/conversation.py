"""
SMARTII Conversation Handler - Natural Language Conversation Management
Handles contextual memory, conversation continuity, and emotional intelligence.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class ConversationHandler:
    """Manages natural conversations with context, memory, and emotional awareness."""

    def __init__(self, memory_engine):
        self.memory_engine = memory_engine
        self.active_conversations = {}  # client_id -> conversation state
        self.emotion_tracker = {}  # Track user emotional state
        self.context_window = {}  # Recent context for each user

    async def get_context(self, client_id: str) -> Dict[str, Any]:
        """Get conversation context for a user."""
        try:
            context = {
                "history": [],
                "preferences": {},
                "emotional_state": "neutral",
                "last_interaction": None,
                "conversation_topics": [],
                "pending_tasks": []
            }

            # Get conversation history
            history = await self.memory_engine.get_conversation_history(client_id, limit=20)
            context["history"] = history

            # Get user preferences
            preferences = await self.memory_engine.get_user_preferences(client_id)
            context["preferences"] = preferences

            # Get emotional state
            context["emotional_state"] = self.emotion_tracker.get(client_id, "neutral")

            # Get last interaction time
            if history:
                context["last_interaction"] = history[-1].get("timestamp")

            # Extract conversation topics
            context["conversation_topics"] = self._extract_topics(history)

            # Get pending tasks
            context["pending_tasks"] = self.active_conversations.get(client_id, {}).get("pending_tasks", [])

            return context

        except Exception as e:
            logger.error(f"Error getting context for {client_id}: {e}")
            return {}

    async def update_conversation(self, client_id: str, user_message: str, ai_response: str) -> Dict[str, Any]:
        """Update conversation state with new interaction."""
        try:
            # Create conversation entry
            entry = {
                "user_message": user_message,
                "ai_response": ai_response,
                "timestamp": datetime.now().isoformat()
            }

            # Add to memory
            await self.memory_engine.add_conversation_entry(client_id, entry)

            # Update active conversation state
            if client_id not in self.active_conversations:
                self.active_conversations[client_id] = {
                    "start_time": datetime.now(),
                    "message_count": 0,
                    "topics": set(),
                    "pending_tasks": []
                }

            conv_state = self.active_conversations[client_id]
            conv_state["message_count"] += 1
            conv_state["last_activity"] = datetime.now()

            # Extract and update topics
            new_topics = self._extract_topics_from_message(user_message)
            conv_state["topics"].update(new_topics)

            # Update emotional state
            self._update_emotional_state(client_id, user_message, ai_response)

            # Update context window
            self._update_context_window(client_id, entry)

            # Check for conversation continuity
            await self._check_conversation_continuity(client_id)

            return {"status": "updated"}

        except Exception as e:
            logger.error(f"Error updating conversation for {client_id}: {e}")
            return {"status": "error", "message": str(e)}

    def _extract_topics(self, history: List[Dict[str, Any]]) -> List[str]:
        """Extract main topics from conversation history."""
        topics = set()

        # Simple keyword-based topic extraction
        topic_keywords = {
            "weather": ["weather", "rain", "sunny", "temperature", "forecast"],
            "calendar": ["meeting", "appointment", "schedule", "calendar", "event"],
            "email": ["email", "mail", "message", "send", "inbox"],
            "music": ["music", "song", "play", "listen", "audio"],
            "shopping": ["buy", "purchase", "shop", "order", "price"],
            "travel": ["travel", "flight", "hotel", "trip", "vacation"],
            "work": ["work", "project", "task", "deadline", "meeting"],
            "health": ["health", "doctor", "medicine", "exercise", "diet"]
        }

        for entry in history[-10:]:  # Last 10 messages
            message = entry.get("user_message", "").lower()
            for topic, keywords in topic_keywords.items():
                if any(keyword in message for keyword in keywords):
                    topics.add(topic)

        return list(topics)

    def _extract_topics_from_message(self, message: str) -> List[str]:
        """Extract topics from a single message."""
        topics = []
        message_lower = message.lower()

        # Topic detection logic
        if any(word in message_lower for word in ["weather", "rain", "temperature"]):
            topics.append("weather")
        if any(word in message_lower for word in ["meeting", "appointment", "schedule"]):
            topics.append("calendar")
        if any(word in message_lower for word in ["email", "mail", "message"]):
            topics.append("email")

        return topics

    def _update_emotional_state(self, client_id: str, user_message: str, ai_response: str):
        """Update the user's emotional state based on conversation."""
        # Simple emotion detection
        positive_words = ["good", "great", "excellent", "happy", "love", "awesome"]
        negative_words = ["bad", "terrible", "sad", "angry", "hate", "awful", "frustrated"]

        message_lower = user_message.lower()
        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)

        current_emotion = self.emotion_tracker.get(client_id, "neutral")

        if positive_count > negative_count:
            new_emotion = "positive"
        elif negative_count > positive_count:
            new_emotion = "negative"
        else:
            new_emotion = "neutral"

        # Smooth emotion transitions
        if current_emotion != new_emotion:
            self.emotion_tracker[client_id] = new_emotion

    def _update_context_window(self, client_id: str, entry: Dict[str, Any]):
        """Update the recent context window for the user."""
        if client_id not in self.context_window:
            self.context_window[client_id] = []

        self.context_window[client_id].append(entry)

        # Keep only recent context (last 5 exchanges)
        if len(self.context_window[client_id]) > 10:  # 5 exchanges = 10 messages
            self.context_window[client_id] = self.context_window[client_id][-10:]

    async def _check_conversation_continuity(self, client_id: str):
        """Check if the conversation should be continued or reset."""
        conv_state = self.active_conversations.get(client_id)
        if not conv_state:
            return

        # Reset conversation if inactive for too long
        if "last_activity" in conv_state:
            inactive_time = datetime.now() - conv_state["last_activity"]
            if inactive_time > timedelta(hours=2):
                # Archive current conversation
                await self._archive_conversation(client_id)
                # Start new conversation
                self.active_conversations[client_id] = {
                    "start_time": datetime.now(),
                    "message_count": 0,
                    "topics": set(),
                    "pending_tasks": []
                }

    async def _archive_conversation(self, client_id: str):
        """Archive a completed conversation."""
        try:
            conv_state = self.active_conversations.get(client_id, {})
            if conv_state.get("message_count", 0) > 0:
                # Save conversation summary to memory
                summary = {
                    "type": "conversation_summary",
                    "content": f"Conversation with {conv_state.get('message_count', 0)} messages on topics: {list(conv_state.get('topics', []))}",
                    "metadata": {
                        "client_id": client_id,
                        "start_time": conv_state.get("start_time").isoformat() if conv_state.get("start_time") else None,
                        "duration": str(datetime.now() - conv_state.get("start_time")) if conv_state.get("start_time") else None,
                        "topics": list(conv_state.get("topics", []))
                    }
                }
                await self.memory_engine.save_memory(summary)

        except Exception as e:
            logger.error(f"Error archiving conversation for {client_id}: {e}")

    async def get_conversation_insights(self, client_id: str) -> Dict[str, Any]:
        """Get insights about the user's conversation patterns."""
        try:
            history = await self.memory_engine.get_conversation_history(client_id, limit=100)

            insights = {
                "total_conversations": 0,
                "average_message_length": 0,
                "common_topics": [],
                "peak_activity_hours": [],
                "emotional_tone": "neutral"
            }

            if not history:
                return insights

            # Calculate insights
            total_messages = len(history)
            total_length = sum(len(entry.get("user_message", "")) for entry in history)
            insights["average_message_length"] = total_length / total_messages if total_messages > 0 else 0

            # Common topics
            all_topics = []
            for entry in history:
                topics = self._extract_topics_from_message(entry.get("user_message", ""))
                all_topics.extend(topics)

            from collections import Counter
            topic_counts = Counter(all_topics)
            insights["common_topics"] = topic_counts.most_common(5)

            # Peak activity hours
            hours = [datetime.fromisoformat(entry.get("timestamp", "")).hour for entry in history if entry.get("timestamp")]
            hour_counts = Counter(hours)
            insights["peak_activity_hours"] = hour_counts.most_common(3)

            return insights

        except Exception as e:
            logger.error(f"Error getting conversation insights for {client_id}: {e}")
            return {}

    async def suggest_follow_up(self, client_id: str) -> Optional[str]:
        """Suggest a follow-up question or action based on conversation context."""
        try:
            context = await self.get_context(client_id)
            history = context.get("history", [])

            if not history:
                return "How can I help you today?"

            last_exchange = history[-1]
            user_message = last_exchange.get("user_message", "").lower()

            # Generate contextual follow-ups
            if "weather" in user_message:
                return "Would you like me to set a weather reminder or check forecasts for other locations?"
            elif "meeting" in user_message:
                return "Should I add this to your calendar or send meeting invites?"
            elif "email" in user_message:
                return "Would you like me to draft that email for you?"
            elif any(word in user_message for word in ["play", "music", "song"]):
                return "What genre or artist would you like to listen to?"
            else:
                return "Is there anything else I can help you with?"

        except Exception as e:
            logger.error(f"Error suggesting follow-up for {client_id}: {e}")
            return None

    async def handle_correction(self, client_id: str, correction: str) -> str:
        """Handle user corrections to previous AI responses."""
        try:
            # Store the correction for learning
            correction_data = {
                "type": "correction",
                "content": correction,
                "metadata": {
                    "client_id": client_id,
                    "timestamp": datetime.now().isoformat()
                }
            }
            await self.memory_engine.save_memory(correction_data)

            return "Thank you for the correction. I'll remember that for next time."

        except Exception as e:
            logger.error(f"Error handling correction for {client_id}: {e}")
            return "I noted your correction."

    async def detect_language(self, text: str) -> str:
        """Detect the language of input text."""
        try:
            # Simple language detection based on common words
            # In production, use langdetect or similar library
            
            english_words = ["the", "is", "are", "was", "were", "what", "how", "why", "when"]
            spanish_words = ["el", "la", "es", "son", "que", "como", "por", "para"]
            french_words = ["le", "la", "est", "sont", "que", "comment", "pour", "avec"]
            german_words = ["der", "die", "das", "ist", "sind", "wie", "was", "wo"]
            
            text_lower = text.lower()
            
            english_count = sum(1 for word in english_words if word in text_lower)
            spanish_count = sum(1 for word in spanish_words if word in text_lower)
            french_count = sum(1 for word in french_words if word in text_lower)
            german_count = sum(1 for word in german_words if word in text_lower)
            
            max_count = max(english_count, spanish_count, french_count, german_count)
            
            if max_count == 0:
                return "en"  # Default to English
            elif max_count == english_count:
                return "en"
            elif max_count == spanish_count:
                return "es"
            elif max_count == french_count:
                return "fr"
            else:
                return "de"
                
        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            return "en"

    async def adapt_response_style(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, str]:
        """Adapt conversation style based on user preferences."""
        try:
            style = {
                "verbosity": preferences.get("verbosity", "balanced"),  # concise, balanced, detailed
                "formality": preferences.get("formality", "friendly"),  # formal, friendly, casual
                "technical_level": preferences.get("technical_level", "medium"),  # low, medium, high
                "emoji_usage": preferences.get("emoji_usage", False)
            }
            
            return style
            
        except Exception as e:
            logger.error(f"Error adapting response style: {e}")
            return {"verbosity": "balanced", "formality": "friendly", "technical_level": "medium", "emoji_usage": False}

    async def get_personalized_greeting(self, client_id: str) -> str:
        """Generate a personalized greeting based on user context."""
        try:
            context = await self.get_context(client_id)
            preferences = context.get("preferences", {})
            last_interaction = context.get("last_interaction")

            greeting = "Hello! I'm SMARTII, your intelligent assistant."

            # Add personalization
            if preferences.get("name"):
                greeting = f"Hello {preferences['name']}! Great to see you again."

            # Add time-based greeting
            current_hour = datetime.now().hour
            if current_hour < 12:
                time_greeting = "Good morning"
            elif current_hour < 18:
                time_greeting = "Good afternoon"
            else:
                time_greeting = "Good evening"

            greeting = f"{time_greeting}! {greeting}"

            # Add context from last interaction
            if last_interaction:
                last_time = datetime.fromisoformat(last_interaction)
                time_diff = datetime.now() - last_time

                if time_diff.days == 0:
                    greeting += " Welcome back!"
                elif time_diff.days == 1:
                    greeting += " It's been a day since we last talked."
                else:
                    greeting += f" It's been {time_diff.days} days since we last spoke."

            return greeting

        except Exception as e:
            logger.error(f"Error generating personalized greeting for {client_id}: {e}")
            return "Hello! I'm SMARTII, ready to assist you."

    def clear_context(self, client_id: str):
        """Clear conversation context for a user."""
        if client_id in self.active_conversations:
            del self.active_conversations[client_id]
        if client_id in self.emotion_tracker:
            del self.emotion_tracker[client_id]
        if client_id in self.context_window:
            del self.context_window[client_id]
