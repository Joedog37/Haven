# AI-generated Oregon Trail game engine for Haven
# Dynamic story generation with random events and persistent state
import json
import os
import random
from datetime import datetime


class OregonTrailGame:
    """AI-generated Oregon Trail adventure with persistent state."""

    def __init__(self, save_dir="saves"):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
        self.game_state = None
        self.save_file = os.path.join(save_dir, "oregon_save.json")

    def new_game(self, player_name: str, profession: str) -> dict:
        """Start a new Oregon Trail journey."""
        self.game_state = {
            "player": {
                "name": player_name,
                "profession": profession,
                "health": 100,
                "max_health": 100,
            },
            "party": [
                {"name": player_name, "health": 100, "alive": True},
            ],
            "resources": {
                "food": self._get_starting_food(profession),
                "ammo": 50,
                "medicine": 5,
                "gold": self._get_starting_gold(profession),
                "oxen": 4,
            },
            "location": "independence",
            "mile": 0,
            "total_miles": 2000,
            "day": 1,
            "month": 4,  # April start
            "year": 1848,
            "weather": "clear",
            "speed": "normal",
            "rest_days": 0,
            "events": [],
            "story_log": [],
            "flags": {},
            "created_at": datetime.now().isoformat(),
        }
        self._save()
        intro = self._generate_intro()
        return {
            "type": "game_start",
            "message": intro,
            "state": self._get_player_summary(),
            "choices": self._get_choices(),
        }

    def make_choice(self, choice_index: int, custom_input: str = None) -> dict:
        """Process a player's choice and advance the journey."""
        if not self.game_state:
            return {"type": "error", "message": "No active game. Start a new game first!"}

        choices = self._get_choices()
        if 0 <= choice_index < len(choices):
            choice = choices[choice_index]
            return self._process_choice(choice.get("action", ""), custom_input)
        elif custom_input:
            return self._process_choice("custom", custom_input)
        else:
            return {"type": "error", "message": "Invalid choice. Please select a valid option."}

    def travel(self) -> dict:
        """Travel along the Oregon Trail."""
        if not self.game_state:
            return {"type": "error", "message": "No active game."}

        state = self.game_state
        resources = state["resources"]

        # Check if can travel
        if resources["oxen"] <= 0:
            return {
                "type": "error",
                "message": "You have no oxen to pull the wagon! You cannot travel.",
                "state": self._get_player_summary(),
                "choices": self._get_choices(),
            }

        # Calculate distance based on speed and weather
        distance = self._calculate_distance()
        state["mile"] += distance
        state["day"] += 1
        self._update_month()

        # Consume food
        food_consumed = len(state["party"]) * 2
        resources["food"] -= food_consumed

        # Random event
        event = self._random_event()
        message = f"Day {state['day']}: You travel {distance} miles. (Mile {state['mile']}/{state['total_miles']})\n"
        message += f"Weather: {state['weather'].title()}\n"
        message += f"Food consumed: {food_consumed}\n\n"

        if event:
            message += event["message"]
            state["events"].append(event)
            state["story_log"].append(f"Day {state['day']}: {event['title']}")

        # Check for starvation
        if resources["food"] <= 0:
            resources["food"] = 0
            health_loss = random.randint(5, 15)
            state["player"]["health"] = max(0, state["player"]["health"] - health_loss)
            message += f"\n⚠️ You have no food! You lose {health_loss} health from starvation."

        # Check for destination
        if state["mile"] >= state["total_miles"]:
            message += "\n\n🎉 Congratulations! You have reached Oregon! Your journey is complete!"
            state["flags"]["completed"] = True

        # Check for death
        if state["player"]["health"] <= 0:
            message += "\n\n💀 You have perished on the trail. Your journey ends here..."
            state["flags"]["dead"] = True

        self._save()
        return {
            "type": "travel",
            "message": message,
            "state": self._get_player_summary(),
            "choices": self._get_choices(),
        }

    def rest(self) -> dict:
        """Rest to recover health."""
        if not self.game_state:
            return {"type": "error", "message": "No active game."}

        state = self.game_state
        resources = state["resources"]

        # Consume food while resting
        food_consumed = len(state["party"]) * 2
        resources["food"] -= food_consumed

        # Recover health
        health_gain = random.randint(10, 20)
        if resources["medicine"] > 0:
            health_gain += 10
            resources["medicine"] -= 1

        state["player"]["health"] = min(state["player"]["max_health"],
                                         state["player"]["health"] + health_gain)
        state["day"] += 1
        state["rest_days"] += 1
        self._update_month()

        message = f"Day {state['day']}: You rest and recover {health_gain} health.\n"
        message += f"Health: {state['player']['health']}/{state['player']['max_health']}\n"
        message += f"Food consumed: {food_consumed}"

        if resources["food"] <= 0:
            resources["food"] = 0
            message += "\n⚠️ You have no food!"

        self._save()
        return {
            "type": "rest",
            "message": message,
            "state": self._get_player_summary(),
            "choices": self._get_choices(),
        }

    def hunt(self) -> dict:
        """Hunt for food."""
        if not self.game_state:
            return {"type": "error", "message": "No active game."}

        resources = self.game_state["resources"]

        if resources["ammo"] <= 0:
            return {
                "type": "error",
                "message": "You have no ammo for hunting!",
                "state": self._get_player_summary(),
                "choices": self._get_choices(),
            }

        # Hunt success based on profession
        success_chance = 60
        if self.game_state["player"]["profession"] == "hunter":
            success_chance = 80

        if random.randint(1, 100) <= success_chance:
            resources["ammo"] -= random.randint(1, 3)
            food_gained = random.randint(10, 30)
            resources["food"] += food_gained
            message = f"🎯 Successful hunt! You gain {food_gained} food. Ammo used: {random.randint(1, 3)}"
        else:
            resources["ammo"] -= 1
            message = "🎯 You hunt but find nothing. The game is scarce today."

        self.game_state["day"] += 1
        self._update_month()
        self._save()

        return {
            "type": "hunt",
            "message": message,
            "state": self._get_player_summary(),
            "choices": self._get_choices(),
        }

    def trade(self) -> dict:
        """Trade at a trading post."""
        if not self.game_state:
            return {"type": "error", "message": "No active game."}

        resources = self.game_state["resources"]
        trade_text = "🏪 Trading Post:\n\n"
        trade_text += "Available items:\n"
        trade_text += "  • Food (10 units) - 5 gold\n"
        trade_text += "  • Ammo (20 units) - 5 gold\n"
        trade_text += "  • Medicine (2 units) - 10 gold\n"
        trade_text += "  • Oxen (1) - 15 gold\n\n"
        trade_text += f"Your Gold: {resources['gold']}"

        return {
            "type": "trade",
            "message": trade_text,
            "state": self._get_player_summary(),
            "choices": self._get_choices(),
        }

    def buy_item(self, item: str) -> dict:
        """Buy an item from the trading post."""
        if not self.game_state:
            return {"type": "error", "message": "No active game."}

        resources = self.game_state["resources"]
        prices = {
            "food": {"cost": 5, "amount": 10},
            "ammo": {"cost": 5, "amount": 20},
            "medicine": {"cost": 10, "amount": 2},
            "oxen": {"cost": 15, "amount": 1},
        }

        if item not in prices:
            return {"type": "error", "message": "Unknown item."}

        price = prices[item]
        if resources["gold"] < price["cost"]:
            return {"type": "error", "message": f"Not enough gold! You need {price['cost']} gold."}

        resources["gold"] -= price["cost"]
        resources[item] += price["amount"]

        return {
            "type": "buy",
            "message": f"You buy {price['amount']} {item} for {price['cost']} gold.",
            "state": self._get_player_summary(),
            "choices": self._get_choices(),
        }

    def save_game(self) -> dict:
        """Save the current game state."""
        if not self.game_state:
            return {"type": "error", "message": "No active game to save."}
        self._save()
        return {"type": "save", "message": "Game saved successfully!"}

    def load_game(self) -> dict:
        """Load a saved game."""
        if os.path.exists(self.save_file):
            with open(self.save_file, "r") as f:
                self.game_state = json.load(f)
            return {
                "type": "load",
                "message": f"Welcome back, {self.game_state['player']['name']}! Your journey continues...",
                "state": self._get_player_summary(),
                "choices": self._get_choices(),
            }
        return {"type": "error", "message": "No saved game found."}

    def get_status(self) -> dict:
        """Return the current game status."""
        if self.game_state:
            return {
                "active": True,
                "player": self._get_player_summary(),
                "location": self.game_state["location"],
                "mile": self.game_state["mile"],
            }
        return {"active": False}

    # ---- Internal Methods ----

    def _get_starting_food(self, profession: str) -> int:
        food_map = {"hunter": 80, "farmer": 60, "merchant": 70, "soldier": 50}
        return food_map.get(profession.lower(), 60)

    def _get_starting_gold(self, profession: str) -> int:
        gold_map = {"hunter": 30, "farmer": 40, "merchant": 60, "soldier": 35}
        return gold_map.get(profession.lower(), 40)

    def _calculate_distance(self) -> int:
        state = self.game_state
        base_distance = 15

        # Weather modifier
        if state["weather"] == "storm":
            base_distance //= 2
        elif state["weather"] == "rain":
            base_distance = int(base_distance * 0.75)

        # Speed modifier
        if state["speed"] == "fast":
            base_distance += 5
        elif state["speed"] == "slow":
            base_distance -= 5

        # Random variation
        return max(5, base_distance + random.randint(-5, 5))

    def _update_month(self):
        state = self.game_state
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        month_idx = state["month"] - 1

        if month_idx < 0 or month_idx >= 12:
            return

        state["day"] = state["day"] % days_in_month[month_idx]
        if state["day"] == 0:
            state["month"] += 1
            if state["month"] > 12:
                state["month"] = 1
                state["year"] += 1

        # Update weather based on season
        self._update_weather()

    def _update_weather(self):
        state = self.game_state
        month = state["month"]

        # Seasonal weather
        if month in [12, 1, 2]:  # Winter
            state["weather"] = random.choice(["snow", "snow", "cold", "clear"])
        elif month in [3, 4, 11]:  # Spring/Fall
            state["weather"] = random.choice(["rain", "rain", "clear", "clear"])
        else:  # Summer
            state["weather"] = random.choice(["clear", "clear", "clear", "storm"])

    def _random_event(self) -> dict:
        """Generate a random event based on location and progress."""
        state = self.game_state
        mile = state["mile"]
        resources = state["resources"]

        # Events based on location
        events = []

        # River crossings
        if 400 < mile < 450 and not state["flags"].get("platte_river"):
            state["flags"]["platte_river"] = True
            return {
                "title": "Platte River Crossing",
                "message": "🌊 You reach the Platte River! The water is high and the current is strong.\n"
                           "You carefully cross with your wagon. The oxen struggle but make it across.",
            }
        elif 800 < mile < 850 and not state["flags"].get("snake_river"):
            state["flags"]["snake_river"] = True
            return {
                "title": "Snake River Crossing",
                "message": "🌊 The Snake River blocks your path! You must build a raft to cross.\n"
                           "After hours of work, you successfully cross the river.",
            }

        # Random encounters
        if random.randint(1, 100) <= 20:
            encounter_events = [
                {
                    "title": "Friendly Trader",
                    "message": "🤝 A friendly trader offers you supplies at a discount!\n"
                               "You gain 10 food and 5 ammo.",
                    "effect": lambda: resources.update({"food": resources["food"] + 10, "ammo": resources["ammo"] + 5}),
                },
                {
                    "title": "Broken Wagon Wheel",
                    "message": "🔧 A wagon wheel breaks! You spend time repairing it.\n"
                               "You lose a day but the wagon is fixed.",
                    "effect": lambda: state.update({"day": state["day"] + 1}),
                },
                {
                    "title": "Wildlife Sighting",
                    "message": "🦌 You spot a herd of deer! You hunt and gain extra food.\n"
                               "You gain 15 food.",
                    "effect": lambda: resources.update({"food": resources["food"] + 15}),
                },
                {
                    "title": "Storm Warning",
                    "message": "⛈️ A storm is approaching! You take shelter and wait it out.\n"
                               "You lose a day but stay safe.",
                    "effect": lambda: state.update({"day": state["day"] + 1, "weather": "storm"}),
                },
                {
                    "title": "Illness",
                    "message": "🤒 Someone in your party falls ill!\n"
                               "You use medicine to treat them.",
                    "effect": lambda: resources.update({"medicine": max(0, resources["medicine"] - 1)}),
                },
                {
                    "title": "Lost Supplies",
                    "message": "📦 Some supplies were lost during travel!\n"
                               "You lose 5 food.",
                    "effect": lambda: resources.update({"food": max(0, resources["food"] - 5)}),
                },
            ]
            event = random.choice(encounter_events)
            if "effect" in event:
                event["effect"]()
                del event["effect"]
            return event

        return None

    def _generate_intro(self) -> str:
        player = self.game_state["player"]
        intros = [
            f"You are {player['name']}, a {player['profession']}. "
            f"The year is 1848, and you have decided to join the great migration to Oregon. "
            f"From Independence, Missouri, you will travel 2,000 miles across the wilderness "
            f"to reach the promised land of Oregon.\n\n"
            f"Your journey begins in April. You have supplies, oxen, and hope.\n\n"
            f"What do you do?",
            f"You are {player['name']}, a {player['profession']}. "
            f"Gold has been discovered in California, and the Oregon Trail is bustling "
            f"with travelers. You pack your wagon and join the caravan.\n\n"
            f"The trail is dangerous — disease, starvation, and hostile territory await.\n\n"
            f"What do you do?",
        ]
        return random.choice(intros)

    def _get_choices(self) -> list:
        if not self.game_state:
            return []

        state = self.game_state
        choices = [
            {"text": "🚶 Travel", "action": "travel"},
            {"text": "🏕️ Rest", "action": "rest"},
            {"text": "🎯 Hunt", "action": "hunt"},
            {"text": "💾 Save Game", "action": "save"},
        ]

        # Add location-specific choices
        if state["location"] == "independence":
            choices.append({"text": "🏪 Visit Trading Post", "action": "trade"})
        elif state["mile"] > 500 and state["mile"] < 600:
            choices.append({"text": "🏪 Fort Laramie Trading Post", "action": "trade"})
        elif state["mile"] > 1000 and state["mile"] < 1100:
            choices.append({"text": "🏪 Fort Hall Trading Post", "action": "trade"})

        choices.append({"text": "📊 View Stats", "action": "stats"})
        choices.append({"text": "⌨️ Custom Action", "action": "custom"})

        return choices

    def _process_choice(self, action: str, custom_input: str = None) -> dict:
        if not self.game_state:
            return {"type": "error", "message": "No active game."}

        if action == "travel":
            return self.travel()
        elif action == "rest":
            return self.rest()
        elif action == "hunt":
            return self.hunt()
        elif action == "trade":
            return self.trade()
        elif action == "save":
            return self.save_game()
        elif action == "stats":
            return self._show_stats()
        elif action == "custom" and custom_input:
            return self._process_custom_action(custom_input)
        else:
            return {"type": "error", "message": "Unknown action."}

    def _show_stats(self) -> dict:
        state = self.game_state
        resources = state["resources"]
        player = state["player"]

        stats_text = "📊 Journey Stats:\n\n"
        stats_text += f"Player: {player['name']} ({player['profession']})\n"
        stats_text += f"Health: {player['health']}/{player['max_health']}\n\n"
        stats_text += f"Progress: Mile {state['mile']}/{state['total_miles']} ({state['mile']*100//state['total_miles']}%)\n"
        stats_text += f"Location: {state['location'].title()}\n"
        stats_text += f"Date: {self._get_date_string()}\n\n"
        stats_text += "Resources:\n"
        stats_text += f"  🍖 Food: {resources['food']}\n"
        stats_text += f"  🎯 Ammo: {resources['ammo']}\n"
        stats_text += f"  💊 Medicine: {resources['medicine']}\n"
        stats_text += f"  💰 Gold: {resources['gold']}\n"
        stats_text += f"  🐂 Oxen: {resources['oxen']}\n"

        return {
            "type": "stats",
            "message": stats_text,
            "state": self._get_player_summary(),
            "choices": self._get_choices(),
        }

    def _get_date_string(self) -> str:
        state = self.game_state
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        month_name = months[state["month"] - 1] if 1 <= state["month"] <= 12 else "Unknown"
        return f"{month_name} {state['day']}, {state['year']}"

    def _process_custom_action(self, action: str) -> dict:
        action_lower = action.lower()

        # Check for travel
        if "travel" in action_lower or "go" in action_lower:
            return self.travel()

        # Check for rest
        if "rest" in action_lower or "sleep" in action_lower:
            return self.rest()

        # Check for hunt
        if "hunt" in action_lower:
            return self.hunt()

        # Check for trade
        if "trade" in action_lower or "buy" in action_lower:
            if "buy" in action_lower:
                item = action_lower.replace("buy ", "").strip()
                return self.buy_item(item)
            return self.trade()

        # Check for stats
        if "stats" in action_lower or "status" in action_lower:
            return self._show_stats()

        # Default response
        responses = [
            f"You attempt to {action}, but the wilderness offers no immediate response.",
            f"You try to {action}. Perhaps later, this will prove useful.",
            f"You {action}. The trail continues ahead, unforgiving and vast.",
        ]
        response = random.choice(responses)

        return {
            "type": "custom",
            "message": response,
            "state": self._get_player_summary(),
            "choices": self._get_choices(),
        }

    def _get_player_summary(self) -> dict:
        if not self.game_state:
            return {}
        state = self.game_state
        resources = state["resources"]
        player = state["player"]

        return {
            "name": player["name"],
            "profession": player["profession"],
            "health": player["health"],
            "max_health": player["max_health"],
            "food": resources["food"],
            "ammo": resources["ammo"],
            "medicine": resources["medicine"],
            "gold": resources["gold"],
            "oxen": resources["oxen"],
            "mile": state["mile"],
            "total_miles": state["total_miles"],
            "location": state["location"],
            "day": state["day"],
            "month": state["month"],
            "weather": state["weather"],
        }

    def _save(self):
        """Save game state to file."""
        if self.game_state:
            with open(self.save_file, "w") as f:
                json.dump(self.game_state, f, indent=2)
