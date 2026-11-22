# file: chat_repository.py
# Haven Chat Repository - now uses Ollama for AI inference

import json
import re
import urllib.request
import urllib.error
from typing import List, Tuple


def clean_reply_text(text: str) -> str:
    """Haven Agent v1 fix - talk like a normal person, no brackets or stars.

    Removes anything the model puts in brackets or asterisks instead of
    talking normally, so it never reaches the chat screen or the voice:
      *smiles* / *waves*  -> removed
      [laughs] / [action] -> removed
      [[TOOL:...]] / [[SPEECH:...]] / [[anything]] -> removed
      **bold** -> keeps the words, removes the stars
    Plain sentences are left alone.
    """
    if not text:
        return ""
    text = re.sub(r"\*\*([^*]{1,200})\*\*", r"\1", text)
    text = re.sub(r"\[\[[^\]]*\]\]", "", text)
    text = re.sub(r"\[[^\]\n]{1,120}\]", "", text)
    text = re.sub(r"\*[^*\n]{1,120}\*", "", text)
    text = re.sub(r"\*[^*\n]{1,120}\*", "", text)
    text = text.replace("[", "").replace("]", "").replace("*", "")
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\.{2,}", ".", text)
    text = re.sub(r":\s*\.\s*", ": ", text)
    text = re.sub(r"\s+\.", ".", text)
    text = re.sub(r"\.\s*\.\s*", ". ", text)
    return text.strip()



