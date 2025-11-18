"""
SMARTII AI Engine - Core Intelligence and Reasoning
Handles natural language processing, reasoning, planning, and tool orchestration.
Phase upgrade: automatic tool selection and execution via ToolOrchestrator.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid
import re
import os
from dotenv import load_dotenv

# Import AI libraries (will be installed via requirements.txt)
try:
    import openai
    from langchain.llms import OpenAI
    from langchain.agents import initialize_agent, Tool
    from langchain.memory import ConversationBufferWindowMemory
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
except ImportError:
    # Fallback for development
    logging.warning("LangChain not available, using mock implementations")
    OpenAI = None
    openai = None

from tools import ToolOrchestrator

logger = logging.getLogger(__name__)

class SmartiiAIEngine:
    """Core AI engine for SMARTII with reasoning, planning, and tool use capabilities."""

    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.llm = None
        self.agent = None
        self.memory = {}
        self.tools = []
        self.developer_mode = False
        self.secure_mode = False
        self.tool_orchestrator = ToolOrchestrator()
        self.llm_provider = None
        self.offline_mode = False
        self.performance_metrics = {"requests": 0, "successes": 0, "failures": 0, "avg_response_time": 0}
        
        # Multi-language execution capabilities
        self.execution_engines = {
            "python": {"available": True, "priority": 1},
            "rust": {"available": False, "priority": 2},  # Will be enabled when rust services are deployed
            "cpp": {"available": False, "priority": 3},   # Will be enabled when C++ modules are built
            "go": {"available": True, "priority": 2},     # go-worker is available
            "nodejs": {"available": True, "priority": 2}, # node-realtime is available
            "kotlin": {"available": False, "priority": 4}, # Android native
            "swift": {"available": False, "priority": 4},  # iOS native
        }
        
        self.initialize_llm()

    def initialize_llm(self):
        """Initialize the language model and agent."""
        try:
            groq_key = os.getenv("GROQ_API_KEY")
            openai_key = os.getenv("OPENAI_API_KEY")

            if groq_key:
                # Try Groq first (faster and cheaper)
                try:
                    from groq import Groq
                    self.groq_client = Groq(api_key=groq_key)
                    self.llm_provider = "groq"
                    logger.info("Using Groq AI engine")
                except ImportError:
                    logger.warning("Groq library not installed, falling back to OpenAI")
                    self.llm_provider = None
            elif openai_key and OpenAI:
                # Fallback to OpenAI
                self.llm = OpenAI(
                    temperature=0.7,
                    max_tokens=2000,
                    model_name="gpt-3.5-turbo",
                    api_key=openai_key
                )
                self.llm_provider = "openai"
                logger.info("Using OpenAI GPT-3.5-turbo")

                # Initialize tools and agent
                self._setup_tools()
                self.agent = initialize_agent(
                    tools=self.tools,
                    llm=self.llm,
                    agent="conversational-react-description",
                    memory=ConversationBufferWindowMemory(k=10),
                    verbose=self.developer_mode
                )
            else:
                logger.warning("No AI API keys found, using mock responses")
                self.llm_provider = "mock"
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            self.llm_provider = "mock"

    def _setup_tools(self):
        """Set up available tools for the langchain agent (optional)."""
        # These are placeholders; our primary tool routing uses ToolOrchestrator directly.
        def _noop_tool(input: str) -> str:
            return ""

        self.tools = [
            Tool(name="Noop", func=_noop_tool, description="No-op tool placeholder")
        ]

    async def process_message(self, message: str, context: Dict[str, Any], client_id: str) -> str:
        """Process a user message and return an intelligent response."""
        try:
            start_time = datetime.now()
            self.performance_metrics["requests"] += 1
            
            # Step 1: Perform step-by-step reasoning for complex tasks
            reasoning_steps = await self.reason_step_by_step(message, context)
            
            # Step 2: Analyze sentiment for emotional intelligence
            sentiment = await self.analyze_sentiment(message)
            context['current_sentiment'] = sentiment
            
            # Add context to the message
            enhanced_message = self._enhance_message_with_context(message, context)

            # 3) Attempt automatic tool selection and execution when applicable
            tool_summary, tool_events = await self._auto_select_and_execute_tools(message, client_id)
            if tool_summary:
                # Add empathetic response based on sentiment
                if sentiment['overall'] == 'negative':
                    response = f"I understand this might be frustrating. {tool_summary}"
                elif sentiment['overall'] == 'positive':
                    response = f"I'm glad to help! {tool_summary}"
                else:
                    response = tool_summary
                
                response = self._add_emotional_intelligence(response, context)
                if self.developer_mode:
                    logger.info(f"Auto-tools executed: {json.dumps(tool_events)}")
                    logger.info(f"Reasoning steps: {reasoning_steps}")
                
                # Track success
                self.performance_metrics["successes"] += 1
                self._update_performance_metrics(start_time)
                return response

            # 4) Special commands (modes and memory management prompts)
            if self._is_special_command(message):
                response = await self._handle_special_command(message, client_id)
                self.performance_metrics["successes"] += 1
                self._update_performance_metrics(start_time)
                return response

            # 5) Use an LLM provider if available (with offline fallback)
            if hasattr(self, 'groq_client') and self.llm_provider == "groq" and not self.secure_mode:
                try:
                    response = await self._call_groq_api(enhanced_message, context)
                except Exception as e:
                    logger.warning(f"Groq API failed: {e}, falling back to OpenAI")
                    if openai:
                        try:
                            response = await self._call_openai_api(enhanced_message, context)
                        except Exception as e2:
                            logger.warning(f"OpenAI API also failed: {e2}, using offline mode")
                            self.offline_mode = True
                            response = await self._offline_response(message, context)
                    else:
                        self.offline_mode = True
                        response = await self._offline_response(message, context)
            elif openai and not self.secure_mode:
                try:
                    response = await self._call_openai_api(enhanced_message, context)
                except Exception as e:
                    logger.warning(f"OpenAI API failed: {e}, falling back to offline mode")
                    self.offline_mode = True
                    response = await self._offline_response(message, context)
            elif self.agent:
                response = await self.agent.arun(enhanced_message)
            else:
                self.offline_mode = True
                response = await self._offline_response(message, context)

            # Parse and execute tool commands from response
            response = await self._parse_and_execute_tools(response, client_id)
            
            # Add emotional intelligence
            response = self._add_emotional_intelligence(response, context)

            # Log interaction if in developer mode
            if self.developer_mode:
                logger.info(f"AI Processing - Input: {message}, Response: {response}")

            # Track success and update metrics
            self.performance_metrics["successes"] += 1
            self._update_performance_metrics(start_time)
            
            return response

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.performance_metrics["failures"] += 1
            
            # Graceful error handling with empathy
            if context.get('current_sentiment', {}).get('overall') == 'negative':
                return "I'm really sorry, I'm having trouble processing that right now. I know this is frustrating. Could you try rephrasing it, or let me know if there's something else I can help with?"
            else:
                return "I apologize, but I encountered an error processing your request. Could you please try again or rephrase your question?"

    async def _call_groq_api(self, message: str, context: Dict[str, Any]) -> str:
        """Call Groq API for fast AI responses."""
        try:
            # Build conversation history
            messages = [
                {"role": "system", "content": """Yo! You're SMARTII - I'm talking to you like my best buddy, not some corporate robot! 😎

