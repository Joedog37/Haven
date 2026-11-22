# Games module - text-based games for Haven
import random


class GameEngine:
    """Text-based games that Haven can play with the user."""

    def __init__(self):
        self.active_game = None  # Current game state
        self.games = {
            "trivia": "Test your knowledge with fun trivia questions!",
            "guessing": "I think of a number, you try to guess it!",
            "wordle": "Guess the 5-letter word in 6 tries!",
            "rockpaperscissors": "Classic game — rock, paper, or scissors?",
            "tictactoe": "Play tic-tac-toe against me!",
            "20questions": "Think of something, I'll try to guess it!",
        }

    def list_games(self) -> str:
        """List available games."""
        if not self.games:
            return "No games available."
        lines = ["Available games:"]
        for name, desc in self.games.items():
            lines.append(f"  • {name}: {desc}")
        lines.append("\nJust say 'play <game>' to start!")
        return "\n".join(lines)

    def start_game(self, game_name: str) -> str:
        """Start a game by name."""
        game = game_name.lower().replace(" ", "").replace("-", "")

        if game == "trivia":
            self.active_game = {"type": "trivia", "score": 0, "round": 0}
            return self._trivia_question()
        elif game == "guessing" or game == "numberguessing":
            self.active_game = {
                "type": "guessing",
                "number": random.randint(1, 100),
                "attempts": 0,
                "max_attempts": 7,
            }
            return "I'm thinking of a number between 1 and 100. You have 7 tries to guess it! What's your first guess?"
        elif game == "wordle":
            words = ["APPLE", "HOUSE", "BRAIN", "OCEAN", "LIGHT", "DREAM", "WORLD", "MUSIC", "POWER", "SPACE"]
            self.active_game = {
                "type": "wordle",
                "word": random.choice(words),
                "guesses": [],
                "max_guesses": 6,
            }
            return f"I'm thinking of a 5-letter word. You have 6 tries!\n\n  _ _ _ _ _\n\nGuess a word!"
        elif game == "rockpaperscissors" or game == "rps":
            return "Rock, Paper, Scissors! What's your choice?"
        elif game == "tictactoe":
            self.active_game = {
                "type": "tictactoe",
                "board": [" "] * 9,
                "current": "X",
                "winner": None,
            }
            return self._tictactoe_board() + "\n\nYou're X. Enter a position (1-9) to place your mark!"
        elif game == "20questions":
            self.active_game = {
                "type": "20questions",
                "questions": [],
                "answers": [],
                "count": 0,
                "max_questions": 20,
            }
            return "Think of something (an animal, object, or person), and I'll try to guess what it is!\n\nIs it alive? (yes/no)"
        else:
            return f"Unknown game: {game_name}. Type 'games' to see available games."

    def play_turn(self, user_input: str) -> str:
        """Process a turn in the active game."""
        if not self.active_game:
            return "No game is currently active. Type 'play <game>' to start one!"

        game_type = self.active_game["type"]

        if game_type == "trivia":
            return self._trivia_answer(user_input)
        elif game_type == "guessing":
            return self._guessing_turn(user_input)
        elif game_type == "wordle":
            return self._wordle_turn(user_input)
        elif game_type == "rockpaperscissors":
            return self._rps_turn(user_input)
        elif game_type == "tictactoe":
            return self._tictactoe_turn(user_input)
        elif game_type == "20questions":
            return self._questions_turn(user_input)

        return "Something went wrong with the game. Try starting a new one!"

    def end_game(self) -> str:
        """End the current game."""
        if self.active_game:
            game_type = self.active_game["type"]
            self.active_game = None
            return f"Game ended. Thanks for playing {game_type}! Type 'play <game>' to start a new game."
        return "No game is currently active."

    # ---- Trivia ----
    def _trivia_question(self) -> str:
        questions = [
            {"q": "What planet is known as the Red Planet?", "a": "mars"},
            {"q": "What is the largest ocean on Earth?", "a": "pacific"},
            {"q": "Who painted the Mona Lisa?", "a": "da vinci"},
            {"q": "What is the chemical symbol for gold?", "a": "au"},
            {"q": "How many continents are there?", "a": "7"},
            {"q": "What year did the Titanic sink?", "a": "1912"},
            {"q": "What is the speed of light approximately in mph?", "a": "670000000"},
            {"q": "What is the smallest country in the world?", "a": "vatican"},
            {"q": "What element does 'O' represent on the periodic table?", "a": "oxygen"},
            {"q": "How many bones are in the adult human body?", "a": "206"},
            {"q": "What is the capital of Japan?", "a": "tokyo"},
            {"q": "What gas do plants absorb from the atmosphere?", "a": "carbon dioxide"},
            {"q": "Who wrote Romeo and Juliet?", "a": "shakespeare"},
            {"q": "What is the hardest natural substance on Earth?", "a": "diamond"},
            {"q": "What is the largest mammal?", "a": "blue whale"},
        ]
        self.active_game["round"] += 1
        q = random.choice(questions)
        self.active_game["current_question"] = q
        return f"Question {self.active_game['round']}: {q['q']}"

    def _trivia_answer(self, answer: str) -> str:
        if not self.active_game or "current_question" not in self.active_game:
            return self._trivia_question()

        correct = self.active_game["current_question"]["a"].lower()
        if correct in answer.lower() or answer.lower() in correct:
            self.active_game["score"] += 1
            result = f"✓ Correct! Score: {self.active_game['score']}/{self.active_game['round']}\n\n"
            result += self._trivia_question()
            return result
        else:
            ans = self.active_game["current_question"]["a"]
            result = f"✗ Wrong! The answer was: {ans}. Score: {self.active_game['score']}/{self.active_game['round']}\n\n"
            result += self._trivia_question()
            return result

    # ---- Number Guessing ----
    def _guessing_turn(self, guess: str) -> str:
        try:
            guess = int(guess.strip())
        except ValueError:
            return "Please enter a number!"

        game = self.active_game
        game["attempts"] += 1
        remaining = game["max_attempts"] - game["attempts"]

        if guess == game["number"]:
            return f"🎉 Correct! The number was {game['number']}. You got it in {game['attempts']} attempt(s)!"
        elif guess < game["number"]:
            return f"📈 Higher! ({remaining} tries left)"
        else:
            return f"📉 Lower! ({remaining} tries left)"

    # ---- Wordle ----
    def _wordle_turn(self, guess: str) -> str:
        guess = guess.strip().upper()
        if len(guess) != 5:
            return "Please guess a 5-letter word!"

        game = self.active_game
        game["guesses"].append(guess)

        if len(game["guesses"]) > game["max_guesses"]:
            return f"Game over! The word was {game['word']}. Better luck next time!"

        # Generate feedback
        feedback = ""
        target = game["word"]
        for i, letter in enumerate(guess):
            if letter == target[i]:
                feedback += f"\033[42m{letter}\033[0m"  # Green — correct position
            elif letter in target:
                feedback += f"\033[43m{letter}\033[0m"  # Yellow — wrong position
            else:
                feedback += f"  {letter} "  # Gray — not in word

        # Simple text feedback
        correct = sum(1 for i, l in enumerate(guess) if l == target[i])
        present = sum(1 for l in guess if l in target) - correct
        feedback_text = f"Guess {len(game['guesses'])}: {guess}\n  🟢 Correct: {correct}  🟡 Present: {present}  ⚫ Absent: {5 - correct - present}"

        if guess == target:
            return f"{feedback_text}\n\n🎉 Congratulations! You guessed {target} in {len(game['guesses'])} tries!"

        return f"{feedback_text}\n\nGuess another word!"

    # ---- Rock Paper Scissors ----
    def _rps_turn(self, choice: str) -> str:
        choice = choice.strip().lower()
        options = ["rock", "paper", "scissors"]

        if choice not in options:
            return "Please choose rock, paper, or scissors!"

        ai_choice = random.choice(options)
        if choice == ai_choice:
            return f"You chose {choice}, I chose {ai_choice}. It's a tie!"
        elif (choice == "rock" and ai_choice == "scissors") or \
             (choice == "paper" and ai_choice == "rock") or \
             (choice == "scissors" and ai_choice == "paper"):
            return f"You chose {choice}, I chose {ai_choice}. You win! 🎉"
        else:
            return f"You chose {choice}, I chose {ai_choice}. I win! 😄"

    # ---- Tic Tac Toe ----
    def _tictactoe_board(self) -> str:
        b = self.active_game["board"]
        board = (
            f"  {b[0]} | {b[1]} | {b[2]}  \n"
            f"---|---|---\n"
            f"  {b[3]} | {b[4]} | {b[5]}  \n"
            f"---|---|---\n"
            f"  {b[6]} | {b[7]} | {b[8]}  \n"
        )
        return board

    def _tictactoe_turn(self, pos: str) -> str:
        try:
            pos = int(pos.strip()) - 1
        except ValueError:
            return "Please enter a number from 1 to 9!"

        if pos < 0 or pos > 8:
            return "Invalid position! Enter 1-9."

        game = self.active_game
        if game["board"][pos] != " ":
            return "That spot is taken! Choose another."

        # Player move
        game["board"][pos] = "X"
        winner = self._check_tictactoe_winner()
        if winner:
            return self._tictactoe_board() + f"\n\n🎉 {'You win!' if winner == 'X' else 'I win!'}"
        if " " not in game["board"]:
            return self._tictactoe_board() + "\n\nIt's a draw!"

        # AI move (simple: random empty spot)
        empty = [i for i, v in enumerate(game["board"]) if v == " "]
        ai_pos = random.choice(empty)
        game["board"][ai_pos] = "O"
        winner = self._check_tictactoe_winner()
        if winner:
            return self._tictactoe_board() + f"\n\n{'You win! 🎉' if winner == 'X' else 'I win! 😄'}"

        return self._tictactoe_board() + "\n\nYour turn (X). Enter a position (1-9)!"

    def _check_tictactoe_winner(self) -> str | None:
        b = self.active_game["board"]
        wins = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # cols
            [0, 4, 8], [2, 4, 6],              # diagonals
        ]
        for a, b_idx, c in wins:
            if b[a] == b[b_idx] == b[c] and b[a] != " ":
                return b[a]
        return None

    # ---- 20 Questions ----
    def _questions_turn(self, answer: str) -> str:
        game = self.active_game
        game["count"] += 1
        answer = answer.strip().lower()

        if game["count"] >= game["max_questions"]:
            return f"I've used all my questions! What were you thinking of? Tell me and I'll try to remember for next time!"

        # Simple decision tree
        questions = [
            ("Is it alive?", ["yes", "no"]),
            ("Is it an animal?", ["yes", "no"]),
            ("Is it bigger than a car?", ["yes", "no"]),
            ("Does it have wheels?", ["yes", "no"]),
            ("Is it something you eat?", ["yes", "no"]),
            ("Is it found in a house?", ["yes", "no"]),
            ("Is it electronic?", ["yes", "no"]),
            ("Is it a person?", ["yes", "no"]),
            ("Is it a fruit or vegetable?", ["yes", "no"]),
            ("Does it have four legs?", ["yes", "no"]),
        ]

        if game["count"] <= len(questions):
            q = questions[game["count"] - 1][0]
            return f"Question {game['count']}/{game['max_questions']}: {q} (yes/no)"
        else:
            # Make a guess
            guesses = ["a computer", "a dog", "a phone", "a car", "a tree", "a book", "a cat", "a chair"]
            guess = random.choice(guesses)
            return f"Let me guess... is it {guess}? (yes/no)"

    def get_status(self) -> dict:
        """Return status of game engine."""
        return {
            "active_game": self.active_game["type"] if self.active_game else None,
            "available_games": list(self.games.keys()),
        }