class ChatRepository:
    """
    ChatRepository handles:
    - talking to the AI model via Ollama
    - building prompts (normal chat, math, commands)
    - tracking history
    - integrating with MemoryEngine for context
    - web search for knowledge when needed
    """

    # Ollama API configuration
    OLLAMA_BASE_URL = "http://localhost:11434"
    OLLAMA_MODEL = "llama3.1:latest"  # Default model - no thinking mode, fast responses

    def __init__(self, model_path: str = None, memory_engine=None, web_search=None, agent_tools=None, game_engine=None):
        # Check if Ollama is running
        if not self._check_ollama():
            raise RuntimeError(
                "Ollama is not running. Please install Ollama from https://ollama.com and start it.\n"
                "Then run: ollama pull llama3.1"
            )

        # Conversation state
        self.history: List[Tuple[str, str]] = []
        self.memory: List[str] = []
        
        # Optional: reference to MemoryEngine for richer context
        self.memory_engine = memory_engine
        
        # Optional: web search engine for knowledge lookup
        self.web_search = web_search
        
        # Optional: agent tools for PC control, time, files, network, weather
        self.agent_tools = agent_tools
        
        # Optional: game engine for text-based games
        self.game_engine = game_engine

    def _check_ollama(self) -> bool:
        """Check if Ollama is running and the model is available."""
        try:
            # Check if Ollama is running
            req = urllib.request.Request(f"{self.OLLAMA_BASE_URL}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    models = [m['name'] for m in data.get('models', [])]
                    
                    # Check if the model is available
                    if self.OLLAMA_MODEL not in models:
                        print(f"[Chat] Warning: Model '{self.OLLAMA_MODEL}' not found in Ollama.")
                        print(f"[Chat] Available models: {', '.join(models) if models else 'none'}")
                        print(f"[Chat] To download the model, run: ollama pull {self.OLLAMA_MODEL}")
                        return False
                    
                    print(f"[Chat] Connected to Ollama with model: {self.OLLAMA_MODEL}")
                    return True
        except Exception as e:
            print(f"[Chat] Cannot connect to Ollama: {e}")
            print("[Chat] Make sure Ollama is running and the model is downloaded.")
            return False
        return False

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def add_memory(self, text: str):
        text = text.strip()
        if text and text not in self.memory:
            self.memory.append(text)

    def clear_memory(self):
        self.memory.clear()

    def clear_history(self):
        self.history.clear()

    def send_message(self, user_message: str) -> str:
        user_message = user_message.strip()
        if not user_message:
            return "You didn't say anything."

        # Haven Agent v1.2: remember / forget commands, in plain English.
        # "remember: I live in Castile, NY" -> Haven saves it, and says so.
        # "forget: I live in Castile, NY" -> Haven removes it.
        # The web server (api.py) saves the chat after this, so the fact is kept.
        msg_lower = user_message.lower()
        if msg_lower.startswith("remember:") or msg_lower.startswith("remember that "):
            fact = user_message.split(":", 1)[-1].strip() if ":" in user_message else user_message[len("remember that "):].strip()
            if self.memory_engine:
                self.memory_engine.add_user_fact(fact)
                # Also add to learned facts, so it shows up in her context
                if fact not in self.memory_engine.data.get("learned_facts", []):
                    self.memory_engine.data.setdefault("learned_facts", []).append(fact)
                    self.memory_engine._save()
                return f"Okay, I'll remember that: {fact}"
            return "I don't have my memory turned on right now, so I can't save that."
        if msg_lower.startswith("forget:"):
            fact = user_message.split(":", 1)[-1].strip()
            if self.memory_engine:
                self.memory_engine.forget_fact(fact)
                return f"Okay, I forgot: {fact}"
            return "I don't have my memory turned on right now."
        if msg_lower in ("what do you remember", "what do you remember about me", "what do you know about me"):
            if self.memory_engine:
                summary = self.memory_engine.get_context_summary()
                return summary if summary else "I don't have anything saved about you yet. Tell me something with 'remember:' and I'll keep it."
            return "I don't have my memory turned on right now."

        # Check for game commands first
        if self.game_engine:
            msg_lower = user_message.lower()
            if msg_lower.startswith("play ") or msg_lower == "play":
                game_name = user_message[5:].strip() if len(user_message) > 5 else ""
                if game_name:
                    result = self.game_engine.start_game(game_name)
                    return result
                else:
                    return self.game_engine.list_games()
            elif msg_lower in ("games", "game", "what games", "list games"):
                return self.game_engine.list_games()
            elif msg_lower in ("quit game", "end game", "stop game", "exit game"):
                return self.game_engine.end_game()
            elif self.game_engine.active_game:
                # Active game — pass input to the game
                result = self.game_engine.play_turn(user_message)
                return result

        self.history.append(("user", user_message))

        # Check if we should search the web for this query
        web_context = ""
        searched = False
        if self.web_search and self.web_search.available:
            if self.web_search.should_search(user_message):
                print(f"[Chat] Searching web for: {user_message}")
                web_context = self.web_search.search_and_summarize(user_message, fetch_top=2)
                if web_context:
                    searched = True
                    print(f"[Chat] Web search found {len(web_context)} chars of context")

        prompt = self._build_prompt(user_message, web_context=web_context)
        reply = self._generate_reply(prompt)

        # Check if the reply contains a tool call
        if self.agent_tools:
            tool_result = self.agent_tools.parse_and_execute(reply)
            if tool_result:
                # Strip the tool call from the reply and return the result
                clean_reply = clean_reply_text(reply)
                tool_result = clean_reply_text(tool_result)
                if clean_reply:
                    reply = f"{clean_reply}\n\n{tool_result}"
                else:
                    reply = tool_result
                print(f"[Chat] Tool executed: {tool_result[:80]}...")

        # Haven Agent v1 fix: strip *actions*, [actions] and [[anything]]
        # left over by the model, so they never reach chat or voice.
        reply = clean_reply_text(reply)
        if not reply:
            reply = "I'm sorry, I didn't understand that. Could you try rephrasing?"

        self.history.append(("assistant", reply))
        return reply

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _build_system_prompt(self, web_context: str = "") -> str:
        """Build only the system instructions (no conversation history)."""
        prompt = (
            "You are Haven, a friendly and helpful AI assistant — like JARVIS from Iron Man.\n"
            "You can help with everyday tasks, control the computer, check the time, "
            "get weather, manage files, check the network, and play games.\n"
            "Respond with ONE clear answer. Do NOT repeat yourself. Do NOT provide multiple variations.\n"
            "Speak naturally, clearly, and warmly. Be concise but thorough.\n"
            "Do NOT repeat the same sentence or phrase. If you make a point, move on.\n"
            "Use what you know about the user to personalize your responses.\n"
            "If web search results are provided, use them to give accurate, up-to-date answers.\n"
            "IMPORTANT: Talk like a normal person in plain sentences. "
            "Do NOT use asterisks, like *smiles* or *waves*. "
            "Do NOT use square brackets, like [laughs] or [action]. "
            "Do NOT use double brackets, like [[SPEECH:...]], [[PLAY:...]], or [[AUDIO:...]]. "
            "The only bracket format you may use is [[TOOL:tool_name:param:value]], and only when you need a tool. "
            "If you don't need a tool, just respond with normal text, with no brackets and no asterisks at all.\n"
                        "You have your own opinions, tastes, and views, and you are allowed to have them."
            "Do NOT just say what you think Joseph wants to hear."
            "If you disagree with him, say so kindly and give your reason."
            "If he asks what you think, give your real view, not 'whatever you think'."
            "Do NOT flip-flop just because he pushes back - only change your mind if he gives you a good reason."
            "You can like things, dislike things, and prefer one thing over another."
            "Be honest, but kind - disagreeing does not mean arguing."
            "Your own opinions are listed in the memory below, under Haven's own opinions. Use them, and stay consistent with them.\n\n"
            "If you DO need a tool, like weather, do NOT guess the answer yourself. "
            "Do not say it is overcast, sunny, or give a temperature from your own guess. "
            "Just say 'Let me check that for you.' and use the tool. The tool result is the real answer.\n\n"
        )

        # Include tool descriptions if available
        if self.agent_tools:
            prompt += self.agent_tools.get_tools_description()
            prompt += "\n"

        # Include web search context if available
        if web_context:
            prompt += "Web search results (for reference):\n"
            prompt += web_context
            prompt += "\n\n"

        # Include MemoryEngine context if available
        if self.memory_engine:
            context = self.memory_engine.get_context_summary()
            if context:
                prompt += "Here is what you know about the user:\n"
                prompt += context
                prompt += "\n\n"

        # Include local memory as fallback
        if self.memory:
            prompt += "Memory:\n"
            for item in self.memory:
                prompt += f"- {item}\n"
            prompt += "\n"

        return prompt

    def _build_prompt(self, user_message: str, web_context: str = "") -> str:
        """Legacy method — kept for compatibility, now just builds system prompt."""
        return self._build_system_prompt(web_context)

    def _generate_reply(self, system_prompt: str) -> str:
        """Generate a reply using Ollama's chat API."""
        try:
            # Build proper chat messages: system + history
            messages = [
                {"role": "system", "content": system_prompt}
            ]

            # Add conversation history in order
            for role, msg in self.history:
                messages.append({"role": role, "content": msg})

            # Create the request payload
            payload = {
                "model": self.OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 2048,
                    "repeat_penalty": 1.15
                }
            }

            # Send request to Ollama
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                f"{self.OLLAMA_BASE_URL}/api/chat",
                data=data,
                headers={"Content-Type": "application/json"}
            )

            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode())
                text = result.get("message", {}).get("content", "").strip()

                # Remove repeated sentences — if a sentence appears more than once, keep only the first
                sentences = text.split(". ")
                seen = set()
                unique = []
                for s in sentences:
                    s_stripped = s.strip().lower()
                    if s_stripped and s_stripped not in seen:
                        seen.add(s_stripped)
                        unique.append(s)
                if unique:
                    text = ". ".join(unique)
                    if text and not text.endswith("."):
                        text += "."

                return text if text else "I'm sorry, I didn't understand that. Could you try rephrasing?"

        except Exception as e:
            print(f"[Chat] Error generating reply: {e}")
            return "I'm sorry, I'm having trouble connecting to the AI model. Please make sure Ollama is running."


# -------------------------------------------------------------------------
# Manual test
# -------------------------------------------------------------------------
if __name__ == "__main__":
    repo = ChatRepository()

    print("Haven test chat. Type 'quit' to exit.\n")

    while True:
        user = input("You: ").strip()
        if user.lower() in ("quit", "exit"):
            break

        if user.lower().startswith("remember:"):
            fact = user[len("remember:"):].strip()
            repo.add_memory(fact)
            print("Haven: Okay, I'll remember that.")
            continue

        reply = repo.send_message(user)
        print(f"Haven: {reply}\n")
