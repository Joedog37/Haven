# file: memory/engine.py
# Haven Memory Engine — learns from conversations and remembers facts across sessions

import json
import os
import re
from datetime import datetime


class MemoryEngine:
    """
    Manages persistent memory for Haven. Stores user facts, Haven facts,
    and conversation history. Automatically extracts important facts from
    conversations and loads recent context for new sessions.
    """

    # Keywords that signal a fact worth remembering
    FACT_PATTERNS = [
        r"(?i)i (?:am|'m)\s+(?:a|an)\s+([\w\s]+?)(?:\.|$)",  # "I am a doctor", "I'm a student"
        r"(?i)my\s+(\w+)\s+is\s+([\w\s]+?)(?:\.|$)",  # "my age is 25", "my hobby is reading"
        r"(?i)i (?:like|love|hate|prefer|enjoy|dislike)\s+([\w\s]+?)(?:\.|$)",
        r"(?i)i (?:have|own)\s+([\w\s]+?)(?:\.|$)",
        r"(?i)i (?:work|live|study)\s+(?:as|at|in)?\s*([\w\s]+?)(?:\.|$)",
        r"(?i)remember\s+that\s+([\w\s]+?)(?:\.|$)",
        r"(?i)my\s+name\s+is\s+(\w+)",
        r"(?i)my\s+real\s+name\s+is\s+(\w+)",
        r"(?i)call\s+me\s+(\w+)",
        r"(?i)i(?:'m| am)\s+(\d+)\s+(?:years?\s+old|year\s+old)",
        r"(?i)my\s+middle\s+name\s+is\s+(\w+)",
        r"(?i)i\s+(?:was|were)\s+born\s+(?:in|on)\s+([\w\s]+?)(?:\.|$)",
        r"(?i)i\s+live\s+in\s+([\w\s,]+?)(?:\.|$)",  # "I live in Castile, NY"
        r"(?i)my\s+favourite\s+(\w+)\s+is\s+([\w\s]+?)(?:\.|$)",  # "my favourite game is ..."
        r"(?i)my\s+favorite\s+(\w+)\s+is\s+([\w\s]+?)(?:\.|$)",
        r"(?i)i\s+(?:am|'m)\s+(\d+)\s+(?:years?\s+old|year\s+old)",
    ]

    def __init__(self, path="storage.json", profile_id=None):
        """
        Initialize the memory engine.

        Args:
            path: Path to the storage JSON file.
            profile_id: Optional profile identifier (username, device ID, etc.).
                        When set, Haven addresses the user by this name and tracks
                        which device/session this memory belongs to.
        """
        self.path = path
        self.profile_id = profile_id

        # Default memory structure
        self.data = {
            "user": {
                "name": None,
                "facts": []
            },
            "haven": {
                "facts": []
            },
            "conversation_history": [],
            "learned_facts": []  # Facts auto-extracted from conversations
        }

        self._load()

        # Apply profile ID if provided and no name is already stored
        if self.profile_id and not self.data["user"]["name"]:
            self.data["user"]["name"] = self.profile_id
            self._save()

    # -----------------------------
    # LOAD / SAVE
    # -----------------------------
    def _load(self):
        """Load memory from disk."""
        if not os.path.exists(self.path):
            print(f"[Memory] No storage.json found, starting fresh.")
            return

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                loaded = json.load(f)

            if isinstance(loaded, dict):
                # Merge carefully to preserve new keys
                for key in loaded:
                    if key in self.data:
                        if isinstance(self.data[key], dict):
                            self.data[key].update(loaded[key])
                        elif isinstance(self.data[key], list) and isinstance(loaded[key], list):
                            self.data[key] = loaded[key]
                    else:
                        self.data[key] = loaded[key]

            print(f"[Memory] Loaded memory from {self.path}")
            print(f"  User facts: {len(self.data['user']['facts'])}")
            print(f"  Learned facts: {len(self.data.get('learned_facts', []))}")
            print(f"  Conversations: {len(self.data['conversation_history'])}")

        except Exception as e:
            print(f"[Memory] Error loading memory: {e}")

    def _save(self):
        """Save memory to disk."""
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"[Memory] Error saving memory: {e}")

    # -----------------------------
    # MEMORY FUNCTIONS
    # -----------------------------
    def add_user_fact(self, fact: str):
        """Add a fact about the user."""
        fact = fact.strip()
        if fact and fact not in self.data["user"]["facts"]:
            self.data["user"]["facts"].append(fact)
            self._save()
            print(f"[Memory] Remembered user fact: {fact}")

    def add_haven_fact(self, fact: str):
        """Add a fact about Haven."""
        fact = fact.strip()
        if fact and fact not in self.data["haven"]["facts"]:
            self.data["haven"]["facts"].append(fact)
            self._save()

    def add_history(self, user_text: str, haven_reply: str):
        """Save a conversation exchange and try to learn from it."""
        entry = {
            "user": user_text,
            "haven": haven_reply,
            "timestamp": datetime.now().isoformat()
        }
        self.data["conversation_history"].append(entry)

        # Haven Agent v1.2: keep 500 exchanges, not 100, so she remembers longer.
        # 500 chats is still a small file, about a few hundred KB.
        if len(self.data["conversation_history"]) > 500:
            self.data["conversation_history"] = self.data["conversation_history"][-500:]

        # Try to learn new facts from this exchange
        before = len(self.data.get("learned_facts", []))
        self._learn_from_exchange(user_text, haven_reply)
        self._save()
        # Haven Agent v1.2: plain-English learning log, so Joseph can see
        # what she actually learned, without opening storage.json.
        try:
            learned_now = self.data.get("learned_facts", [])[before:]
            if learned_now:
                log_folder = os.path.join(os.path.dirname(self.path), "..", "logs")
                os.makedirs(log_folder, exist_ok=True)
                log_path = os.path.join(log_folder, "haven_learned.txt")
                with open(log_path, "a", encoding="utf-8") as f:
                    for fact in learned_now:
                        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M')} - Learned: {fact}\n")
        except Exception:
            pass

    # -----------------------------
    # LEARNING — Auto-extract facts from conversations
    # -----------------------------
    def _learn_from_exchange(self, user_text: str, haven_reply: str):
        """
        Try to extract important facts from a conversation exchange.
        Looks for patterns like 'I am...', 'my name is...', 'I like...', etc.
        """
        facts_found = []

        # Check for name patterns - only match explicit name introductions
        # Avoid matching "I'm just", "I'm having", "I'm trying", etc.
        name_match = re.search(r"(?i)(?:my\s+(?:real\s+)?name\s+is|call\s+me)\s+(\w+)", user_text)
        if name_match:
            name = name_match.group(1).capitalize()
            # Filter out common non-name words
            non_names = {"just", "the", "a", "an", "i", "am", "is", "it", "to", "for", "and", "not", "you", "my", "your"}
            if name.lower() not in non_names and self.data["user"]["name"] != name:
                self.data["user"]["name"] = name
                facts_found.append(f"User's name is {name}")
                print(f"[Memory] Learned name: {name}")

        # Haven Agent v1.2: "remember:" / "remember that" / "please remember"
        # means the whole rest of the sentence is a fact to keep, word for word.
        remember_match = re.search(r"(?i)(?:remember(?: that)?:?|please remember)\s+(.+)", user_text)
        if remember_match:
            fact_text = remember_match.group(1).strip().rstrip('.')
            if len(fact_text) > 3:
                normalized = fact_text.lower().strip()
                existing = [f.lower() for f in self.data.get("learned_facts", [])]
                if normalized not in existing:
                    self.data.setdefault("learned_facts", []).append(fact_text)
                    facts_found.append(fact_text)
                    print(f"[Memory] Remembered: {fact_text}")

        # Check for general fact patterns
        for pattern in self.FACT_PATTERNS:
            matches = re.finditer(pattern, user_text)
            for match in matches:
                fact_text = match.group(0).strip().rstrip('.')
                if fact_text and len(fact_text) > 5:
                    # Normalize for dedup
                    normalized = fact_text.lower().strip()
                    existing = [f.lower() for f in self.data.get("learned_facts", [])]
                    if normalized not in existing:
                        self.data.setdefault("learned_facts", []).append(fact_text)
                        facts_found.append(fact_text)
                        print(f"[Memory] Learned fact: {fact_text}")

        # Check if Haven confirmed something the user said
        confirmation_patterns = [
            r"(?i)okay(?:,| )?i(?:'|'ll| will) (?:remember|note)",
            r"(?i)got\s+it",
            r"(?i)understood",
        ]
        for pattern in confirmation_patterns:
            if re.search(pattern, haven_reply):
                # User's message was confirmed — likely a fact worth keeping
                if len(facts_found) == 0 and len(user_text) > 10:
                    # No pattern matched but Haven confirmed — save the whole statement
                    normalized = user_text.lower().strip()
                    existing = [f.lower() for f in self.data.get("learned_facts", [])]
                    if normalized not in existing:
                        self.data.setdefault("learned_facts", []).append(user_text.strip())
                        print(f"[Memory] Saved confirmed statement: {user_text.strip()}")
                break

    # -----------------------------
    # CONTEXT — Build memory context for the chat prompt
    # -----------------------------
    def get_context_summary(self, max_facts=20) -> str:
        """
        Build a summary of what Haven knows for the chat prompt.
        Includes user name, key facts, and recent conversation highlights.
        """
        parts = []

        # Haven Agent v1.2: plain-English brain file.
        # Joseph can edit Pc/memory/HAVEN_KNOWS.md in Notepad, no Python needed.
        # Anything written there is included here, so Haven knows it every chat.
        try:
            knows_path = os.path.join(os.path.dirname(self.path), "HAVEN_KNOWS.md")
            if os.path.exists(knows_path):
                with open(knows_path, "r", encoding="utf-8") as f:
                    knows = f.read().strip()
                if knows:
                    parts.append("What Haven knows (from HAVEN_KNOWS.md, Joseph can edit this file):")
                    parts.append(knows)
        except Exception:
            pass

        # Haven Agent v1.7: plain-English opinions file.
        # Joseph can edit Pc/memory/HAVEN_OPINIONS.md in Notepad, no Python needed.
        # Anything written there is included here, so Haven keeps her own
        # opinions every chat, instead of just agreeing with Joseph.
        try:
            opinions_path = os.path.join(os.path.dirname(self.path), "HAVEN_OPINIONS.md")
            if os.path.exists(opinions_path):
                with open(opinions_path, "r", encoding="utf-8") as f:
                    opinions_lines = [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]
                    opinions = "\n".join(opinions_lines)
                if opinions:
                    parts.append("Haven's own opinions (from HAVEN_OPINIONS.md, Joseph can edit this file):")
                    parts.append(opinions)
        except Exception:
            pass

        # User identity
        user_name = self.data["user"]["name"]
        if user_name:
            parts.append(f"The user's name is {user_name}.")
            parts.append(f"Address the user as {user_name} naturally in conversation.")

        # User facts
        user_facts = self.data["user"]["facts"]
        if user_facts:
            recent = user_facts[-max_facts:]
            parts.append("Things you know about the user:")
            for fact in recent:
                parts.append(f"  - {fact}")

        # Learned facts from conversations
        learned = self.data.get("learned_facts", [])
        if learned:
            recent_learned = learned[-max_facts:]
            parts.append("Things learned from conversations:")
            for fact in recent_learned:
                parts.append(f"  - {fact}")

        # Haven facts
        haven_facts = self.data["haven"]["facts"]
        if haven_facts:
            parts.append("About yourself (Haven):")
            for fact in haven_facts:
                parts.append(f"  - {fact}")

        if not parts:
            return ""

        return "\n".join(parts)

    def get_recent_conversations(self, count=5) -> list:
        """Get the most recent conversation exchanges for context."""
        return self.data["conversation_history"][-count:]

    # -----------------------------
    # PROCESS INPUT FOR MODEL
    # -----------------------------
    def process(self, text: str) -> str:
        """
        Process text before sending to the model.
        Returns the original text — the memory context is added to the prompt separately.
        """
        return text

    # -----------------------------
    # MEMORY MANAGEMENT
    # -----------------------------
    def clear_history(self):
        """Clear conversation history but keep learned facts."""
        self.data["conversation_history"] = []
        self._save()
        print("[Memory] Conversation history cleared.")

    def clear_learned_facts(self):
        """Clear auto-learned facts."""
        self.data["learned_facts"] = []
        self._save()
        print("[Memory] Learned facts cleared.")

    def forget_fact(self, fact: str) -> bool:
        """Remove a specific fact."""
        fact_lower = fact.lower()
        # Check user facts
        self.data["user"]["facts"] = [f for f in self.data["user"]["facts"] if f.lower() != fact_lower]
        # Check learned facts
        self.data["learned_facts"] = [f for f in self.data.get("learned_facts", []) if f.lower() != fact_lower]
        self._save()
        return True

    def get_stats(self) -> dict:
        """Return memory statistics."""
        return {
            "user_name": self.data["user"]["name"],
            "profile_id": self.profile_id,
            "user_facts_count": len(self.data["user"]["facts"]),
            "learned_facts_count": len(self.data.get("learned_facts", [])),
            "haven_facts_count": len(self.data["haven"]["facts"]),
            "conversation_count": len(self.data["conversation_history"]),
        }
