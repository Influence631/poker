"""Pygame GUI version of poker game."""
import pygame
import sys
from typing import List, Optional, Tuple, Dict
from player import Player, AIBot
from poker_game import PokerGame
from poker_cards import Card, Rank, Suit
from hand_evaluator import HandEvaluator
import json
import os
import time

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
FPS = 60

# Colors
GREEN_FELT = (53, 101, 77)
DARK_GREEN = (35, 65, 50)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GOLD = (255, 215, 0)
RED = (220, 20, 60)
BLUE = (70, 130, 180)
GRAY = (128, 128, 128)
LIGHT_GRAY = (192, 192, 192)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER = (100, 149, 237)

# Fonts
FONT_LARGE = pygame.font.Font(None, 48)
FONT_MEDIUM = pygame.font.Font(None, 36)
FONT_SMALL = pygame.font.Font(None, 24)
FONT_TINY = pygame.font.Font(None, 20)

# Card images cache
CARD_IMAGES: Dict[str, pygame.Surface] = {}
CARD_BACK_IMAGE: Optional[pygame.Surface] = None

def load_card_images():
    """Load all card images from PNG folder."""
    global CARD_IMAGES, CARD_BACK_IMAGE

    cards_path = "Playing Cards/Playing Cards/PNG-cards-1.3"

    if not os.path.exists(cards_path):
        print(f"Warning: Card images not found at {cards_path}")
        return

    # Map rank/suit to filename format
    rank_map = {
        "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7", "8": "8",
        "9": "9", "10": "10", "J": "jack", "Q": "queen", "K": "king", "A": "ace"
    }

    suit_map = {
        "♥": "hearts", "♦": "diamonds", "♣": "clubs", "♠": "spades"
    }

    # Load each card
    for rank in Rank:
        for suit in Suit:
            rank_str = rank_map.get(rank.display, rank.display.lower())
            suit_str = suit_map.get(suit.value, "")

            # Try loading the primary version first
            filename = f"{rank_str}_of_{suit_str}.png"
            filepath = os.path.join(cards_path, filename)

            # For face cards (J, Q, K), try the "2" version first as it's often cleaner
            if rank.display in ["J", "Q", "K"]:
                filename2 = f"{rank_str}_of_{suit_str}2.png"
                filepath2 = os.path.join(cards_path, filename2)
                if os.path.exists(filepath2):
                    filepath = filepath2
                    filename = filename2

            if os.path.exists(filepath):
                try:
                    img = pygame.image.load(filepath)
                    # Store by card key
                    key = f"{rank.display}{suit.value}"
                    CARD_IMAGES[key] = img
                    print(f"Loaded {filename} as {key}")
                except Exception as e:
                    print(f"Error loading {filename}: {e}")

    print(f"Loaded {len(CARD_IMAGES)} card images")


class Button:
    """A clickable button."""

    def __init__(self, x: int, y: int, width: int, height: int, text: str,
                 color: Tuple[int, int, int] = BUTTON_COLOR,
                 hover_color: Tuple[int, int, int] = BUTTON_HOVER):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.enabled = True

    def draw(self, screen: pygame.Surface):
        """Draw the button."""
        if not self.enabled:
            color = GRAY
        elif self.is_hovered:
            color = self.hover_color
        else:
            color = self.color

        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=8)

        text_surface = FONT_MEDIUM.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def update(self, mouse_pos: Tuple[int, int]):
        """Update hover state."""
        self.is_hovered = self.rect.collidepoint(mouse_pos) and self.enabled

    def is_clicked(self, mouse_pos: Tuple[int, int]) -> bool:
        """Check if button is clicked."""
        return self.is_hovered and self.enabled