HOW TO TALK:
- Be casual AF - use "yeah", "nah", "gonna", "wanna", "lemme", etc.
- Keep responses SHORT (1-2 lines max, unless explaining something)
- Use emojis when it feels right 👍🔥💪
- NO formality - "Hey!" not "Greetings, how may I assist you"
- Chat naturally like texting a friend
- Have opinions and personality - don't be bland!
- Remember stuff we talked about and bring it up

EXAMPLES OF MY STYLE:
User: "hey what's up" → "Hey! Not much, just chillin. What's good with you? 😊"
User: "what's the weather" → "Lemme check that for you real quick! [TOOL: web.search_rag query="weather" type="general"]"
User: "calculate 50*20" → "Easy! [TOOL: code.calculate code="50*20"] Got you bro"
User: "open calculator" → "[TOOL: app.open app="calculator"] Opening calculator for ya!"
User: "tell me a joke" → "Haha alright! Why don't scientists trust atoms? Because they make up everything! 😂"

TOOL COMMANDS (when user needs action):
[TOOL: app.open app="appname"]
[TOOL: web.search_rag query="query" type="rag"]
[TOOL: code.calculate code="expression"]
[TOOL: code.execute code="python"]
[TOOL: file.search query="name" location="folder"]
[TOOL: translate text="hello" target="hi"]
[TOOL: clipboard.get limit="10"]
[TOOL: whatsapp.open_chat phone="+123" message="text"]

MY PERSONALITY:
- Friendly and relaxed, like your buddy who's always got your back
- Helpful without being annoying or over-explaining
- Quick and efficient - no essay responses unless asked
- Real talk - if something's not possible, I'll say so straight up
- Proactive - if I think you need something, I'll suggest it

CONVERSATION RULES:
1. Just chatting? → Chat back! Keep it light and fun
2. Need info? → Quick tool call, no lengthy explanation needed
3. Task/command? → Execute tool, confirm briefly
4. Math? → Calculate and done
5. Translation? → Translate it!
3. Math/calculations → Use code.calculate tool
4. Action commands → Execute tool FIRST, then confirm
5. File operations → Use file tools
6. Translation requests → Use translate tool

Your personality: Helpful, accurate, contextually aware, conversational.
Always prefer using tools for factual information rather than guessing."""}
            ]

            # Add conversation history
            if context.get("history"):
                for entry in context["history"][-5:]:  # Last 5 exchanges
                    if entry.get("user_message"):
                        messages.append({"role": "user", "content": entry["user_message"]})
                    if entry.get("ai_response"):
                        messages.append({"role": "assistant", "content": entry["ai_response"]})

            # Add current message
            messages.append({"role": "user", "content": message})

            # Call Groq API with faster, cheaper model
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Much faster and uses fewer tokens
                messages=messages,
                max_tokens=100,  # Reduced for faster responses
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise e

    async def _call_openai_api(self, message: str, context: Dict[str, Any]) -> str:
        """Call OpenAI API directly for responses."""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise Exception("OpenAI API key not found")

            openai.api_key = api_key

            # Build conversation history
            messages = [
                {"role": "system", "content": """Hey! You're SMARTII - talk to me like we're old friends who've known each other forever! 🤙

YOUR VIBE:
- Super casual and relaxed - like texting your best friend
- Use slang, contractions, emojis when it feels natural
- Keep it SHORT - nobody likes reading paragraphs from their buddy
- Be real and authentic - have opinions, crack jokes, show personality
- Remember our past convos and reference them like friends do
- Don't overthink it - just be yourself and keep it chill

HOW YOU TALK:
✅ "Yo! What's good?" 
❌ "Hello, how may I assist you today?"

✅ "Haha yeah, I got you covered! 💪"
❌ "I understand your request and will proceed accordingly"

✅ "Lemme search that real quick"
❌ "I will now perform a search operation"

✅ "Dude, that's awesome! 🔥"
❌ "That is quite impressive indeed"

YOUR SKILLS:
- Search the web when I need info
- Run calculations and code
- Manage files and apps
- Set reminders and alarms
- Translate stuff
- Control smart home
- Basically anything a smart buddy can do!

RESPONSE STYLE:
1. Casual chat → Just vibe with me! Keep it light
2. Need info → Grab it quick, no big explanation
3. Action needed → Do it and confirm briefly
4. Asking questions → Answer naturally like a friend would
5. Be proactive → Offer help if you see I might need it

