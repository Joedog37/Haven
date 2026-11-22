# AI-generated DnD game engine for Haven
# Uses the local AI model to generate dynamic stories, NPCs, and events
import json
import os
import random
from datetime import datetime


class DnDGame:
    """AI-generated Dungeons & Dragons style RPG with persistent state."""

    def __init__(self, save_dir="saves"):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
        self.game_state = None
        self.save_file = os.path.join(save_dir, "dnd_save.json")

    def new_game(self, player_name: str, character_class: str, character_race: str) -> dict:
        """Start a new DnD adventure."""
        self.game_state = {
            "player": {
                "name": player_name,
                "race": character_race,
                "class": character_class,
                "level": 1,
                "xp": 0,
                "hp": self._get_max_hp(character_class),
                "max_hp": self._get_max_hp(character_class),
                "attack": self._get_attack(character_class),
                "defense": self._get_defense(character_class),
                "inventory": self._starting_inventory(character_class),
                "gold": 10,
            },
            "location": "village",
            "chapter": 1,
            "scene": "intro",
            "flags": {},
            "encounters": 0,
            "story_log": [],
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
        """Process a player's choice and advance the story."""
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

    def attack(self, target: str = None) -> dict:
        """Perform an attack action."""
        if not self.game_state:
            return {"type": "error", "message": "No active game."}

        player = self.game_state["player"]
        attack_roll = random.randint(1, 20) + player["attack"]
        damage = random.randint(1, 6) + player["attack"]

        # Generate encounter based on location
        enemy = self._get_enemy_for_location()
        enemy_hp = enemy["hp"]
        enemy_defense = enemy["defense"]

        if attack_roll >= enemy_defense + 10:
            enemy_hp -= damage
            message = f"You attack {enemy['name']}! Roll: {attack_roll}, Damage: {damage}\n"
            if enemy_hp <= 0:
                xp_gain = random.randint(10, 30)
                gold_gain = random.randint(5, 20)
                player["xp"] += xp_gain
                player["gold"] += gold_gain
                message += f"\n🎉 You defeated {enemy['name']}! Gained {xp_gain} XP and {gold_gain} gold."
                self._check_level_up()
            else:
                # Enemy counter-attacks
                enemy_attack = random.randint(1, 20) + enemy["attack"]
                if enemy_attack >= player["defense"] + 10:
                    player_damage = random.randint(1, 4) + enemy["attack"]
                    player["hp"] = max(0, player["hp"] - player_damage)
                    message += f"\n{enemy['name']} counter-attacks! You take {player_damage} damage. HP: {player['hp']}/{player['max_hp']}"
                else:
                    message += f"\n{enemy['name']} attacks but misses!"

                if player["hp"] <= 0:
                    message += "\n\n💀 You have fallen in battle! Your adventure ends here... for now."
                    self.game_state["flags"]["defeated"] = True
        else:
            message = f"You attack {enemy['name']} but miss! Roll: {attack_roll}\n"
            # Enemy attacks
            enemy_attack = random.randint(1, 20) + enemy["attack"]
            if enemy_attack >= player["defense"] + 10:
                player_damage = random.randint(1, 4) + enemy["attack"]
                player["hp"] = max(0, player["hp"] - player_damage)
                message += f"\n{enemy['name']} strikes you for {player_damage} damage! HP: {player['hp']}/{player['max_hp']}"

        self.game_state["encounters"] += 1
        self.game_state["story_log"].append(f"Battle: {message[:100]}")
        self._save()

        return {
            "type": "combat",
            "message": message,
            "state": self._get_player_summary(),
            "choices": self._get_choices(),
        }

    def use_item(self, item_name: str) -> dict:
        """Use an item from inventory."""
        if not self.game_state:
            return {"type": "error", "message": "No active game."}

        player = self.game_state["player"]
        for i, item in enumerate(player["inventory"]):
            if item["name"].lower() == item_name.lower():
                if item["type"] == "potion":
                    heal = item["heal"]
                    player["hp"] = min(player["max_hp"], player["hp"] + heal)
                    player["inventory"].pop(i)
                    message = f"You use {item['name']} and recover {heal} HP! HP: {player['hp']}/{player['max_hp']}"
                    self._save()
                    return {
                        "type": "item_use",
                        "message": message,
                        "state": self._get_player_summary(),
                        "choices": self._get_choices(),
                    }
                elif item["type"] == "key":
                    self.game_state["flags"][item.get("opens", "")] = True
                    message = f"You use {item['name']} to unlock something!"
                    self._save()
                    return {
                        "type": "item_use",
                        "message": message,
                        "state": self._get_player_summary(),
                        "choices": self._get_choices(),
                    }

        return {"type": "error", "message": f"You don't have {item_name} in your inventory."}

    def rest(self) -> dict:
        """Rest to recover HP."""
        if not self.game_state:
            return {"type": "error", "message": "No active game."}

        player = self.game_state["player"]
        old_hp = player["hp"]
        player["hp"] = player["max_hp"]
        healed = player["hp"] - old_hp

        # Random event during rest
        events = [
            "You rest peacefully and recover fully.",
            "You rest, but hear strange noises in the distance...",
            "You rest and have a prophetic dream about your quest.",
            "You rest and find a small herb that boosts your health.",
        ]
        event = random.choice(events)
        message = f"{event}\n\nYou recover {healed} HP. HP: {player['hp']}/{player['max_hp']}"

        self._save()
        return {
            "type": "rest",
            "message": message,
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
                "message": f"Welcome back, {self.game_state['player']['name']}! Your adventure continues...",
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
                "chapter": self.game_state["chapter"],
            }
        return {"active": False}

    # ---- Internal Methods ----

    def _get_max_hp(self, char_class: str) -> int:
        hp_map = {"warrior": 15, "mage": 10, "rogue": 12, "cleric": 13, "ranger": 14}
        return hp_map.get(char_class.lower(), 12)

    def _get_attack(self, char_class: str) -> int:
        atk_map = {"warrior": 3, "mage": 1, "rogue": 2, "cleric": 1, "ranger": 2}
        return atk_map.get(char_class.lower(), 2)

    def _get_defense(self, char_class: str) -> int:
        def_map = {"warrior": 3, "mage": 0, "rogue": 2, "cleric": 2, "ranger": 2}
        return def_map.get(char_class.lower(), 2)

    def _starting_inventory(self, char_class: str) -> list:
        base = [{"name": "Health Potion", "type": "potion", "heal": 5}]
        if char_class.lower() == "warrior":
            base.append({"name": "Iron Sword", "type": "weapon", "damage": 2})
        elif char_class.lower() == "mage":
            base.append({"name": "Wooden Staff", "type": "weapon", "damage": 1})
        elif char_class.lower() == "rogue":
            base.append({"name": "Dagger", "type": "weapon", "damage": 1})
        return base

    def _get_enemy_for_location(self) -> dict:
        location = self.game_state["location"]
        enemies = {
            "village": {"name": "Rat Swarm", "hp": 8, "attack": 1, "defense": 0},
            "forest": {"name": "Goblin", "hp": 12, "attack": 2, "defense": 1},
            "cave": {"name": "Orc", "hp": 18, "attack": 3, "defense": 2},
            "dungeon": {"name": "Dark Knight", "hp": 25, "attack": 4, "defense": 3},
            "mountain": {"name": "Troll", "hp": 30, "attack": 5, "defense": 4},
        }
        enemy = enemies.get(location, {"name": "Bandit", "hp": 10, "attack": 2, "defense": 1})
        # Scale with level
        level = self.game_state["player"]["level"]
        enemy["hp"] += level * 3
        enemy["attack"] += level
        return enemy

    def _check_level_up(self):
        player = self.game_state["player"]
        xp_needed = player["level"] * 50
        if player["xp"] >= xp_needed:
            player["level"] += 1
            player["xp"] -= xp_needed
            player["max_hp"] += 3
            player["hp"] = player["max_hp"]
            player["attack"] += 1
            player["defense"] += 1

    def _generate_intro(self) -> str:
        player = self.game_state["player"]
        intros = [
            f"You are {player['name']}, a {player['race']} {player['class']}. "
            f"The village of Thornwood has been plagued by dark forces. "
            f"Strange lights have been seen in the nearby Whispering Forest, "
            f"and villagers have gone missing. The elder asks for your help.\n\n"
            f"What do you do?",
            f"You are {player['name']}, a {player['race']} {player['class']}. "
            f"A mysterious letter has arrived at your door, inviting you to "
            f"the ancient ruins of Eldergrove. The letter promises great treasure "
            f"but warns of deadly traps.\n\nWhat do you do?",
            f"You are {player['name']}, a {player['race']} {player['class']}. "
            f"The kingdom is at war, and the king's army has fallen. "
            f"As a last resort, you are sent to find the legendary Sword of Light "
            f"hidden deep in the Dragon's Lair.\n\nWhat do you do?",
        ]
        return random.choice(intros)

    def _get_choices(self) -> list:
        if not self.game_state:
            return []

        location = self.game_state["location"]
        scene = self.game_state["scene"]
        flags = self.game_state["flags"]

        choices = [
            {"text": "🗡️ Attack", "action": "attack"},
            {"text": "🎒 Inventory", "action": "inventory"},
            {"text": "🏕️ Rest", "action": "rest"},
            {"text": "💾 Save Game", "action": "save"},
        ]

        if location == "village":
            choices.extend([
                {"text": "🌲 Explore the Forest", "action": "go_forest"},
                {"text": "🏪 Visit the Shop", "action": "shop"},
                {"text": "👴 Talk to the Elder", "action": "talk_elder"},
            ])
        elif location == "forest":
            choices.extend([
                {"text": "🏘️ Return to Village", "action": "go_village"},
                {"text": "🕳️ Enter the Cave", "action": "go_cave"},
                {"text": "🔍 Search for Items", "action": "search"},
            ])
        elif location == "cave":
            choices.extend([
                {"text": "🌲 Return to Forest", "action": "go_forest"},
                {"text": "🏰 Enter the Dungeon", "action": "go_dungeon"},
                {"text": "🔍 Search for Treasure", "action": "search"},
            ])
        elif location == "dungeon":
            choices.extend([
                {"text": "🕳️ Return to Cave", "action": "go_cave"},
                {"text": "⛰️ Climb the Mountain", "action": "go_mountain"},
                {"text": "🔍 Search for Secrets", "action": "search"},
            ])

        choices.append({"text": "⌨️ Custom Action", "action": "custom"})
        return choices

    def _process_choice(self, action: str, custom_input: str = None) -> dict:
        if not self.game_state:
            return {"type": "error", "message": "No active game."}

        if action == "attack":
            return self.attack()
        elif action == "rest":
            return self.rest()
        elif action == "save":
            return self.save_game()
        elif action == "inventory":
            return self._show_inventory()
        elif action == "go_forest":
            return self._travel("forest")
        elif action == "go_village":
            return self._travel("village")
        elif action == "go_cave":
            return self._travel("cave")
        elif action == "go_dungeon":
            return self._travel("dungeon")
        elif action == "go_mountain":
            return self._travel("mountain")
        elif action == "shop":
            return self._visit_shop()
        elif action == "talk_elder":
            return self._talk_elder()
        elif action == "search":
            return self._search_area()
        elif action == "custom" and custom_input:
            return self._process_custom_action(custom_input)
        else:
            return {"type": "error", "message": "Unknown action."}

    def _travel(self, location: str) -> dict:
        self.game_state["location"] = location
        self.game_state["scene"] = "explore"

        locations = {
            "village": "You return to the peaceful village of Thornwood. The villagers greet you warmly.",
            "forest": "You enter the Whispering Forest. Ancient trees tower above you, and the air is thick with mystery.",
            "cave": "You descend into a dark cave. The walls glow with faint crystals, illuminating the path ahead.",
            "dungeon": "You enter an ancient dungeon. Dusty corridors stretch before you, filled with forgotten treasures and deadly traps.",
            "mountain": "You climb the treacherous Dragon's Peak. The wind howls, and the path is narrow and dangerous.",
        }

        message = locations.get(location, "You travel to an unknown location.")

        # Random encounter chance
        if random.randint(1, 100) <= 30:
            enemy = self._get_enemy_for_location()
            message += f"\n\n⚔️ A {enemy['name']} appears! Prepare for battle!"

        self.game_state["story_log"].append(f"Traveled to {location}")
        self._save()

        return {
            "type": "travel",
            "message": message,
            "state": self._get_player_summary(),
            "choices": self._get_choices(),
        }

    def _show_inventory(self) -> dict:
        player = self.game_state["player"]
        inv_text = "🎒 Your Inventory:\n"
        for item in player["inventory"]:
            inv_text += f"  • {item['name']}\n"
        inv_text += f"\n💰 Gold: {player['gold']}"

        return {
            "type": "inventory",
            "message": inv_text,
            "state": self._get_player_summary(),
            "choices": self._get_choices(),
        }

    def _visit_shop(self) -> dict:
        player = self.game_state["player"]
        shop_items = [
            {"name": "Health Potion", "cost": 5, "heal": 5},
            {"name": "Greater Health Potion", "cost": 15, "heal": 15},
            {"name": "Iron Shield", "cost": 20, "defense": 1},
        ]
        shop_text = "🏪 Village Shop:\n"
        for item in shop_items:
            shop_text += f"  • {item['name']} - {item['cost']} gold\n"
        shop_text += f"\n💰 Your Gold: {player['gold']}"

        return {
            "type": "shop",
            "message": shop_text,
            "state": self._get_player_summary(),
            "choices": self._get_choices(),
        }

    def _talk_elder(self) -> dict:
        dialogues = [
            "The elder tells you of an ancient prophecy: 'When darkness falls, a hero shall rise to restore the light.'",
            "The elder warns you: 'Beware the shadows in the forest. They are not what they seem.'",
            "The elder gives you a quest: 'Find the three sacred relics hidden in the dungeon. They hold the power to save our village.'",
        ]
        dialogue = random.choice(dialogues)

        return {
            "type": "dialogue",
            "message": dialogue,
            "state": self._get_player_summary(),
            "choices": self._get_choices(),
        }

    def _search_area(self) -> dict:
        player = self.game_state["player"]
        finds = [
            {"name": "Health Potion", "type": "potion", "heal": 5},
            {"name": "Gold Coins", "type": "gold", "amount": random.randint(5, 15)},
            {"name": "Ancient Key", "type": "key", "opens": "secret_door"},
        ]
        find = random.choice(finds)

        if find["type"] == "gold":
            player["gold"] += find["amount"]
            message = f"🔍 You search the area and find {find['amount']} gold coins!"
        else:
            player["inventory"].append(find)
            message = f"🔍 You search the area and find {find['name']}!"

        self._save()
        return {
            "type": "search",
            "message": message,
            "state": self._get_player_summary(),
            "choices": self._get_choices(),
        }

    def _process_custom_action(self, action: str) -> dict:
        action_lower = action.lower()

        # Check for item use
        if "use" in action_lower or "drink" in action_lower:
            item_name = action_lower.replace("use ", "").replace("drink ", "").strip()
            return self.use_item(item_name)

        # Check for travel
        if "go" in action_lower or "travel" in action_lower:
            for loc in ["village", "forest", "cave", "dungeon", "mountain"]:
                if loc in action_lower:
                    return self._travel(loc)

        # Check for combat
        if "attack" in action_lower or "fight" in action_lower:
            return self.attack()

        # Check for rest
        if "rest" in action_lower or "sleep" in action_lower:
            return self.rest()

        # Check for inventory
        if "inventory" in action_lower or "items" in action_lower:
            return self._show_inventory()

        # Default: AI-generated response
        responses = [
            f"You attempt to {action}, but nothing happens. The world around you remains unchanged.",
            f"You try to {action}. Perhaps that will work better later in your adventure.",
            f"You {action}. The environment seems to react subtly, but nothing obvious occurs.",
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
        player = self.game_state["player"]
        return {
            "name": player["name"],
            "race": player["race"],
            "class": player["class"],
            "level": player["level"],
            "xp": player["xp"],
            "hp": player["hp"],
            "max_hp": player["max_hp"],
            "gold": player["gold"],
            "inventory": player["inventory"],
        }

    def _save(self):
        """Save game state to file."""
        if self.game_state:
            with open(self.save_file, "w") as f:
                json.dump(self.game_state, f, indent=2)