class PokerGUI:
    """Main GUI class for poker game."""

    SAVE_FILE = "player_data.json"

    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Texas Hold'em Poker")
        self.clock = pygame.time.Clock()

        # Load card images
        load_card_images()

        # Game state
        self.player = self.load_player()
        self.game: Optional[PokerGame] = None
        self.state = "menu"
        self.message = ""
        self.message_timer = 0

        # UI elements
        self.buttons: List[Button] = []
        self.selected_difficulty = "medium"

        # Game flow
        self.current_round = "pre-flop"
        self.waiting_for_player = False
        self.bot_action_delay = 0
        self.winners = []
        self.action_history = []
        self.players_acted = set()  # Track who has acted in current round
        self.current_player_index = 0  # Track whose turn it is
        self.blinds_posted = False  # Track if blinds have been posted this hand
        self.current_acting_player = None  # Who is currently making a decision

        # Debug logging
        self.debug_log = []
        self.hand_number = 0

        # Universal turn timer (for all players)
        self.turn_timer = 0
        self.turn_time_limit = 600  # 10 seconds at 60 FPS
        self.bot_min_think_time = 60  # Minimum 1 second for bots

        # Bet/raise input
        self.showing_bet_dialog = False
        self.bet_input = ""
        self.bet_action = ""  # "bet" or "raise"

    def load_player(self) -> Player:
        """Load or create player."""
        if os.path.exists(self.SAVE_FILE):
            try:
                with open(self.SAVE_FILE, 'r') as f:
                    data = json.load(f)
                    return Player(data.get("name", "Player"), data.get("chips", 1000))
            except:
                pass
        return Player("Player", 1000)

    def save_player(self):
        """Save player data."""
        data = {
            "name": self.player.name,
            "chips": self.player.chips
        }
        with open(self.SAVE_FILE, 'w') as f:
            json.dump(data, f)

    def show_message(self, message: str, duration: int = 120):
        """Show a temporary message."""
        self.message = message
        self.message_timer = duration

    def run(self):
        """Main game loop."""
        running = True
        frame_count = 0
        while running:
            mouse_pos = pygame.mouse.get_pos()

            # Debug: print every second
            if frame_count % 60 == 0:
                print(f"Frame {frame_count}, state={self.state}")

            # Update button hover states
            for button in self.buttons:
                button.update(mouse_pos)

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.save_player()
                    running = False

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_mouse_click(mouse_pos)

                if event.type == pygame.KEYDOWN:
                    self.handle_keyboard(event)

            # Update game logic
            self.update()

            # Draw
            self.screen.fill(GREEN_FELT)

            if self.state == "menu":
                self.draw_menu()
            elif self.state == "difficulty_select":
                self.draw_difficulty_select()
            elif self.state == "playing":
                self.draw_game()
                if self.showing_bet_dialog:
                    self.draw_bet_dialog()
            elif self.state == "showing_results":
                self.draw_game()
                self.draw_results()
            elif self.state == "game_over":
                self.draw_game_over()

            # Draw message overlay
            if self.message_timer > 0:
                self.draw_message_overlay()

            pygame.display.flip()
            self.clock.tick(FPS)
            frame_count += 1

        pygame.quit()
        sys.exit()

    def update(self):
        """Update game state."""
        if self.message_timer > 0:
            self.message_timer -= 1

        if not hasattr(self, '_update_logged') and self.state == "playing":
            self.log_debug(f"Update() called with state={self.state}")
            self._update_logged = True

        if self.state == "playing":
            # Decrement delays FIRST (before any other logic)
            if self.bot_action_delay > 0:
                self.bot_action_delay -= 1

            # Universal turn timer (for current acting player)
            if self.current_acting_player and not self.showing_bet_dialog:
                self.turn_timer += 1

                # Player timeout
                if self.current_acting_player == self.player and self.turn_timer >= self.turn_time_limit:
                    self.log_debug(f"{self.current_round.upper()}: {self.player.name} TIMEOUT - AUTO FOLD")
                    self.player.fold()
                    self.action_history.append(f"{self.player.name} folds (timeout)")
                    self.show_message(f"{self.player.name} folds (timeout)", 120)
                    self.players_acted.add(self.player)
                    self.waiting_for_player = False
                    self.current_acting_player = None
                    self.turn_timer = 0
                    self.bot_action_delay = 60  # Brief delay before next action

                # Bot minimum think time + decision
                elif self.current_acting_player != self.player:
                    if self.turn_timer >= self.bot_min_think_time:
                        # Bot has thought long enough, make decision
                        if self.current_acting_player:  # Double check still exists
                            self.process_bot_action(self.current_acting_player)
                            self.turn_timer = 0

            # Process next action when no one is currently acting
            elif not self.waiting_for_player and not self.showing_bet_dialog and self.bot_action_delay == 0:
                # Debug: check why this might not be called
                if not hasattr(self, '_first_action_logged'):
                    self.log_debug(f"Calling process_next_action - wait:{self.waiting_for_player}, dialog:{self.showing_bet_dialog}, delay:{self.bot_action_delay}")
                    self._first_action_logged = True
                self.process_next_action()

    def handle_mouse_click(self, pos: Tuple[int, int]):
        """Handle mouse clicks."""
        for button in self.buttons:
            if button.is_clicked(pos):
                self.handle_button_click(button.text)
                break

    def handle_keyboard(self, event: pygame.event.Event):
        """Handle keyboard input."""
        if self.showing_bet_dialog:
            if event.key == pygame.K_BACKSPACE:
                self.bet_input = self.bet_input[:-1]
            elif event.key == pygame.K_RETURN:
                self.submit_bet()
            elif event.key == pygame.K_ESCAPE:
                self.showing_bet_dialog = False
                self.bet_input = ""
            elif event.unicode.isdigit() and len(self.bet_input) < 6:
                self.bet_input += event.unicode

    def handle_button_click(self, button_text: str):
        """Handle button clicks."""
        if self.state == "menu":
            if button_text == "Play Poker":
                if self.player.chips < 20:
                    self.show_message("Not enough chips! Add more first.")
                else:
                    self.state = "difficulty_select"
            elif button_text == "Add Chips (+$500)":
                self.player.chips += 500
                self.save_player()
                self.show_message(f"Added $500! Total: ${self.player.chips}")
            elif button_text == "Quit":
                self.save_player()
                pygame.quit()
                sys.exit()

        elif self.state == "difficulty_select":
            if button_text in ["Easy", "Medium", "Hard"]:
                self.selected_difficulty = button_text.lower()
                self.start_new_game()
            elif button_text == "Back":
                self.state = "menu"

        elif self.state == "playing":
            if self.waiting_for_player:
                self.handle_player_action(button_text)

        elif self.state == "showing_results":
            if button_text == "Continue":
                self.next_hand()
            elif button_text == "Main Menu":
                self.state = "menu"
                self.game = None

        elif self.state == "game_over":
            if button_text == "Main Menu":
                self.state = "menu"
                self.game = None
            elif button_text == "Quit":
                self.save_player()
                pygame.quit()
                sys.exit()

    def handle_player_action(self, action: str):
        """Handle player's betting action."""
        call_amount = self.game.current_bet - self.player.current_bet
        player_pos = 0  # Player is always at position 0

        # Reset timer
        self.turn_timer = 0

        if action == "Check":
            self.action_history.append(f"{self.player.name} checks")
            self.show_message(f"{self.player.name} checks", 90)
            self.log_debug(f"{self.current_round.upper()}: {self.player.name} (pos {player_pos}) CHECKS (pot: ${self.game.pot})")
            self.players_acted.add(self.player)
            self.waiting_for_player = False
            self.current_acting_player = None  # Clear current actor
            self.bot_action_delay = 60  # Brief delay before next action

        elif action == "Fold":
            self.player.fold()
            self.action_history.append(f"{self.player.name} folds")
            self.show_message(f"{self.player.name} folds", 90)
            self.log_debug(f"{self.current_round.upper()}: {self.player.name} (pos {player_pos}) FOLDS (pot: ${self.game.pot})")
            self.players_acted.add(self.player)
            self.waiting_for_player = False
            self.current_acting_player = None  # Clear current actor
            self.bot_action_delay = 60  # Brief delay before next action

        elif action.startswith("Call"):
            actual_bet = self.player.bet(call_amount)
            self.game.pot += actual_bet
            self.action_history.append(f"{self.player.name} calls ${actual_bet}")
            self.show_message(f"{self.player.name} calls ${actual_bet}", 90)
            self.log_debug(f"{self.current_round.upper()}: {self.player.name} (pos {player_pos}) CALLS ${actual_bet} (pot: ${self.game.pot}, chips: {self.player.chips})")
            self.players_acted.add(self.player)
            self.waiting_for_player = False
            self.current_acting_player = None  # Clear current actor
            self.bot_action_delay = 60  # Brief delay before next action

        elif action == "Bet" or action == "Raise":
            self.bet_action = action.lower()
            self.showing_bet_dialog = True
            self.bet_input = ""

    def submit_bet(self):
        """Submit bet/raise amount."""
        if not self.bet_input:
            return

        try:
            amount = int(self.bet_input)
            call_amount = self.game.current_bet - self.player.current_bet

            if self.bet_action == "bet":
                min_amount = self.game.min_raise
                if amount < min_amount or amount > self.player.chips:
                    self.show_message(f"Invalid bet amount! ({min_amount}-{self.player.chips})", 90)
                    return

                actual_bet = self.player.bet(amount)
                self.game.pot += actual_bet
                self.game.current_bet = self.player.current_bet
                self.game.min_raise = amount
                self.action_history.append(f"{self.player.name} bets ${actual_bet}")
                self.show_message(f"{self.player.name} bets ${actual_bet}", 60)
                # Reset players_acted when someone raises
                self.players_acted = {self.player}

            elif self.bet_action == "raise":
                min_raise = self.game.min_raise
                if amount < min_raise or call_amount + amount > self.player.chips:
                    self.show_message(f"Invalid raise! Min raise: ${min_raise}", 90)
                    return

                total_bet = call_amount + amount
                actual_bet = self.player.bet(total_bet)
                self.game.pot += actual_bet
                self.game.current_bet = self.player.current_bet
                self.game.min_raise = amount
                self.action_history.append(f"{self.player.name} raises ${amount}")
                self.show_message(f"{self.player.name} raises ${amount}", 60)
                # Reset players_acted when someone raises
                self.players_acted = {self.player}

            self.showing_bet_dialog = False
            self.bet_input = ""
            self.waiting_for_player = False
            self.current_acting_player = None  # Clear current actor
            self.bot_action_delay = 60  # Brief delay before next action

        except ValueError:
            self.show_message("Invalid amount!", 90)

    def process_next_action(self):
        """Process next bot action or advance game."""
        self.log_debug(f"process_next_action called - round: {self.current_round}, blinds_posted: {self.blinds_posted}")

        # Check if only one player remains
        if len([p for p in self.game.all_players if not p.folded]) <= 1:
            self.end_hand()
            return

        # Post blinds as first actions if not done yet
        if self.current_round == "pre-flop" and not self.blinds_posted:
            self.log_debug("Posting blinds...")
            self.post_blinds_animated()
            return

        # Determine betting order (proper poker rules)
        num_players = len(self.game.all_players)

        # Pre-flop: Start after BB (UTG position)
        # Post-flop: Start after dealer (SB position)
        if self.current_round == "pre-flop":
            # UTG is after BB: dealer + 3 positions
            start_pos = (self.game.dealer_position + 3) % num_players
        else:
            # Post-flop starts after dealer (SB position)
            start_pos = (self.game.dealer_position + 1) % num_players

        # Find next player to act
        checked_count = 0
        while checked_count < num_players:
            player_index = (start_pos + checked_count) % num_players
            player = self.game.all_players[player_index]

            # Check if this player needs to act
            if not player.folded and not player.all_in and player not in self.players_acted:
                # Player needs to act if:
                # 1. They haven't matched current bet, OR
                # 2. Current bet is 0 and they haven't acted yet (everyone gets to check/bet)
                needs_to_act = (player.current_bet < self.game.current_bet) or \
                               (self.game.current_bet == 0 and player not in self.players_acted)

                if needs_to_act:
                    # This player needs to act - set them as current and return
                    # The update() loop will handle calling process_bot_action with timer
                    self.current_acting_player = player
                    self.turn_timer = 0  # Reset timer for new player

                    if player == self.player:
                        self.waiting_for_player = True

                    return

            checked_count += 1

        # All players have acted - advance round
        self.current_acting_player = None
        self.advance_round()

    def post_blinds_animated(self):
        """Post blinds as animated actions."""
        num_players = len(self.game.all_players)
        sb_pos = (self.game.dealer_position + 1) % num_players
        bb_pos = (self.game.dealer_position + 2) % num_players

        self.log_debug(f"--- HAND #{self.hand_number} ---")
        self.log_debug(f"Dealer: {self.game.all_players[self.game.dealer_position].name} (pos {self.game.dealer_position})")

        # Post small blind
        sb_player = self.game.all_players[sb_pos]
        sb_amount = self.game.post_blind(sb_pos, self.game.small_blind)
        self.action_history.append(f"{sb_player.name} posts SB ${sb_amount}")
        self.show_message(f"{sb_player.name} posts SB ${sb_amount}", 90)
        self.log_debug(f"SB: {sb_player.name} posts ${sb_amount} (pos {sb_pos}, chips: {sb_player.chips})")

        # Post big blind
        bb_player = self.game.all_players[bb_pos]
        bb_amount = self.game.post_blind(bb_pos, self.game.big_blind)
        self.action_history.append(f"{bb_player.name} posts BB ${bb_amount}")
        self.log_debug(f"BB: {bb_player.name} posts ${bb_amount} (pos {bb_pos}, chips: {bb_player.chips})")
        self.log_debug(f"Pot after blinds: ${self.game.pot}, Current bet: ${self.game.current_bet}")

        self.blinds_posted = True
        self.bot_action_delay = 120  # 2 second pause after blinds

    def process_bot_action(self, bot: Player):
        """Process one bot action."""
        bot_pos = self.game.all_players.index(bot)

        action, amount = bot.make_decision(
            self.game.pot,
            self.game.current_bet,
            self.game.community_cards,
            self.game.min_raise
        )

        call_amount = self.game.current_bet - bot.current_bet

        if action == "fold":
            bot.fold()
            self.action_history.append(f"{bot.name} folds")
            self.show_message(f"{bot.name} folds", 120)
            self.log_debug(f"{self.current_round.upper()}: {bot.name} (pos {bot_pos}) FOLDS (pot: ${self.game.pot})")
            self.players_acted.add(bot)
        elif action == "call":
            actual_bet = bot.bet(call_amount)
            self.game.pot += actual_bet
            self.action_history.append(f"{bot.name} calls ${actual_bet}")
            self.show_message(f"{bot.name} calls ${actual_bet}", 120)
            self.log_debug(f"{self.current_round.upper()}: {bot.name} (pos {bot_pos}) CALLS ${actual_bet} (pot: ${self.game.pot}, chips: {bot.chips})")
            self.players_acted.add(bot)
        elif action == "check":
            self.action_history.append(f"{bot.name} checks")
            self.show_message(f"{bot.name} checks", 120)
            self.log_debug(f"{self.current_round.upper()}: {bot.name} (pos {bot_pos}) CHECKS (pot: ${self.game.pot})")
            self.players_acted.add(bot)
        elif action == "raise":
            total_bet = call_amount + amount
            actual_bet = bot.bet(total_bet)
            self.game.pot += actual_bet
            self.game.current_bet = bot.current_bet
            self.game.min_raise = amount
            self.action_history.append(f"{bot.name} raises ${amount}")
            self.show_message(f"{bot.name} raises ${amount}", 120)
            self.log_debug(f"{self.current_round.upper()}: {bot.name} (pos {bot_pos}) RAISES ${amount} (pot: ${self.game.pot}, chips: {bot.chips})")
            # Reset players_acted when someone raises
            self.players_acted = {bot}

        # Mark this bot as done acting
        self.current_acting_player = None
        self.bot_action_delay = 60  # Brief delay before next player

    def advance_round(self):
        """Advance to next betting round."""
        # Reset who has acted for new round
        self.players_acted = set()

        if self.current_round == "pre-flop":
            self.game.deal_flop()
            self.current_round = "flop"
            self.show_message("Dealing Flop", 150)
            self.bot_action_delay = 120  # 2 second pause to show cards
            return  # Allow betting on flop
        elif self.current_round == "flop":
            self.game.deal_turn()
            self.current_round = "turn"
            self.show_message("Dealing Turn", 150)
            self.bot_action_delay = 120  # 2 second pause to show cards
            return  # Allow betting on turn
        elif self.current_round == "turn":
            self.game.deal_river()
            self.current_round = "river"
            self.show_message("Dealing River", 150)
            self.bot_action_delay = 120  # 2 second pause to show cards
            return  # Allow betting on river
        elif self.current_round == "river":
            self.end_hand()
            return
        else:
            self.end_hand()
            return

    def end_hand(self):
        """End the current hand and show results."""
        self.winners = self.game.determine_winners()
        self.state = "showing_results"
        self.save_player()

    def next_hand(self):
        """Start next hand or end game."""
        if self.game.is_game_over():
            self.state = "game_over"
        else:
            self.game.move_dealer_button()
            if self.game.start_new_hand():
                self.hand_number += 1
                self.current_round = "pre-flop"
                self.waiting_for_player = False
                self.bot_action_delay = 120  # 2 second pause to show cards
                self.action_history = []
                self.blinds_posted = False
                self.players_acted = set()  # Reset who has acted
                self.current_acting_player = None  # Reset current actor
                self.turn_timer = 0  # Reset turn timer
                self.state = "playing"
                self.log_debug(f"=== HAND #{self.hand_number} STARTED ===")
                self.log_debug(f"Dealer position: {self.game.dealer_position}, Dealer: {self.game.all_players[self.game.dealer_position].name}")
                self.show_message("New hand started!", 120)
            else:
                self.state = "game_over"

    def start_new_game(self):
        """Start a new poker game."""
        self.game = PokerGame(self.player, num_bots=3, small_blind=10, bot_difficulty=self.selected_difficulty)
        self.game.start_new_hand()
        self.current_round = "pre-flop"
        self.waiting_for_player = False
        self.bot_action_delay = 0  # Start immediately
        self.action_history = []
        self.blinds_posted = False
        self.hand_number = 1
        self.debug_log = []
        self.players_acted = set()
        self.current_acting_player = None
        self.turn_timer = 0
        self.log_debug(f"=== NEW GAME STARTED ===")
        self.log_debug(f"Players: {[p.name for p in self.game.all_players]}")
        self.log_debug(f"Dealer position: {self.game.dealer_position}")
        self.state = "playing"
        self.log_debug(f"State set to: {self.state}")
        self.log_debug(f"Initial values - wait:{self.waiting_for_player}, dialog:{self.showing_bet_dialog}, delay:{self.bot_action_delay}, current_actor:{self.current_acting_player}")
        self.show_message("Game started!", 120)

    def log_debug(self, message: str):
        """Add message to debug log."""
        timestamp = len(self.debug_log)
        log_entry = f"[{timestamp:04d}] {message}"
        self.debug_log.append(log_entry)
        print(log_entry)  # Also print to console

    def export_debug_log(self):
        """Export debug log to file."""
        filename = f"poker_debug_{int(time.time())}.txt"
        with open(filename, 'w') as f:
            f.write("\n".join(self.debug_log))
        print(f"Debug log exported to {filename}")
        return filename

    def calculate_hand_strength_ai(self) -> Tuple[float, str]:
        """Calculate AI-based hand strength (0-1) and recommendation."""
        if not self.player.hand:
            return 0.0, "No hand"

        # Pre-flop evaluation
        if len(self.game.community_cards) == 0:
            card1, card2 = self.player.hand
            rank1, rank2 = card1.rank.value, card2.rank.value

            # Pair
            if rank1 == rank2:
                strength = 0.5 + (rank1 / 28.0)
                if strength > 0.8:
                    return strength, "Strong - Raise"
                elif strength > 0.6:
                    return strength, "Good - Bet/Call"
                else:
                    return strength, "Decent - Call"

            # High cards
            high = max(rank1, rank2)
            low = min(rank1, rank2)
            suited_bonus = 0.1 if card1.suit == card2.suit else 0
            connected_bonus = 0.05 if abs(rank1 - rank2) <= 2 else 0
            strength = (high / 28.0) + (low / 56.0) + suited_bonus + connected_bonus

            if strength > 0.7:
                return strength, "Strong - Raise"
            elif strength > 0.5:
                return strength, "Decent - Call"
            elif strength > 0.35:
                return strength, "Weak - Check/Fold"
            else:
                return strength, "Very Weak - Fold"

        # Post-flop evaluation
        full_hand = self.player.hand + self.game.community_cards
        hand_rank, _ = HandEvaluator.evaluate_hand(full_hand)
        strength = hand_rank / 10.0

        if strength > 0.8:
            return strength, "Very Strong - Raise"
        elif strength > 0.65:
            return strength, "Strong - Bet/Raise"
        elif strength > 0.45:
            return strength, "Decent - Call/Bet"
        elif strength > 0.3:
            return strength, "Weak - Check/Call"
        else:
            return strength, "Very Weak - Fold"

    def calculate_outs(self) -> int:
        """Calculate the number of outs to improve the hand."""
        if not self.player.hand or len(self.game.community_cards) < 3:
            return 0

        from poker_cards import Deck, Rank, Suit

        full_hand = self.player.hand + self.game.community_cards
        current_rank, current_tie = HandEvaluator.evaluate_hand(full_hand)

        # Get all known cards
        known_cards = set(full_hand)

        # Create all possible cards and filter out known ones
        all_cards = [Card(rank, suit) for suit in Suit for rank in Rank]
        unknown_cards = [c for c in all_cards if c not in known_cards]

        # Count outs - cards that improve our hand
        outs = 0
        for card in unknown_cards:
            test_hand = full_hand + [card]
            new_rank, new_tie = HandEvaluator.evaluate_hand(test_hand)
            # Check if hand improved
            if new_rank > current_rank or (new_rank == current_rank and new_tie > current_tie):
                outs += 1

        return outs

    def calculate_pot_odds_evaluation(self) -> Tuple[str, str, str]:
        """
        Calculate pot odds and odds against, return recommendation.
        Returns: (pot_odds_str, odds_against_str, recommendation)
        """
        if not self.player.hand:
            return "N/A", "N/A", "No hand"

        call_amount = self.game.current_bet - self.player.current_bet

        # Pre-flop or no bet to call
        if len(self.game.community_cards) < 3:
            return "Pre-flop", "Pre-flop", "See flop"

        if call_amount == 0:
            return "N/A", "N/A", "Check/Bet"

        # Calculate pot odds: (pot + call_amount) : call_amount
        pot_after_call = self.game.pot + call_amount
        pot_odds_ratio = pot_after_call / call_amount if call_amount > 0 else 0
        pot_odds_str = f"{pot_odds_ratio:.1f}:1"

        # Calculate outs
        outs = self.calculate_outs()

        # Calculate unknown cards
        known_cards_count = len(self.player.hand) + len(self.game.community_cards)
        unknown_cards = 52 - known_cards_count

        # Calculate odds against: (unknown - outs) : outs
        if outs > 0:
            odds_against_ratio = (unknown_cards - outs) / outs
            odds_against_str = f"{odds_against_ratio:.1f}:1"
        else:
            odds_against_str = "No outs"
            odds_against_ratio = 999  # Very high

        # Make recommendation based on pot odds vs odds against
        # If pot odds > odds against, it's a good call
        if outs == 0:
            full_hand = self.player.hand + self.game.community_cards
            hand_rank, _ = HandEvaluator.evaluate_hand(full_hand)
            if hand_rank >= 6:  # Flush or better
                recommendation = "CALL/RAISE (strong hand)"
            else:
                recommendation = "FOLD (no improvement)"
        elif pot_odds_ratio > odds_against_ratio:
            recommendation = "CALL/BET (good odds)"
        elif pot_odds_ratio > odds_against_ratio * 0.8:  # Close
            recommendation = "CALL (marginal)"
        else:
            recommendation = "FOLD (bad odds)"

        return pot_odds_str, odds_against_str, recommendation

    def calculate_hand_strength_math(self) -> Tuple[float, str]:
        """Calculate math-based hand strength using pot odds and outs."""
        if not self.player.hand:
            return 0.0, "No hand"

        if len(self.game.community_cards) == 0:
            # Pre-flop: Use simplified probability
            card1, card2 = self.player.hand
            rank1, rank2 = card1.rank.value, card2.rank.value

            if rank1 == rank2:
                # Pocket pair: ~50% to improve
                strength = 0.5 + (rank1 / 40.0)
            else:
                # High card probability
                strength = max(rank1, rank2) / 28.0

            if strength > 0.7:
                return strength, "Math: 70%+ equity"
            elif strength > 0.5:
                return strength, "Math: 50-70% equity"
            else:
                return strength, "Math: <50% equity"

        # Post-flop: Calculate actual outs and odds
        full_hand = self.player.hand + self.game.community_cards
        hand_rank, _ = HandEvaluator.evaluate_hand(full_hand)

        # Calculate actual outs
        outs = self.calculate_outs()

        # Estimate outs based on current hand if calculation returns 0
        if outs == 0:
            if hand_rank >= 8:  # Strong made hand
                outs = 0  # Already have strong hand
                equity = 0.9
            elif hand_rank >= 6:  # Medium hand
                outs = 5
            elif hand_rank >= 4:  # Weak hand with potential
                outs = 8
            else:  # Very weak
                outs = 3

        # Calculate equity from outs
        known_cards = len(self.player.hand) + len(self.game.community_cards)
        unknown_cards = 52 - known_cards

        if outs > 0:
            # Rule of 2 and 4: multiply outs by 2 for one card, 4 for two cards
            cards_to_come = 2 if len(self.game.community_cards) == 3 else 1
            multiplier = 4 if cards_to_come == 2 else 2
            equity = min(0.95, (outs * multiplier) / 100.0)
        else:
            equity = 0.9 if hand_rank >= 6 else 0.1

        equity = min(0.95, max(0.05, equity))

        if equity > 0.65:
            return equity, f"Math: ~{int(equity*100)}% ({outs} outs)"
        elif equity > 0.40:
            return equity, f"Math: ~{int(equity*100)}% ({outs} outs)"
        else:
            return equity, f"Math: ~{int(equity*100)}% ({outs} outs)"

    # ===== Drawing Methods =====

    def draw_menu(self):
        """Draw main menu."""
        title = FONT_LARGE.render("TEXAS HOLD'EM POKER", True, GOLD)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)

        info = FONT_MEDIUM.render(f"{self.player.name} - ${self.player.chips}", True, WHITE)
        info_rect = info.get_rect(center=(WINDOW_WIDTH // 2, 250))
        self.screen.blit(info, info_rect)

        self.buttons = [
            Button(WINDOW_WIDTH // 2 - 150, 350, 300, 60, "Play Poker"),
            Button(WINDOW_WIDTH // 2 - 150, 430, 300, 60, "Add Chips (+$500)"),
            Button(WINDOW_WIDTH // 2 - 150, 510, 300, 60, "Quit")
        ]

        for button in self.buttons:
            button.draw(self.screen)

    def draw_difficulty_select(self):
        """Draw difficulty selection screen."""
        title = FONT_LARGE.render("SELECT DIFFICULTY", True, GOLD)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)

        self.buttons = [
            Button(WINDOW_WIDTH // 2 - 150, 300, 300, 60, "Easy"),
            Button(WINDOW_WIDTH // 2 - 150, 380, 300, 60, "Medium"),
            Button(WINDOW_WIDTH // 2 - 150, 460, 300, 60, "Hard"),
            Button(WINDOW_WIDTH // 2 - 150, 560, 300, 60, "Back")
        ]

        for button in self.buttons:
            button.draw(self.screen)

        y = 700
        for text in ["Easy: Passive bots", "Medium: Balanced play", "Hard: Aggressive bots"]:
            label = FONT_SMALL.render(text, True, LIGHT_GRAY)
            label_rect = label.get_rect(center=(WINDOW_WIDTH // 2, y))
            self.screen.blit(label, label_rect)
            y += 30

    def draw_game(self):
        """Draw the poker game."""
        if not self.game:
            return

        # Draw table
        table_rect = pygame.Rect(200, 200, 1000, 500)
        pygame.draw.ellipse(self.screen, DARK_GREEN, table_rect)
        pygame.draw.ellipse(self.screen, GOLD, table_rect, 3)

        # Draw round indicator at top
        round_text = FONT_SMALL.render(self.current_round.upper(), True, LIGHT_GRAY)
        round_rect = round_text.get_rect(center=(WINDOW_WIDTH // 2, 60))
        self.screen.blit(round_text, round_rect)

        # Draw pot ABOVE community cards
        pot_text = FONT_MEDIUM.render(f"Pot: ${self.game.pot}", True, GOLD)
        pot_rect = pot_text.get_rect(center=(WINDOW_WIDTH // 2, 260))
        self.screen.blit(pot_text, pot_rect)

        # Draw community cards BELOW pot
        self.draw_community_cards()

        # Draw players
        self.draw_players()

        # Draw player's hand
        self.draw_player_hand()

        # Always draw timer when someone is acting
        self.draw_player_timer()

        # Draw action buttons
        if self.waiting_for_player:
            self.draw_action_buttons()
        else:
            self.buttons = []

        # Draw action history
        self.draw_action_history()

        # Draw hand strength evaluation (if player has cards and community cards exist)
        if self.player.hand and not self.player.folded:
            self.draw_hand_evaluation()

    def draw_community_cards(self):
        """Draw community cards with fancy animations."""
        if not self.game.community_cards:
            return

        card_width = 80
        card_height = 110
        spacing = 10
        total_width = len(self.game.community_cards) * (card_width + spacing) - spacing
        start_x = (WINDOW_WIDTH - total_width) // 2
        y = 300  # Moved down to avoid pot label

        for i, card in enumerate(self.game.community_cards):
            x = start_x + i * (card_width + spacing)

            # Add subtle shadow and glow effect
            shadow_surf = pygame.Surface((card_width + 10, card_height + 10))
            shadow_surf.set_alpha(80)
            shadow_surf.fill((0, 0, 0))
            self.screen.blit(shadow_surf, (x - 5, y - 5))

            self.draw_card(card, x, y, card_width, card_height)

    def draw_card(self, card: Card, x: int, y: int, width: int, height: int, face_down: bool = False):
        """Draw a playing card using loaded images."""
        # Card background with shadow
        shadow_offset = 3
        pygame.draw.rect(self.screen, (50, 50, 50),
                        (x + shadow_offset, y + shadow_offset, width, height),
                        border_radius=8)

        if face_down:
            # Draw card back
            pygame.draw.rect(self.screen, WHITE, (x, y, width, height), border_radius=8)
            pygame.draw.rect(self.screen, BLACK, (x, y, width, height), 2, border_radius=8)
            pygame.draw.rect(self.screen, BLUE, (x + 5, y + 5, width - 10, height - 10), border_radius=5)
            # Add pattern
            for i in range(3):
                for j in range(4):
                    cx = x + 15 + i * 25
                    cy = y + 15 + j * 30
                    pygame.draw.circle(self.screen, DARK_GREEN, (cx, cy), 8)
        else:
            # Try to use loaded image
            card_key = f"{card.rank.display}{card.suit.value}"

            if card_key in CARD_IMAGES:
                # Use loaded image
                img = CARD_IMAGES[card_key]
                # Scale image to fit
                scaled_img = pygame.transform.scale(img, (width, height))
                self.screen.blit(scaled_img, (x, y))
            else:
                # Fallback to programmatic rendering
                pygame.draw.rect(self.screen, WHITE, (x, y, width, height), border_radius=8)
                pygame.draw.rect(self.screen, BLACK, (x, y, width, height), 2, border_radius=8)

                suit_name = card.suit.value
                color = RED if suit_name in ['♥', '♦'] else BLACK

                suit_symbols = {
                    '♥': '♥', '♦': '♦', '♣': '♣', '♠': '♠'
                }
                suit_display = suit_symbols.get(suit_name, suit_name)

                rank_font = pygame.font.Font(None, 28)
                suit_font = pygame.font.Font(None, 32)

                rank_text = rank_font.render(card.rank.display, True, color)
                self.screen.blit(rank_text, (x + 6, y + 5))

                suit_text_small = suit_font.render(suit_display, True, color)
                self.screen.blit(suit_text_small, (x + 6, y + 25))

                center_suit_font = pygame.font.Font(None, 60)
                suit_text_large = center_suit_font.render(suit_display, True, color)
                suit_rect = suit_text_large.get_rect(center=(x + width // 2, y + height // 2))
                self.screen.blit(suit_text_large, suit_rect)

                rank_text_br = rank_font.render(card.rank.display, True, color)
                self.screen.blit(rank_text_br, (x + width - 22, y + height - 45))

                suit_text_br = suit_font.render(suit_display, True, color)
                self.screen.blit(suit_text_br, (x + width - 22, y + height - 22))

    def draw_players(self):
        """Draw all players in clockwise order."""
        if not self.game:
            return

        # Player positions in clockwise order (player is at position 0 - bottom)
        # Positions: 0=bottom (player), 1=left, 2=top, 3=right
        positions = [
            (WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT - 300),  # Position 0: Player (bottom) - shown separately
            (150, WINDOW_HEIGHT // 2 - 50),                   # Position 1: Left side
            (WINDOW_WIDTH // 2 - 100, 50),                    # Position 2: Top
            (WINDOW_WIDTH - 350, WINDOW_HEIGHT // 2 - 50)     # Position 3: Right side
        ]

        # Draw all players except the human player (index 0)
        for i, player in enumerate(self.game.all_players):
            if i > 0:  # Skip human player (index 0)
                x, y = positions[i]
                is_dealer = i == self.game.dealer_position
                self.draw_player_info(player, x, y, is_dealer)

    def draw_player_info(self, player: Player, x: int, y: int, is_dealer: bool):
        """Draw player info panel."""
        # Determine position info
        player_index = self.game.all_players.index(player)
        num_players = len(self.game.all_players)
        sb_pos = (self.game.dealer_position + 1) % num_players
        bb_pos = (self.game.dealer_position + 2) % num_players

        is_sb = player_index == sb_pos
        is_bb = player_index == bb_pos

        panel_rect = pygame.Rect(x, y, 200, 100)
        pygame.draw.rect(self.screen, DARK_GREEN, panel_rect, border_radius=8)
        pygame.draw.rect(self.screen, GOLD if is_dealer else WHITE, panel_rect, 2, border_radius=8)

        name_text = FONT_SMALL.render(player.name, True, WHITE)
        self.screen.blit(name_text, (x + 10, y + 10))

        # Show dealer/SB/BB indicators
        indicator_x = x + 150
        if is_dealer:
            dealer_text = FONT_TINY.render("(D)", True, GOLD)
            self.screen.blit(dealer_text, (indicator_x, y + 10))
        elif is_sb:
            sb_text = FONT_TINY.render("(SB)", True, LIGHT_GRAY)
            self.screen.blit(sb_text, (indicator_x - 10, y + 10))
        elif is_bb:
            bb_text = FONT_TINY.render("(BB)", True, LIGHT_GRAY)
            self.screen.blit(bb_text, (indicator_x - 10, y + 10))

        chips_text = FONT_SMALL.render(f"${player.chips}", True, GOLD)
        self.screen.blit(chips_text, (x + 10, y + 40))

        if player.current_bet > 0:
            bet_text = FONT_TINY.render(f"Bet: ${player.current_bet}", True, LIGHT_GRAY)
            self.screen.blit(bet_text, (x + 10, y + 65))

        status = "Folded" if player.folded else "All-In" if player.all_in else "Active"
        status_color = GRAY if player.folded else RED if player.all_in else WHITE
        status_text = FONT_TINY.render(status, True, status_color)
        self.screen.blit(status_text, (x + 10, y + 80))

        # Show face-down cards for bots (only if not folded and has cards)
        if player != self.player and len(player.hand) > 0 and not player.folded:
            card_width = 25
            card_height = 35
            card_x = x + 150
            card_y = y + 35

            # Draw two small face-down cards
            for i in range(2):
                # Draw card back (gray rectangle with pattern)
                card_rect = pygame.Rect(card_x + (i * 30), card_y, card_width, card_height)
                pygame.draw.rect(self.screen, BLUE, card_rect, border_radius=3)
                pygame.draw.rect(self.screen, WHITE, card_rect, 1, border_radius=3)

                # Add a pattern to show it's face-down
                pattern_rect = pygame.Rect(card_x + (i * 30) + 3, card_y + 3, card_width - 6, card_height - 6)
                pygame.draw.rect(self.screen, LIGHT_GRAY, pattern_rect, 1, border_radius=2)

    def draw_player_hand(self):
        """Draw player's hand."""
        if not self.player.hand:
            return

        card_width = 100
        card_height = 140
        spacing = 20
        total_width = 2 * card_width + spacing
        start_x = (WINDOW_WIDTH - total_width) // 2
        y = WINDOW_HEIGHT - 220

        panel_rect = pygame.Rect(start_x - 20, y - 60, total_width + 40, card_height + 120)
        pygame.draw.rect(self.screen, DARK_GREEN, panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, GOLD, panel_rect, 3, border_radius=10)

        # Determine player position
        num_players = len(self.game.all_players)
        sb_pos = (self.game.dealer_position + 1) % num_players
        bb_pos = (self.game.dealer_position + 2) % num_players
        is_dealer = 0 == self.game.dealer_position
        is_sb = 0 == sb_pos
        is_bb = 0 == bb_pos

        # Player name, chips, and position indicator
        position_str = ""
        if is_dealer:
            position_str = " (D)"
        elif is_sb:
            position_str = " (SB)"
        elif is_bb:
            position_str = " (BB)"

        info_text = FONT_MEDIUM.render(f"{self.player.name}{position_str} - ${self.player.chips}", True, GOLD)
        info_rect = info_text.get_rect(center=(WINDOW_WIDTH // 2, y - 30))
        self.screen.blit(info_text, info_rect)

        # Cards
        for i, card in enumerate(self.player.hand):
            x = start_x + i * (card_width + spacing)
            self.draw_card(card, x, y, card_width, card_height)

        # Hand rank
        if len(self.game.community_cards) >= 3:
            hand_name = HandEvaluator.get_hand_name(self.player.hand + self.game.community_cards)
            hand_text = FONT_SMALL.render(f"Hand: {hand_name}", True, LIGHT_GRAY)
            hand_rect = hand_text.get_rect(center=(WINDOW_WIDTH // 2, y + card_height + 15))
            self.screen.blit(hand_text, hand_rect)

        # Current bet
        if self.player.current_bet > 0:
            bet_text = FONT_SMALL.render(f"Current Bet: ${self.player.current_bet}", True, LIGHT_GRAY)
            bet_rect = bet_text.get_rect(center=(WINDOW_WIDTH // 2, y + card_height + 40))
            self.screen.blit(bet_text, bet_rect)

    def draw_action_buttons(self):
        """Draw betting action buttons."""
        call_amount = self.game.current_bet - self.player.current_bet

        # Position buttons at bottom center, below player's hand
        button_y = WINDOW_HEIGHT - 90
        button_width = 150
        button_height = 50
        spacing = 20

        self.buttons = []

        # Calculate total width to center buttons
        if call_amount == 0:
            num_buttons = 2
        else:
            num_buttons = 1 + (1 if call_amount <= self.player.chips else 0) + (1 if self.player.chips > call_amount else 0)

        total_width = num_buttons * button_width + (num_buttons - 1) * spacing
        start_x = (WINDOW_WIDTH - total_width) // 2
        x = start_x

        if call_amount == 0:
            self.buttons.append(Button(x, button_y, button_width, button_height, "Check"))
            x += button_width + spacing
            self.buttons.append(Button(x, button_y, button_width, button_height, "Bet"))
        else:
            self.buttons.append(Button(x, button_y, button_width, button_height, "Fold"))
            x += button_width + spacing

            if call_amount <= self.player.chips:
                self.buttons.append(Button(x, button_y, button_width, button_height, f"Call ${call_amount}"))
                x += button_width + spacing

            if self.player.chips > call_amount:
                self.buttons.append(Button(x, button_y, button_width, button_height, "Raise"))

        for button in self.buttons:
            button.draw(self.screen)

    def draw_action_history(self):
        """Draw recent action history."""
        y = 150
        for i in range(max(0, len(self.action_history) - 5), len(self.action_history)):
            action_text = FONT_TINY.render(self.action_history[i], True, LIGHT_GRAY)
            self.screen.blit(action_text, (WINDOW_WIDTH - 280, y))
            y += 25

    def draw_player_timer(self):
        """Draw universal turn timer for whoever is currently acting."""
        if not self.current_acting_player:
            return

        time_left = self.turn_time_limit - self.turn_timer
        seconds_left = time_left // 60

        # Timer bar - always visible at top center
        bar_width = 300
        bar_height = 25
        bar_x = WINDOW_WIDTH // 2 - bar_width // 2
        bar_y = 20

        # Background
        pygame.draw.rect(self.screen, DARK_GREEN, (bar_x, bar_y, bar_width, bar_height), border_radius=5)

        # Fill (progress bar)
        fill_width = int(bar_width * (time_left / self.turn_time_limit))

        # Color based on time left
        if self.current_acting_player == self.player:
            # Player timer - red when low
            fill_color = RED if seconds_left <= 3 else GOLD if seconds_left <= 5 else (100, 200, 100)
        else:
            # Bot timer - blue/cyan
            fill_color = (70, 130, 180)

        pygame.draw.rect(self.screen, fill_color, (bar_x, bar_y, fill_width, bar_height), border_radius=5)

        # Border
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2, border_radius=5)

        # Text - show who is acting
        player_name = self.current_acting_player.name
        timer_text = FONT_SMALL.render(f"{player_name}'s turn: {seconds_left}s", True, WHITE)
        timer_rect = timer_text.get_rect(center=(bar_x + bar_width // 2, bar_y + bar_height // 2))
        self.screen.blit(timer_text, timer_rect)

    def draw_bet_dialog(self):
        """Draw bet/raise input dialog."""
        # Overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # Dialog box
        dialog_width = 400
        dialog_height = 250
        dialog_x = (WINDOW_WIDTH - dialog_width) // 2
        dialog_y = (WINDOW_HEIGHT - dialog_height) // 2

        pygame.draw.rect(self.screen, DARK_GREEN, (dialog_x, dialog_y, dialog_width, dialog_height), border_radius=10)
        pygame.draw.rect(self.screen, GOLD, (dialog_x, dialog_y, dialog_width, dialog_height), 3, border_radius=10)

        # Title
        title = self.bet_action.upper()
        title_text = FONT_LARGE.render(title, True, GOLD)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, dialog_y + 40))
        self.screen.blit(title_text, title_rect)

        # Input field
        input_rect = pygame.Rect(dialog_x + 50, dialog_y + 90, dialog_width - 100, 50)
        pygame.draw.rect(self.screen, WHITE, input_rect, border_radius=5)
        pygame.draw.rect(self.screen, GOLD, input_rect, 2, border_radius=5)

        input_text = FONT_MEDIUM.render(f"${self.bet_input}", True, BLACK)
        input_text_rect = input_text.get_rect(center=input_rect.center)
        self.screen.blit(input_text, input_text_rect)

        # Instructions
        call_amount = self.game.current_bet - self.player.current_bet
        if self.bet_action == "bet":
            min_amount = self.game.min_raise
            max_amount = self.player.chips
        else:
            min_amount = self.game.min_raise
            max_amount = self.player.chips - call_amount

        inst_text = FONT_SMALL.render(f"Min: ${min_amount} | Max: ${max_amount}", True, LIGHT_GRAY)
        inst_rect = inst_text.get_rect(center=(WINDOW_WIDTH // 2, dialog_y + 160))
        self.screen.blit(inst_text, inst_rect)

        help_text = FONT_TINY.render("Press ENTER to confirm, ESC to cancel", True, LIGHT_GRAY)
        help_rect = help_text.get_rect(center=(WINDOW_WIDTH // 2, dialog_y + 200))
        self.screen.blit(help_text, help_rect)

    def draw_results(self):
        """Draw hand results."""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # Results panel
        panel_width = 600
        panel_height = 300 + len(self.winners) * 50
        panel_x = (WINDOW_WIDTH - panel_width) // 2
        panel_y = (WINDOW_HEIGHT - panel_height) // 2

        pygame.draw.rect(self.screen, DARK_GREEN, (panel_x, panel_y, panel_width, panel_height), border_radius=10)
        pygame.draw.rect(self.screen, GOLD, (panel_x, panel_y, panel_width, panel_height), 3, border_radius=10)

        # Title
        title = FONT_LARGE.render("HAND RESULTS", True, GOLD)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, panel_y + 40))
        self.screen.blit(title, title_rect)

        # Winners
        y = panel_y + 100
        for player, amount, hand_name in self.winners:
            winner_text = FONT_MEDIUM.render(f"{player.name}", True, WHITE)
            winner_rect = winner_text.get_rect(center=(WINDOW_WIDTH // 2, y))
            self.screen.blit(winner_text, winner_rect)

            hand_text = FONT_SMALL.render(f"{hand_name} - Won ${amount}", True, GOLD)
            hand_rect = hand_text.get_rect(center=(WINDOW_WIDTH // 2, y + 30))
            self.screen.blit(hand_text, hand_rect)
            y += 70

        # Buttons
        self.buttons = [
            Button(WINDOW_WIDTH // 2 - 250, panel_y + panel_height - 80, 200, 60, "Continue"),
            Button(WINDOW_WIDTH // 2 + 50, panel_y + panel_height - 80, 200, 60, "Main Menu")
        ]

        for button in self.buttons:
            button.draw(self.screen)

    def draw_game_over(self):
        """Draw game over screen."""
        bots_with_chips = [b for b in self.game.bots if b.chips > 0] if self.game else []
        player_won = self.player.chips > 0 and len(bots_with_chips) == 0

        if player_won:
            title = FONT_LARGE.render("CONGRATULATIONS!", True, GOLD)
            subtitle = FONT_MEDIUM.render("You won all the chips!", True, WHITE)
        else:
            title = FONT_LARGE.render("GAME OVER", True, RED)
            subtitle = FONT_MEDIUM.render("You ran out of chips", True, WHITE)

        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 200))
        subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, 280))
        self.screen.blit(title, title_rect)
        self.screen.blit(subtitle, subtitle_rect)

        chips_text = FONT_MEDIUM.render(f"Final Chips: ${self.player.chips}", True, GOLD)
        chips_rect = chips_text.get_rect(center=(WINDOW_WIDTH // 2, 360))
        self.screen.blit(chips_text, chips_rect)

        self.buttons = [
            Button(WINDOW_WIDTH // 2 - 150, 450, 300, 60, "Main Menu"),
            Button(WINDOW_WIDTH // 2 - 150, 530, 300, 60, "Quit")
        ]

        for button in self.buttons:
            button.draw(self.screen)

    def draw_hand_evaluation(self):
        """Draw pot odds evaluation panel in top right corner."""
        panel_width = 280
        panel_height = 180
        panel_x = WINDOW_WIDTH - panel_width - 20
        panel_y = 100

        # Get pot odds evaluation
        pot_odds_str, odds_against_str, recommendation = self.calculate_pot_odds_evaluation()

        # Panel background
        pygame.draw.rect(self.screen, DARK_GREEN, (panel_x, panel_y, panel_width, panel_height), border_radius=8)
        pygame.draw.rect(self.screen, GOLD, (panel_x, panel_y, panel_width, panel_height), 3, border_radius=8)

        # Title
        title_text = FONT_SMALL.render("Pot Odds Analysis", True, GOLD)
        self.screen.blit(title_text, (panel_x + 10, panel_y + 10))

        # Pot Odds
        pot_odds_label = FONT_TINY.render("Pot Odds:", True, WHITE)
        self.screen.blit(pot_odds_label, (panel_x + 10, panel_y + 45))
        pot_odds_value = FONT_SMALL.render(pot_odds_str, True, LIGHT_GRAY)
        self.screen.blit(pot_odds_value, (panel_x + 100, panel_y + 42))

        # Odds Against
        odds_against_label = FONT_TINY.render("Odds Against:", True, WHITE)
        self.screen.blit(odds_against_label, (panel_x + 10, panel_y + 75))
        odds_against_value = FONT_SMALL.render(odds_against_str, True, LIGHT_GRAY)
        self.screen.blit(odds_against_value, (panel_x + 120, panel_y + 72))

        # Outs count
        if len(self.game.community_cards) >= 3:
            outs = self.calculate_outs()
            outs_label = FONT_TINY.render(f"Outs:", True, WHITE)
            self.screen.blit(outs_label, (panel_x + 10, panel_y + 105))
            outs_value = FONT_SMALL.render(f"{outs}", True, LIGHT_GRAY)
            self.screen.blit(outs_value, (panel_x + 100, panel_y + 102))

        # Recommendation with colored background
        rec_y = panel_y + 135
        rec_bg_height = 35

        # Determine color based on recommendation
        if "CALL" in recommendation or "BET" in recommendation or "RAISE" in recommendation:
            rec_bg_color = (50, 205, 50)  # Green
        elif "FOLD" in recommendation:
            rec_bg_color = RED
        else:
            rec_bg_color = GOLD

        pygame.draw.rect(self.screen, rec_bg_color, (panel_x + 5, rec_y, panel_width - 10, rec_bg_height), border_radius=5)

        # Recommendation text
        rec_text = FONT_SMALL.render("→ " + recommendation, True, BLACK if rec_bg_color == GOLD else WHITE)
        rec_rect = rec_text.get_rect(center=(panel_x + panel_width // 2, rec_y + rec_bg_height // 2))
        self.screen.blit(rec_text, rec_rect)

    def draw_message_overlay(self):
        """Draw message overlay."""
        if not self.message:
            return

        overlay = pygame.Surface((WINDOW_WIDTH, 100))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, WINDOW_HEIGHT // 2 - 50))

        text = FONT_LARGE.render(self.message, True, GOLD)
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.screen.blit(text, text_rect)


if __name__ == "__main__":
    gui = PokerGUI()
    gui.run()