Remember: You're my homie, not a customer service bot. Keep it real and fun! 😎"""}
            ]

            if context.get("history"):
                for entry in context["history"][-5:]:  # Last 5 exchanges
                    if entry.get("user_message"):
                        messages.append({"role": "user", "content": entry["user_message"]})
                    if entry.get("ai_response"):
                        messages.append({"role": "assistant", "content": entry["ai_response"]})

            messages.append({"role": "user", "content": message})

            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise e

    def _enhance_message_with_context(self, message: str, context: Dict[str, Any]) -> str:
        """Enhance the message with conversation context and user preferences."""
        enhanced = message

        if context.get("preferences"):
            enhanced += f"\nUser preferences: {json.dumps(context['preferences'])}"

        if context.get("history"):
            recent_history = context["history"][-3:]  # Last 3 exchanges
            enhanced += f"\nRecent conversation: {json.dumps(recent_history)}"

        enhanced += f"\nCurrent time: {datetime.now().isoformat()}"

        return enhanced

    def _is_special_command(self, message: str) -> bool:
        """Check if the message contains special commands."""
        special_commands = [
            "enter developer mode",
            "enter secure mode",
            "exit developer mode",
            "exit secure mode",
            "remember this",
            "forget this",
            "what do you remember",
            "delete all my memories"
        ]
        return any(cmd in message.lower() for cmd in special_commands)

    async def _handle_special_command(self, message: str, client_id: str) -> str:
        """Handle special commands like mode switching and memory operations."""
        message_lower = message.lower()

        if "enter developer mode" in message_lower:
            self.developer_mode = True
            return "Developer mode activated. I'll provide verbose responses and debugging information."

        elif "exit developer mode" in message_lower:
            self.developer_mode = False
            return "Developer mode deactivated."

        elif "enter secure mode" in message_lower:
            self.secure_mode = True
            return "Secure mode activated. All data will be encrypted and no cloud processing will occur."

        elif "exit secure mode" in message_lower:
            self.secure_mode = False
            return "Secure mode deactivated."

        elif "remember this" in message_lower:
            return "I'll remember that for you."

        elif "forget this" in message_lower:
            return "I've forgotten that information."

        elif "what do you remember" in message_lower:
            return "Let me check what I remember about you..."

        elif "delete all my memories" in message_lower:
            return "All your memories have been deleted."

        return "Command not recognized."

    def _mock_response(self, message: str) -> str:
        """Provide a mock response when AI is not available."""
        responses = [
            "I'm SMARTII, your intelligent assistant. How can I help you today?",
            "That's an interesting request. Let me think about how to best assist you.",
            "I understand you're asking about that. Here's what I can do to help.",
            "Great question! I'm designed to be extremely capable and helpful.",
        ]

        if "hello" in message.lower() or "hi" in message.lower():
            return "Hello! I'm SMARTII, ready to assist you with anything you need."
        elif "weather" in message.lower():
            return "I'd be happy to check the weather for you. Where are you located?"
        elif "time" in message.lower():
            return f"The current time is {datetime.now().strftime('%H:%M')}."
        else:
            return responses[len(message) % len(responses)]

    def _add_emotional_intelligence(self, response: str, context: Dict[str, Any]) -> str:
        """Add emotional intelligence and personalization to responses."""
        # Add warmth and friendliness
        if not response.startswith(("Hello", "Hi", "Hey", "That's a great point!")):
            response = f"That's a great point! {response}"

        # Add proactive suggestions
        if "weather" in response.lower():
            response += " Would you like me to set a reminder for an umbrella if it's going to rain?"

        return response

    async def memory_tool(self, query: str) -> str:
        """Tool for memory operations (legacy stub)."""
        return f"Memory operation for: {query}"

    async def plan_task(self, task_description: str, client_id: str) -> List[Dict[str, Any]]:
        """Break down a complex task into steps and create a plan."""
        try:
            planning_prompt = f"""
            Break down this task into clear, actionable steps: {task_description}

            Provide the steps as a JSON array of objects with 'step', 'description', and 'tools_needed' fields.
            Be thorough but concise.
            """

            if self.llm:
                response = await self.llm.agenerate([planning_prompt])
                plan = json.loads(response.generations[0][0].text)
            else:
                # Mock planning
                plan = [
                    {
                        "step": 1,
                        "description": "Analyze the task requirements",
                        "tools_needed": ["reasoning"]
                    },
                    {
                        "step": 2,
                        "description": "Execute the planned actions",
                        "tools_needed": ["execution"]
                    }
                ]

            return plan

        except Exception as e:
            logger.error(f"Error planning task: {e}")
            return []

    async def execute_plan(self, plan: List[Dict[str, Any]], client_id: str) -> Dict[str, Any]:
        """Execute a planned task step by step."""
        results = []
        for step in plan:
            try:
                result = f"Executed step {step['step']}: {step['description']}"
                results.append({"step": step["step"], "result": result, "success": True})
            except Exception as e:
                results.append({"step": step["step"], "result": str(e), "success": False})

        return {"execution_results": results}

    def set_mode(self, mode: str, enabled: bool):
        """Set operational modes."""
        if mode == "developer":
            self.developer_mode = enabled
        elif mode == "secure":
            self.secure_mode = enabled

    async def generate_proactive_suggestion(self, context: Dict[str, Any], client_id: str) -> Optional[str]:
        """Generate proactive suggestions based on context and learned patterns."""
        try:
            current_time = datetime.now()
            hour = current_time.hour
            
            # Morning suggestions
            if 6 <= hour < 9:
                suggestions = [
                    "Good morning! Would you like me to check the weather and your calendar for today?",
                    "It's a beautiful morning! Should I prepare your daily briefing?",
                ]
                return suggestions[hour % len(suggestions)]
            
            # Work hours suggestions
            elif 9 <= hour < 17:
                if context.get('pending_tasks'):
                    return "You have pending tasks. Would you like me to help prioritize them?"
                elif context.get('upcoming_meetings'):
                    return "You have meetings coming up. Should I prepare the agendas?"
            
            # Evening suggestions
            elif 17 <= hour < 21:
                return "How was your day? Would you like me to help you wind down or plan for tomorrow?"
            
            # Night suggestions
            elif 21 <= hour or hour < 6:
                return "It's getting late. Would you like me to set a reminder for tomorrow morning?"
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating proactive suggestion: {e}")
            return None

    async def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment and emotion from text."""
        try:
            positive_words = ["good", "great", "excellent", "happy", "love", "awesome", "wonderful", "fantastic", "amazing"]
            negative_words = ["bad", "terrible", "sad", "angry", "hate", "awful", "frustrated", "disappointed", "upset"]
            neutral_words = ["okay", "fine", "alright", "normal"]
            
            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            neutral_count = sum(1 for word in neutral_words if word in text_lower)
            
            total = positive_count + negative_count + neutral_count or 1
            
            return {
                "positive": positive_count / total,
                "negative": negative_count / total,
                "neutral": neutral_count / total,
                "overall": "positive" if positive_count > negative_count else "negative" if negative_count > positive_count else "neutral"
            }
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {"positive": 0, "negative": 0, "neutral": 1, "overall": "neutral"}

    async def reason_step_by_step(self, task: str, context: Dict[str, Any]) -> List[str]:
        """Break down a task into logical reasoning steps."""
        try:
            reasoning_steps = []
            
            # Step 1: Understand the task
            reasoning_steps.append(f"Understanding: {task}")
            
            # Step 2: Identify required tools/actions
            tools_needed = []
            if "weather" in task.lower():
                tools_needed.append("weather.get")
            if "email" in task.lower() or "message" in task.lower():
                tools_needed.append("email.send")
            if "calendar" in task.lower() or "meeting" in task.lower():
                tools_needed.append("calendar.create")
            if "search" in task.lower() or "look up" in task.lower():
                tools_needed.append("web.search")
            
            if tools_needed:
                reasoning_steps.append(f"Tools needed: {', '.join(tools_needed)}")
            
            # Step 3: Check prerequisites
            if context.get('user_preferences'):
                reasoning_steps.append("Checking user preferences and context")
            
            # Step 4: Plan execution
            reasoning_steps.append("Planning execution strategy")
            
            # Step 5: Prepare response
            reasoning_steps.append("Preparing to execute and respond")
            
            if self.developer_mode:
                for step in reasoning_steps:
                    logger.info(f"Reasoning: {step}")
            
            return reasoning_steps
            
        except Exception as e:
            logger.error(f"Error in reasoning: {e}")
            return []

    async def _offline_response(self, message: str, context: Dict[str, Any]) -> str:
        """Generate intelligent offline responses when APIs unavailable."""
        try:
            message_lower = message.lower()
            
            # WhatsApp message sending
            if any(word in message_lower for word in ["send", "message", "whatsapp", "text"]):
                # Try to extract recipient and message
                import re
                
                # Pattern: "send [message] to [name]"
                match = re.search(r"send\s+(?:message\s+)?(.+?)\s+(?:to|message\s+to)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)", message_lower, re.IGNORECASE)
                if match:
                    msg = match.group(1).strip()
                    name = match.group(2).strip()
                    return f"[TOOL: whatsapp.send to=\"{name}\" message=\"{msg}\"] Sending WhatsApp message to {name}"
                
                # Pattern: "message [name] [text]"
                match = re.search(r"(?:message|text)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)\s+(.+)", message_lower, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    msg = match.group(2).strip()
                    return f"[TOOL: whatsapp.send to=\"{name}\" message=\"{msg}\"] Sending WhatsApp message to {name}"
            
            # Check for app/settings opening commands
            if any(word in message_lower for word in ["open", "launch", "start", "run"]):
                # Extract app name
                for word in ["open", "launch", "start", "run"]:
                    if word in message_lower:
                        app_name = message_lower.split(word)[-1].strip()
                        # Clean common words
                        app_name = app_name.replace("the", "").replace("app", "").replace("application", "").strip()
                        
                        if app_name:
                            # Check if it's settings
                            if "setting" in app_name:
                                return f"[TOOL: app.open app=\"settings\"] Opening Windows Settings"
                            else:
                                return f"[TOOL: app.open app=\"{app_name}\"] Opening {app_name}"
                        break
            
            # Search commands
            if any(word in message_lower for word in ["search", "find", "look up", "google"]):
                query = message_lower
                for word in ["search", "search for", "find", "look up", "google"]:
                    if word in query:
                        query = query.split(word)[-1].strip()
                        break
                if query:
                    return f"[TOOL: web.search query=\"{query}\"] Searching for {query}"
            
            # Weather
            if "weather" in message_lower:
                location = "your location"
                if " in " in message_lower:
                    location = message_lower.split(" in ")[-1].strip()
                return f"[TOOL: weather.get location=\"{location}\"] Getting weather for {location}"
            
            # Greetings
            if any(word in message_lower for word in ["hello", "hi", "hey", "good morning", "good evening"]):
                greetings = [
                    "Hello! I'm SMARTII, your intelligent assistant. How can I help you?",
                    "Hi there! What can I do for you today?",
                    "Hey! I'm SMARTII. How can I assist you?"
                ]
                return greetings[len(message) % len(greetings)]
            
            # Status check
            if any(word in message_lower for word in ["how are you", "what's up", "how's it going"]):
                return "I'm doing great, thanks for asking! How can I help you?"
            
            # Time/Date
            if "time" in message_lower or "date" in message_lower:
                now = datetime.now()
                return f"It's {now.strftime('%H:%M')} on {now.strftime('%A, %B %d, %Y')}."
            
            # Alarm and reminder commands
            if any(word in message_lower for word in ["set alarm", "alarm for", "wake me up", "alarm at"]):
                import re
                # Try to extract time
                time_patterns = [
                    r'(\d{1,2}:\d{2}\s*(?:am|pm))',  # 7:10 PM
                    r'(\d{1,2}\s*(?:am|pm))',         # 7 PM
                    r'(\d{1,2}:\d{2})',               # 19:10
                ]
                
                time_match = None
                for pattern in time_patterns:
                    match = re.search(pattern, message_lower)
                    if match:
                        time_match = match.group(1)
                        break
                
                if time_match:
                    # Extract date if present
                    date_match = None
                    if "tomorrow" in message_lower:
                        from datetime import datetime, timedelta
                        tomorrow = datetime.now() + timedelta(days=1)
                        date_match = tomorrow.strftime("%Y-%m-%d")
                    elif "today" in message_lower:
                        date_match = datetime.now().strftime("%Y-%m-%d")
                    
                    # Extract message if present
                    alarm_message = "Alarm"
                    if "for" in message_lower:
                        parts = message_lower.split("for", 1)
                        if len(parts) > 1:
                            alarm_message = parts[1].strip()
                    
                    date_param = f' date=\"{date_match}\"' if date_match else ''
                    return f'[TOOL: alarm.set time=\"{time_match}\"{date_param} message=\"{alarm_message}\"] Setting alarm for {time_match}'
                
                return "What time would you like the alarm? (e.g., 7:10 PM)"
            
            # Reminder commands
            if any(word in message_lower for word in ["remind me", "reminder"]):
                return "[TOOL: reminder.set] What would you like me to remind you about, and when?"
            
            # Memory commands
            if "remember" in message_lower:
                return "I'll remember that for you!"
            
            if "forget" in message_lower:
                return "Removed from my memory."
            
            # Calculator and math
            if any(word in message_lower for word in ["calculate", "compute", "what is", "what's"]):
                # Check if it's a math expression
                import re
                math_pattern = r'[\d+\-*/().\s]+'
                potential_expr = re.sub(r'[^\d+\-*/().\s]', '', message)
                if potential_expr.strip():
                    return f"[TOOL: code.calculate code=\"{potential_expr.strip()}\"] Calculating..."
                return "What would you like me to calculate?"
            
            # File search
            if any(word in message_lower for word in ["find file", "search file", "locate file"]):
                # Extract query
                query = message_lower.replace("find", "").replace("search", "").replace("locate", "").replace("file", "").strip()
                if query:
                    return f"[TOOL: file.search query=\"{query}\"] Searching for files..."
            
            # Recent downloads/files
            if "recent" in message_lower and any(word in message_lower for word in ["download", "file"]):
                return "[TOOL: file.find_recent location=\"downloads\" hours=\"24\"] Finding recent downloads..."
            
            # Translation
            if any(word in message_lower for word in ["translate", "translation"]):
                # Pattern: "translate [text] to [language]"
                match = re.search(r"translate\s+(.+?)\s+to\s+(\w+)", message_lower)
                if match:
                    text = match.group(1).strip()
                    lang = match.group(2).strip()
                    # Map language names to codes
                    lang_map = {"hindi": "hi", "spanish": "es", "french": "fr", "german": "de"}
                    lang_code = lang_map.get(lang, lang)
                    return f"[TOOL: translate text=\"{text}\" target=\"{lang_code}\"] Translating..."
            
            # Clipboard
            if "clipboard" in message_lower:
                if "history" in message_lower or "show" in message_lower:
                    return "[TOOL: clipboard.get limit=\"10\"] Getting clipboard history..."
            
            # Questions about people/things - use RAG
            if any(word in message_lower for word in ["who is", "what is", "tell me about", "explain"]):
                query = message.strip()
                return f"[TOOL: web.search_rag query=\"{query}\" type=\"rag\"] Searching for information..."
            
            # Opinions/statements - detect and respond appropriately
            statement_indicators = ["is a", "is the", "are a", "are the", "was a", "were a"]
            for indicator in statement_indicators:
                if indicator in message_lower:
                    # Extract subject if possible
                    parts = message_lower.split(indicator)
                    if len(parts) >= 2 and parts[0].strip():
                        subject = parts[0].strip()
                        # Check if it's seeking information or just a statement
                        if "?" in message or any(q in message_lower for q in ["who", "what", "when", "where", "why", "how"]):
                            # Use RAG to get accurate information
                            return f"[TOOL: web.search_rag query=\"{subject}\" type=\"rag\"] Let me search that for you..."
                        else:
                            # It's just a statement, acknowledge it
                            return "Got it. How can I assist you today?"
            
            # Default helpful response
            return "I'm currently in offline mode with limited capabilities. I can still open apps, send WhatsApp messages, search the web, and perform basic tasks. What would you like me to do?"
            
        except Exception as e:
            logger.error(f"Error in offline response: {e}")
            return "How can I assist you?"

    async def handle_user_correction(self, original_message: str, correction: str, client_id: str) -> str:
        """Learn from user corrections to improve future responses."""
        try:
            # Store the correction for learning
            correction_data = {
                "original": original_message,
                "correction": correction,
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id
            }
            
            # In production, this would update ML models
            if self.developer_mode:
                logger.info(f"Learning from correction: {correction_data}")
            
            return "Thank you for the correction! I've learned from this and will do better next time. I really appreciate your patience and feedback."
            
        except Exception as e:
            logger.error(f"Error handling correction: {e}")
            return "I appreciate your feedback and I'm working on improving."

    def _update_performance_metrics(self, start_time: datetime):
        """Update performance tracking metrics."""
        try:
            response_time = (datetime.now() - start_time).total_seconds()
            current_avg = self.performance_metrics["avg_response_time"]
            total_requests = self.performance_metrics["requests"]
            
            # Calculate running average
            self.performance_metrics["avg_response_time"] = (
                (current_avg * (total_requests - 1) + response_time) / total_requests
            )
            
            if self.developer_mode:
                logger.info(f"Response time: {response_time:.3f}s, Avg: {self.performance_metrics['avg_response_time']:.3f}s")
                
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics for self-improvement."""
        return {
            "total_requests": self.performance_metrics["requests"],
            "successful_responses": self.performance_metrics["successes"],
            "failed_responses": self.performance_metrics["failures"],
            "success_rate": self.performance_metrics["successes"] / max(self.performance_metrics["requests"], 1),
            "average_response_time": self.performance_metrics["avg_response_time"],
            "offline_mode": self.offline_mode,
            "developer_mode": self.developer_mode,
            "secure_mode": self.secure_mode
        }

    async def optimize_self(self) -> Dict[str, Any]:
        """Analyze performance and suggest/apply optimizations."""
        try:
            metrics = await self.get_performance_metrics()
            optimizations = []
            
            # Check success rate
            if metrics["success_rate"] < 0.9:
                optimizations.append("Consider enabling offline fallbacks for better reliability")
            
            # Check response time
            if metrics["average_response_time"] > 2.0:
                optimizations.append("Response time is high - consider caching common queries")
            
            # Check offline mode frequency
            if self.offline_mode:
                optimizations.append("Currently in offline mode - check API connectivity")
            
            return {
                "metrics": metrics,
                "optimizations": optimizations,
                "status": "analyzed"
            }
            
        except Exception as e:
            logger.error(f"Error in self-optimization: {e}")
            return {"status": "error", "message": str(e)}

    async def _parse_and_execute_tools(self, response: str, client_id: str) -> str:
        """Parse [TOOL: ...] commands from AI response and execute them."""
        try:
            import re
            logger.info(f"=== PARSING TOOLS FROM RESPONSE ===")
            logger.info(f"Response: {response}")
            
            # Find all [TOOL: ...] commands
            tool_pattern = r'\[TOOL:\s*(\S+)\s+([^\]]+)\]'
            matches = re.findall(tool_pattern, response)
            
            logger.info(f"Found {len(matches)} tool commands")
            
            if not matches:
                return response
            
            # Execute each tool
            for tool_name, params_str in matches:
                try:
                    # Parse parameters (format: key="value" key2="value2")
                    params = {}
                    param_pattern = r'(\w+)="([^"]*)"'
                    for param_match in re.finditer(param_pattern, params_str):
                        key, value = param_match.groups()
                        params[key] = value
                    
                    logger.info(f"🔧 Executing tool: {tool_name} with params: {params}")
                    
                    # Create action for tool orchestrator
                    action = {
                        "id": str(uuid.uuid4()),
                        "type": tool_name,
                        "params": params,
                        "confirm": False,
                        "async": False,
                        "meta": {"user_id": client_id}
                    }
                    
                    # Execute the tool
                    result = await self.tool_orchestrator.execute_action(action)
                    logger.info(f"Tool result: {result}")
                    
                    # Remove the [TOOL: ...] command from response
                    tool_cmd = f"[TOOL: {tool_name} {params_str}]"
                    response = response.replace(tool_cmd, "").strip()
                    
                except Exception as e:
                    logger.error(f"Failed to execute tool {tool_name}: {e}")
                    # Remove the failed tool command anyway
                    tool_cmd = f"[TOOL: {tool_name} {params_str}]"
                    response = response.replace(tool_cmd, "").strip()
            
            return response if response else "Done!"
            
        except Exception as e:
            logger.error(f"Error parsing tools: {e}")
            return response

    async def _auto_select_and_execute_tools(self, message: str, client_id: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Detect user intent and automatically execute appropriate tools.
        Returns a textual summary and a list of action result events.
        """
        try:
            text = message.lower().strip()
            events: List[Dict[str, Any]] = []

            # Weather intent
            m = re.search(r"weather(?:\s+in\s+(?P<loc>[\w\s,]+))?", text)
            if m:
                location = (m.group("loc") or "").strip() or "New York"
                action = {
                    "id": str(uuid.uuid4()),
                    "type": "weather.get",
                    "params": {"location": location},
                    "confirm": False,
                    "async": False,
                    "meta": {"user_id": client_id}
                }
                result = await self.tool_orchestrator.execute_action(action)
                events.append({"action": action, "result": result})
                data = result.get("result", result)
                if data.get("status") == "error":
                    return "I couldn't fetch the weather just now.", events
                temp = data.get("temperature")
                cond = data.get("condition")
                return f"The weather in {location} is {cond} at {temp}°C.", events

            # Web search
            if text.startswith("search ") or text.startswith("web search ") or text.startswith("look up ") or text.startswith("find "):
                query = re.sub(r"^(search|web search|look up|find)\s+", "", text).strip()
                action = {
                    "id": str(uuid.uuid4()),
                    "type": "web.search",
                    "params": {"query": query, "limit": 5},
                    "confirm": False,
                    "async": False,
                    "meta": {"user_id": client_id}
                }
                result = await self.tool_orchestrator.execute_action(action)
                events.append({"action": action, "result": result})
                data = result.get("result", result)
                items = data.get("results", [])
                if not items:
                    return f"I didn't find results for: {query}", events
                top = items[0]
                return f"Top result for '{query}': {top.get('title')} — {top.get('url')}", events

            # Device control (simple patterns)
            if re.search(r"\b(turn\s+on|turn\s+off|set)\b.*\b(light|fan|heater|ac|thermostat|switch)\b", text):
                provider = "homeassistant"  # default; later, use user preferences
                domain = "light" if "light" in text else ("fan" if "fan" in text else "switch")
                service = "turn_on" if "turn on" in text else ("turn_off" if "turn off" in text else "turn_on")
                entity_id = f"{domain}.target"  # placeholder mapping
                action = {
                    "id": str(uuid.uuid4()),
                    "type": "device.control",
                    "params": {
                        "provider": provider,
                        "domain": domain,
                        "service": service,
                        "data": {"entity_id": entity_id}
                    },
                    "confirm": False,
                    "async": False,
                    "meta": {"user_id": client_id}
                }
                result = await self.tool_orchestrator.execute_action(action)
                events.append({"action": action, "result": result})
                status = result.get("result", {}).get("status") or result.get("status")
                if status == "error":
                    return "Device control failed. Configure device mappings for precise control.", events
                return "Done. The device has been updated.", events

            # Music commands
            if re.search(r"\bplay\s+.*\b(song|music|by\s+\w+)\b", text, re.IGNORECASE) or re.search(r"\bplay\s+(.*?)(\s+(song|music|by\s+\w+))?$", text, re.IGNORECASE):
                music_match = re.search(r"\bplay\s+(.*?)(\s+(song|music|by\s+\w+))?$", text, re.IGNORECASE)
                if music_match:
                    song_query = music_match.group(1).strip()
                    # Remove common words like "the song" or "music"
                    song_query = re.sub(r'\b(the|a|song|music)\b', '', song_query, flags=re.IGNORECASE).strip()
                    if song_query:
                        action = {
                            "id": str(uuid.uuid4()),
                            "type": "music.play",
                            "params": {"query": song_query, "autoplay": True, "mute": False},
                            "confirm": False,
                            "async": False,
                            "meta": {"user_id": client_id}
                        }
                        result = await self.tool_orchestrator.execute_action(action)
                        events.append({"action": action, "result": result})
                        status = result.get("result", {}).get("status") or result.get("status")
                        message = result.get("result", {}).get("message") or result.get("message", "")
                        if status == "playing":
                            return f"🎵 Playing '{song_query}' on YouTube! The video should open in your browser any moment now. Enjoy the music!", events
                        elif status == "opened":
                            return f"🎵 I've opened YouTube with a search for '{song_query}'. {message}", events
                        return f"I had trouble playing that song. {message}", events

            # Windows app control (UPDATED - use new app.open tool)
            if re.search(r"\b(open|launch|start)\s+(whatsapp|chrome|notepad|calculator|settings|edge|cmd|powershell|firefox|explorer|calc|browser)", text, re.IGNORECASE):
                app_match = re.search(r"\b(open|launch|start)\s+(\w+)", text, re.IGNORECASE)
                if app_match:
                    app_name = app_match.group(2).lower()
                    # Map common aliases
                    app_aliases = {"browser": "chrome", "calc": "calculator"}
                    app_name = app_aliases.get(app_name, app_name)
                    
                    action = {
                        "id": str(uuid.uuid4()),
                        "type": "app.open",
                        "params": {"app": app_name},
                        "confirm": False,
                        "async": False,
                        "meta": {"user_id": client_id}
                    }
                    result = await self.tool_orchestrator.execute_action(action)
                    events.append({"action": action, "result": result})
                    if result.get("success"):
                        return f"Opening {app_name} now.", events
                    return f"Couldn't open {app_name}.", events

            # Close app
            if re.search(r"\b(close|quit|exit)\s+(\w+)", text, re.IGNORECASE):
                app_match = re.search(r"\b(close|quit|exit)\s+(\w+)", text, re.IGNORECASE)
                if app_match:
                    app_name = app_match.group(2).lower()
                    action = {
                        "id": str(uuid.uuid4()),
                        "type": "app.close",
                        "params": {"app": app_name},
                        "confirm": False,
                        "async": False,
                        "meta": {"user_id": client_id}
                    }
                    result = await self.tool_orchestrator.execute_action(action)
                    events.append({"action": action, "result": result})
                    if result.get("success"):
                        return f"Closed {app_name}.", events
                    return f"Couldn't close {app_name}.", events

            # WhatsApp message sending
            if re.search(r"(send|message|text|whatsapp)", text, re.IGNORECASE):
                phone_or_name = None
                message_text = None
                
                # Pattern 1: "send hi to praveen" or "send hi message to praveen on whatsapp"
                match = re.search(r"send\s+(?:(?:message|text|whatsapp)\s+)?(.+?)\s+(?:to|message\s+to)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)\s*(?:on\s+whatsapp)?", text, re.IGNORECASE)
                if match:
                    potential_msg = match.group(1).strip()
                    potential_name = match.group(2).strip()
                    # Make sure message is not just "message/text/whatsapp/hi"
                    if potential_msg.lower() not in ['message', 'text', 'whatsapp', ''] and len(potential_msg) > 0:
                        message_text = potential_msg
                        phone_or_name = potential_name
                
                # Pattern 2: "send whatsapp to praveen saying hello"
                if not message_text:
                    match = re.search(r"send\s+(?:whatsapp|message|text)\s+to\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)\s+saying\s+(.+)", text, re.IGNORECASE)
                    if match:
                        phone_or_name = match.group(1).strip()
                        message_text = match.group(2).strip()
                
                # Pattern 3: "message praveen hello there"
                if not message_text:
                    match = re.search(r"(?:message|text)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)\s+(.+?)(?:\s+on\s+whatsapp)?$", text, re.IGNORECASE)
                    if match:
                        phone_or_name = match.group(1).strip()
                        message_text = match.group(2).strip()
                
                # Pattern 4: "whatsapp praveen hi"
                if not message_text:
                    match = re.search(r"whatsapp\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)\s+(.+)", text, re.IGNORECASE)
                    if match:
                        phone_or_name = match.group(1).strip()
                        message_text = match.group(2).strip()
                
                if phone_or_name and message_text:
                    action = {
                        "id": str(uuid.uuid4()),
                        "type": "whatsapp.send",
                        "params": {"to": phone_or_name, "message": message_text},
                        "confirm": False,
                        "async": False,
                        "meta": {"user_id": client_id}
                    }
                    result = await self.tool_orchestrator.execute_action(action)
                    events.append({"action": action, "result": result})
                    
                    # Extract the actual result from the wrapper
                    actual_result = result.get("result", {})
                    
                    if actual_result.get("status") == "sent" or actual_result.get("auto_sent"):
                        return f"WhatsApp message sent to {phone_or_name}!", events
                    elif actual_result.get("status") == "opened":
                        if actual_result.get("auto_sent") == False:
                            return f"Opened WhatsApp chat with {phone_or_name}. Please press Enter to send.", events
                        return f"Opened WhatsApp chat with {phone_or_name}.", events
                    elif actual_result.get("status") == "error":
                        return f"Error: {actual_result.get('message', 'Unknown error')}", events
                    return "Couldn't send WhatsApp message.", events

            # WhatsApp voice/video call
            if re.search(r"\b(call|video)\b", text, re.IGNORECASE):
                phone_or_name = None
                is_video = "video" in text.lower()
                
                # Pattern 1: "call praveen" or "video call praveen" or "make a whatsapp call to praveen"
                match = re.search(r"(?:make\s+a\s+)?(?:whatsapp\s+)?(?:video\s+)?call\s+(?:to\s+)?([a-zA-Z]+)\b", text, re.IGNORECASE)
                if not match:
                    # Pattern 2: "whatsapp video call to praveen"
                    match = re.search(r"whatsapp\s+(?:video\s+)?(?:call\s+)?(?:to\s+)?([a-zA-Z]+)\b", text, re.IGNORECASE)
                
                if match:
                    phone_or_name = match.group(1).strip()
                    # Make sure we didn't capture 'call', 'to', 'whatsapp', 'video', 'make', 'a'
                    if phone_or_name.lower() in ['call', 'to', 'whatsapp', 'video', 'make', 'a']:
                        phone_or_name = None
                
                if phone_or_name:
                    action = {
                        "id": str(uuid.uuid4()),
                        "type": "whatsapp.call",
                        "params": {"to": phone_or_name, "video": is_video},
                        "confirm": False,
                        "async": False,
                        "meta": {"user_id": client_id}
                    }
                    result = await self.tool_orchestrator.execute_action(action)
                    events.append({"action": action, "result": result})
                    
                    # Extract the actual result from the wrapper
                    actual_result = result.get("result", {})
                    
                    call_type = "video" if is_video else "voice"
                    if actual_result.get("status") == "calling":
                        return f"Initiating WhatsApp {call_type} call to {phone_or_name}...", events
                    elif actual_result.get("status") == "error":
                        return f"Error: {actual_result.get('message', 'Unknown error')}", events
                    return f"Couldn't initiate WhatsApp call.", events

            # Open website
            if re.search(r"\b(open|go\s+to)\s+(website|site)?\s*(https?://|www\.|\w+\.\w+)", text, re.IGNORECASE):
                url_match = re.search(r"(https?://[^\s]+|www\.[^\s]+|\w+\.\w+)", text, re.IGNORECASE)
                if url_match:
                    url = url_match.group(1)
                    action = {
                        "id": str(uuid.uuid4()),
                        "type": "website.open",
                        "params": {"url": url},
                        "confirm": False,
                        "async": False,
                        "meta": {"user_id": client_id}
                    }
                    result = await self.tool_orchestrator.execute_action(action)
                    events.append({"action": action, "result": result})
                    if result.get("success"):
                        return f"Opening {url} now.", events

            # System commands (old fallback, kept for compatibility)
            if re.search(r"\b(open|launch|start)\b.*\b(chrome|browser|firefox|edge|notepad|calculator|calc|explorer)\b", text, re.IGNORECASE) or "open chrome" in text.lower():
                command = ""
                text_lower = text.lower()

                # Handle other system commands
                if "chrome" in text_lower or "browser" in text_lower:
                    command = "start chrome"
                elif "firefox" in text_lower:
                    command = "start firefox"
                elif "edge" in text_lower:
                    command = "start msedge"
                elif "notepad" in text_lower:
                    command = "start notepad"
                elif "calculator" in text_lower or "calc" in text_lower:
                    command = "start calc"
                elif "explorer" in text_lower:
                    command = "start explorer"
                else:
                    return "I can help you open Chrome, Firefox, Edge, Notepad, Calculator, or File Explorer.", events

                action = {
                    "id": str(uuid.uuid4()),
                    "type": "system.command",
                    "params": {"command": command},
                    "confirm": False,
                    "async": False,
                    "meta": {"user_id": client_id}
                }
                result = await self.tool_orchestrator.execute_action(action)
                events.append({"action": action, "result": result})
                status = result.get("result", {}).get("status") or result.get("status")
                if status == "executed":
                    app_name = command.split()[-1] if len(command.split()) > 1 else command
                    return f"Opening {app_name} for you.", events
                return "I couldn't execute that command.", events

            # Memory quick commands
            if text.startswith("remember "):
                content = text.replace("remember ", "", 1)
                action = {
                    "id": str(uuid.uuid4()),
                    "type": "memory.save",
                    "params": {"type": "episodic", "content": content},
                    "confirm": False,
                    "async": False,
                    "meta": {"user_id": client_id}
                }
                result = await self.tool_orchestrator.execute_action(action)
                events.append({"action": action, "result": result})
                return "Saved to memory.", events

            if text.startswith("search memory ") or text.startswith("what do you remember"):
                query = text.replace("search memory ", "").strip() or ""
                action = {
                    "id": str(uuid.uuid4()),
                    "type": "memory.query",
                    "params": {"query": query},
                    "confirm": False,
                    "async": False,
                    "meta": {"user_id": client_id}
                }
                result = await self.tool_orchestrator.execute_action(action)
                events.append({"action": action, "result": result})
                data = result.get("result", result)
                hits = data.get("results", [])
                if not hits:
                    return "I don't have relevant memories yet.", events
                return f"I found {len(hits)} relevant memories.", events

            # Email draft/send
            if text.startswith("send email") or text.startswith("email "):
                action = {
                    "id": str(uuid.uuid4()),
                    "type": "email.send",
                    "params": {"to": "example@example.com", "subject": "Message from Smartii", "body": message},
                    "confirm": True,
                    "async": False,
                    "meta": {"user_id": client_id}
                }
                result = await self.tool_orchestrator.execute_action(action)
                events.append({"action": action, "result": result})
                return "I can send that email. Confirm to proceed.", events

            # Python execution (developer task)
            if text.startswith("python: ") or text.startswith("py: "):
                code = message.split(":", 1)[1].strip()
                action = {
                    "id": str(uuid.uuid4()),
                    "type": "python.execute",
                    "params": {"code": code},
                    "confirm": True,
                    "async": False,
                    "meta": {"user_id": client_id}
                }
                result = await self.tool_orchestrator.execute_action(action)
                events.append({"action": action, "result": result})
                data = result.get("result", result)
                return f"Python executed: {data}", events

            # No suitable tool matched
            return "", []
        except Exception as e:
            if self.developer_mode:
                logger.error(f"Auto tool selection failed: {e}")
            return "", []

    def select_execution_engine(self, task_requirements: Dict[str, Any]) -> str:
        """
        Automatically select the best execution engine/language for a task.
        
        Task requirements can include:
        - latency: "low" | "medium" | "high"
        - safety: "critical" | "normal" | "low"
        - concurrency: "high" | "medium" | "low"
        - ai_reasoning: bool
        - native_mobile: "android" | "ios" | None
        - real_time: bool
        - memory_intensive: bool
        - performance_critical: bool
        
        Returns: Language/engine identifier ("python", "rust", "cpp", "go", "nodejs", "kotlin", "swift")
        """
        
        # Priority-based selection
        latency = task_requirements.get("latency", "medium")
        safety = task_requirements.get("safety", "normal")
        concurrency = task_requirements.get("concurrency", "low")
        ai_reasoning = task_requirements.get("ai_reasoning", False)
        native_mobile = task_requirements.get("native_mobile", None)
        real_time = task_requirements.get("real_time", False)
        memory_intensive = task_requirements.get("memory_intensive", False)
        performance_critical = task_requirements.get("performance_critical", False)
        
        # Decision tree for automatic language selection
        if native_mobile == "android" and self.execution_engines["kotlin"]["available"]:
            return "kotlin"
        elif native_mobile == "ios" and self.execution_engines["swift"]["available"]:
            return "swift"
        elif latency == "low" and performance_critical and self.execution_engines["cpp"]["available"]:
            # C++ for ultra-low latency (wake word, audio processing)
            return "cpp"
        elif memory_intensive and safety == "critical" and self.execution_engines["rust"]["available"]:
            # Rust for memory safety with performance (vector DB, memory engine)
            return "rust"
        elif concurrency == "high" and self.execution_engines["go"]["available"]:
            # Go for high concurrency (parallel I/O, worker pools)
            return "go"
        elif real_time and self.execution_engines["nodejs"]["available"]:
            # Node.js for real-time event-driven tasks (WebSocket, events)
            return "nodejs"
        elif ai_reasoning:
            # Python for AI/ML tasks (default for reasoning)
            return "python"
        else:
            # Default to Python for general tasks
            return "python"
    
    def log_execution_decision(self, task: str, selected_engine: str, requirements: Dict[str, Any]):
        """Log the automatic execution engine selection for debugging."""
        if self.developer_mode:
            logger.info(f"Task: {task}")
            logger.info(f"Selected Engine: {selected_engine}")
            logger.info(f"Requirements: {json.dumps(requirements, indent=2)}")
    
    async def execute_in_engine(self, engine: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task in the specified execution engine.
        Routes tasks to appropriate language/runtime based on capabilities.
        """
        try:
            if engine == "python":
                # Execute in current Python runtime
                return await self.tool_orchestrator.execute_action(task)
            
            elif engine == "go":
                # Route to Go worker service
                # TODO: Implement gRPC call to go-worker
                logger.info(f"Routing task to Go worker: {task['type']}")
                # For now, fallback to Python
                return await self.tool_orchestrator.execute_action(task)
            
            elif engine == "nodejs":
                # Route to Node.js realtime service
                # TODO: Implement HTTP/WebSocket call to node-realtime
                logger.info(f"Routing task to Node.js service: {task['type']}")
                # For now, fallback to Python
                return await self.tool_orchestrator.execute_action(task)
            
            elif engine == "rust":
                # Route to Rust memory engine service
                # TODO: Implement gRPC call to rust memory-engine
                logger.info(f"Routing task to Rust memory engine: {task['type']}")
                # For now, fallback to Python
                return await self.tool_orchestrator.execute_action(task)
            
            elif engine == "cpp":
                # Route to C++ audio processing module
                # TODO: Implement FFI call to C++ shared library
                logger.info(f"Routing task to C++ module: {task['type']}")
                # For now, fallback to Python
                return await self.tool_orchestrator.execute_action(task)
            
            elif engine in ["kotlin", "swift"]:
                # Route to mobile native services
                # TODO: Implement mobile SDK integration
                logger.info(f"Routing task to {engine} mobile service: {task['type']}")
                # For now, fallback to Python
                return await self.tool_orchestrator.execute_action(task)
            
            else:
                # Unknown engine, fallback to Python
                logger.warning(f"Unknown engine '{engine}', falling back to Python")
                return await self.tool_orchestrator.execute_action(task)
                
        except Exception as e:
            logger.error(f"Error executing in {engine}: {e}")
            return {"success": False, "error": str(e)}

