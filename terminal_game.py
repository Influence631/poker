"""Main game controller."""
from player import Player
from poker_game import PokerGame
from ui import PokerUI
from education import PokerEducation
from llm_evaluator import LLMEvaluator
import json
import os


class GameController:
    """Main game controller."""

    SAVE_FILE = "player_data.json"

    def __init__(self):
        self.ui = PokerUI()
        self.player = self.load_player()
        self.game = None

    def load_player(self) -> Player:
        """Load or create player."""
        if os.path.exists(self.SAVE_FILE):
            try:
                with open(self.SAVE_FILE, 'r') as f:
                    data = json.load(f)
                    return Player(data.get("name", "Player"), data.get("chips", 1000))
            except:
                pass

        # Create new player
        self.ui.clear()
        self.ui.show_title()
        name = self.ui.console.input("[cyan]Enter your name:[/cyan] ").strip() or "Player"
        return Player(name, 1000)

    def save_player(self):
        """Save player data."""
        data = {
            "name": self.player.name,
            "chips": self.player.chips
        }
        with open(self.SAVE_FILE, 'w') as f:
            json.dump(data, f)

    def run(self):
        """Main game loop."""
        while True:
            choice = self.ui.show_main_menu()

            if choice == "1":
                self.play_poker()
            elif choice == "2":
                self.visit_store()
            elif choice == "3":
                self.ui.show_stats(self.player)
            elif choice == "4":
                self.save_player()
                self.ui.show_message("Thanks for playing!", "bold green")
                break

    def visit_store(self):
        """Handle store visit."""
        while True:
            chips = self.ui.show_store(self.player.chips)
            if chips:
                self.player.chips += chips
                self.ui.show_message(f"Added ${chips} to your account!", "bold green")
                self.save_player()
            else:
                break

    def play_poker(self):
        """Play a poker game."""
        if self.player.chips < 20:
            self.ui.show_message("You don't have enough chips! Visit the store to get free chips.", "bold red")
            self.ui.ask_continue("Press Enter to continue")
            return

        # Ask for bot difficulty
        difficulty = self.ui.ask_bot_difficulty()

        # Create new game
        self.game = PokerGame(self.player, num_bots=3, small_blind=10, bot_difficulty=difficulty)

        continue_playing = True
        while not self.game.is_game_over() and continue_playing:
            # Start new hand
            if not self.game.start_new_hand():
                break

            self.ui.show_game_state(
                self.player,
                self.game.all_players,
                self.game.community_cards,
                self.game.pot,
                self.game.current_bet,
                self.game.dealer_position
            )

            self.ui.show_message("New hand started!", "bold yellow")
            self.ui.ask_continue("Press Enter to continue")

            # Pre-flop betting
            if not self.run_betting_round("Pre-flop"):
                continue_playing = self.end_hand()
                continue

            # Flop
            self.game.deal_flop()
            self.ui.show_game_state(
                self.player,
                self.game.all_players,
                self.game.community_cards,
                self.game.pot,
                self.game.current_bet,
                self.game.dealer_position
            )

            # Educational questions after flop
            if not self.player.folded:
                self.ask_educational_questions("Flop")

            if not self.run_betting_round("Flop"):
                continue_playing = self.end_hand()
                continue

            # Turn
            self.game.deal_turn()
            self.ui.show_game_state(
                self.player,
                self.game.all_players,
                self.game.community_cards,
                self.game.pot,
                self.game.current_bet,
                self.game.dealer_position
            )

            # Educational questions after turn
            if not self.player.folded:
                self.ask_educational_questions("Turn")

            if not self.run_betting_round("Turn"):
                continue_playing = self.end_hand()
                continue

            # River
            self.game.deal_river()
            self.ui.show_game_state(
                self.player,
                self.game.all_players,
                self.game.community_cards,
                self.game.pot,
                self.game.current_bet,
                self.game.dealer_position
            )

            # Educational questions after river
            if not self.player.folded:
                self.ask_educational_questions("River")

            if not self.run_betting_round("River"):
                continue_playing = self.end_hand()
                continue

            # Showdown
            continue_playing = self.end_hand()

        # Game over - check if player won
        # Player wins if they have chips and all bots are out
        bots_with_chips = [b for b in self.game.bots if b.chips > 0]
        player_won = self.player.chips > 0 and len(bots_with_chips) == 0

        self.ui.show_game_over(player_won)
        self.save_player()
        self.ui.ask_continue("Press Enter to continue")

    def ask_educational_questions(self, stage: str):
        """Ask educational questions specific to the stage."""
        self.ui.show_message(f"\n=== Educational Questions ({stage}) ===", "bold magenta")

        # Question 1: Pot Odds (Avi Rubin style - as a ratio)
        call_amount = self.game.current_bet - self.player.current_bet
        if call_amount > 0:
            pot_odds = PokerEducation.calculate_pot_odds(self.game.pot, call_amount)

            answer = self.ui.ask_educational_question(
                f"What are the pot odds? (Format: X:1 or X.X:1)\n"
                f"Pot: ${self.game.pot}, You need to call: ${call_amount}",
                "Formula: pot / bet to call"
            )

            is_correct, feedback = PokerEducation.evaluate_answer("pot_odds", answer, pot_odds)
            self.ui.show_feedback(is_correct, feedback)

        # Question 2: Outs (stage-specific)
        outs_dict = PokerEducation.calculate_outs(
            self.player.hand,
            self.game.community_cards,
            []
        )
        total_outs = PokerEducation.count_total_outs(outs_dict)

        if total_outs > 0 or stage in ["Turn", "River"]:
            # Create clearer question based on stage
            if stage == "Flop":
                question = f"How many outs do you have for the TURN card?\n(Count cards that would improve your hand on the next card)"
                hint = "Outs are cards that will improve your hand. We're counting what helps on the TURN only."
            elif stage == "Turn":
                question = f"How many outs do you have for the RIVER card?\n(Count cards that would improve your hand on the final card)"
                hint = "Count remaining cards in the deck that would give you a better hand on the RIVER."
            else:  # River
                question = f"How many outs did you have?\n(This is for learning - the hand is complete)"
                hint = "Count what cards would have helped you."

            answer = self.ui.ask_educational_question(question, hint)

            # Use LLM evaluation for better reasoning
            context = {
                "player_hand": self.player.hand,
                "community_cards": self.game.community_cards,
                "outs_dict": outs_dict,
                "stage": stage
            }

            is_correct, feedback, reasoning = LLMEvaluator.evaluate_answer_with_llm(
                "outs", answer, total_outs, context
            )

            if not is_correct and total_outs > 0:
                outs_display = PokerEducation.get_out_cards_display(outs_dict)
                self.ui.show_feedback(is_correct, feedback, outs_display)
            else:
                self.ui.show_feedback(is_correct, feedback)

            # Show reasoning if available
            if reasoning:
                self.ui.show_message(f"\n[dim]Detailed reasoning: {reasoning}[/dim]\n", "")

            # Offer interactive chat
            from rich.prompt import Confirm
            if Confirm.ask("[cyan]Want to discuss this hand with the poker tutor?[/cyan]", default=False):
                LLMEvaluator.interactive_chat(context, self.ui)

            # Question 3: Win Odds (Avi Rubin style - as a ratio)
            if total_outs > 0:
                win_odds = PokerEducation.calculate_equity(total_outs, len(self.game.community_cards))

                known_cards = 2 + len(self.game.community_cards)
                unknown_cards = 52 - known_cards

                answer = self.ui.ask_educational_question(
                    f"What are your odds to win? (Format: X:1 or X.X:1)\n"
                    f"You have {total_outs} outs, {unknown_cards} unknown cards remain",
                    "Formula: (unknown cards - outs) / outs"
                )

                is_correct, feedback = PokerEducation.evaluate_answer("win_odds", answer, win_odds)
                self.ui.show_feedback(is_correct, feedback)

                # Show recommendation
                if call_amount > 0:
                    pot_odds_ratio, pot_odds_str = pot_odds
                    win_odds_ratio, win_odds_str = win_odds
                    hand_rank, _ = HandEvaluator.evaluate_hand(self.player.hand + self.game.community_cards)

                    recommendation = PokerEducation.get_recommendation(
                        pot_odds_ratio, win_odds_ratio, pot_odds_str, win_odds_str, hand_rank
                    )
                    self.ui.show_message(f"\n[yellow]Analysis:[/yellow] {recommendation}\n", "")

    def run_betting_round(self, round_name: str) -> bool:
        """
        Run a betting round.
        Returns False if only one player remains.
        """
        self.ui.show_message(f"\n--- {round_name} Betting ---", "bold cyan")

        # Determine starting position
        if round_name == "Pre-flop":
            # Pre-flop starts after big blind
            start_pos = (self.game.dealer_position + 3) % len(self.game.all_players)
        else:
            # Post-flop starts after dealer
            start_pos = (self.game.dealer_position + 1) % len(self.game.all_players)

        active_players = [p for p in self.game.all_players if not p.folded and not p.all_in]
        players_to_act = active_players.copy()

        current_pos = start_pos

        while players_to_act:
            player = self.game.all_players[current_pos]

            if player.folded or player.all_in or player not in players_to_act:
                current_pos = (current_pos + 1) % len(self.game.all_players)
                continue

            call_amount = self.game.current_bet - player.current_bet

            # Player's turn
            if player == self.player:
                self.ui.show_game_state(
                    self.player,
                    self.game.all_players,
                    self.game.community_cards,
                    self.game.pot,
                    self.game.current_bet,
                    self.game.dealer_position
                )

                action, amount = self.ui.get_player_action(
                    self.game.current_bet,
                    player.current_bet,
                    player.chips,
                    self.game.min_raise
                )

                if action == "fold":
                    player.fold()
                    players_to_act.remove(player)
                elif action == "call":
                    actual_bet = player.bet(call_amount)
                    self.game.pot += actual_bet
                    players_to_act.remove(player)
                elif action == "check":
                    players_to_act.remove(player)
                elif action == "bet" or action == "raise":
                    total_bet = call_amount + amount
                    actual_bet = player.bet(total_bet)
                    self.game.pot += actual_bet
                    self.game.current_bet = player.current_bet
                    self.game.min_raise = amount
                    # Reset players_to_act
                    players_to_act = [p for p in active_players if p != player and not p.folded and not p.all_in]

            else:
                # AI bot
                from player import AIBot
                if isinstance(player, AIBot):
                    action, amount = player.make_decision(
                        self.game.pot,
                        self.game.current_bet,
                        self.game.community_cards,
                        self.game.min_raise
                    )

                    if action == "fold":
                        player.fold()
                        players_to_act.remove(player)
                        self.ui.show_bot_action(player.name, "fold")
                    elif action == "call":
                        actual_bet = player.bet(call_amount)
                        self.game.pot += actual_bet
                        players_to_act.remove(player)
                        self.ui.show_bot_action(player.name, "call", actual_bet)
                    elif action == "check":
                        players_to_act.remove(player)
                        self.ui.show_bot_action(player.name, "check")
                    elif action == "raise":
                        total_bet = call_amount + amount
                        actual_bet = player.bet(total_bet)
                        self.game.pot += actual_bet
                        self.game.current_bet = player.current_bet
                        self.game.min_raise = amount
                        players_to_act = [p for p in active_players if p != player and not p.folded and not p.all_in]
                        self.ui.show_bot_action(player.name, "raise", actual_bet)

            current_pos = (current_pos + 1) % len(self.game.all_players)

        # Check if only one player remains
        remaining = [p for p in self.game.all_players if not p.folded]
        return len(remaining) > 1

    def end_hand(self) -> bool:
        """
        End the current hand.
        Returns True if player wants to continue, False otherwise.
        """
        winners = self.game.determine_winners()
        self.ui.show_game_state(
            self.player,
            self.game.all_players,
            self.game.community_cards,
            self.game.pot,
            self.game.current_bet,
            self.game.dealer_position
        )
        self.ui.show_winners(winners)

        self.game.move_dealer_button()
        self.save_player()

        if not self.game.is_game_over():
            return self.ui.ask_continue("Continue to next hand?")
        return False


if __name__ == "__main__":
    controller = GameController()
    controller.run()
