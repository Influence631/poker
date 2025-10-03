"""Main poker game logic."""
from typing import List, Optional, Dict
from poker_cards import Deck, Card
from player import Player, AIBot
from hand_evaluator import HandEvaluator


class PokerGame:
    """Manages a poker game."""

    def __init__(self, player: Player, num_bots: int = 3, small_blind: int = 10, bot_difficulty: str = "medium"):
        self.player = player
        self.bots = [AIBot(f"Bot {i+1}", difficulty=bot_difficulty) for i in range(num_bots)]
        self.all_players = [player] + self.bots
        self.deck = Deck()
        self.community_cards: List[Card] = []
        self.pot = 0
        self.player_contributions: Dict[Player, int] = {}  # Track each player's contribution to pot
        self.small_blind = small_blind
        self.big_blind = small_blind * 2
        self.current_bet = 0
        self.min_raise = self.big_blind
        self.dealer_position = 0

    def start_new_hand(self):
        """Start a new hand."""
        # Reset players
        for p in self.all_players:
            p.reset_for_new_hand()

        # Remove players with no chips
        self.all_players = [p for p in self.all_players if p.chips > 0]

        if len(self.all_players) < 2:
            return False  # Game over

        # Reset game state
        self.deck.reset()
        self.community_cards = []
        self.pot = 0
        self.player_contributions = {p: 0 for p in self.all_players}  # Reset contributions
        self.current_bet = 0
        self.min_raise = self.big_blind

        # Don't post blinds here - let GUI handle it as animated actions

        # Deal hole cards
        for player in self.all_players:
            player.receive_cards(self.deck.deal(2))

        return True

    def post_blind(self, player_pos: int, amount: int):
        """Post a blind for a specific player position."""
        player = self.all_players[player_pos]
        actual_amount = player.bet(amount)
        self.pot += actual_amount
        self.player_contributions[player] = self.player_contributions.get(player, 0) + actual_amount
        if amount == self.big_blind:
            self.current_bet = self.big_blind
        return actual_amount

    def _post_blinds(self):
        """Post small and big blinds."""
        num_players = len(self.all_players)
        small_blind_pos = (self.dealer_position + 1) % num_players
        big_blind_pos = (self.dealer_position + 2) % num_players

        # Small blind
        sb_player = self.all_players[small_blind_pos]
        sb_amount = sb_player.bet(self.small_blind)
        self.pot += sb_amount
        self.player_contributions[sb_player] = self.player_contributions.get(sb_player, 0) + sb_amount

        # Big blind
        bb_player = self.all_players[big_blind_pos]
        bb_amount = bb_player.bet(self.big_blind)
        self.pot += bb_amount
        self.player_contributions[bb_player] = self.player_contributions.get(bb_player, 0) + bb_amount
        self.current_bet = self.big_blind

    def deal_flop(self):
        """Deal the flop (3 cards)."""
        self.deck.deal(1)  # Burn card
        self.community_cards.extend(self.deck.deal(3))
        self.current_bet = 0
        for p in self.all_players:
            p.current_bet = 0

    def deal_turn(self):
        """Deal the turn (1 card)."""
        self.deck.deal(1)  # Burn card
        self.community_cards.extend(self.deck.deal(1))
        self.current_bet = 0
        for p in self.all_players:
            p.current_bet = 0

    def deal_river(self):
        """Deal the river (1 card)."""
        self.deck.deal(1)  # Burn card
        self.community_cards.extend(self.deck.deal(1))
        self.current_bet = 0
        for p in self.all_players:
            p.current_bet = 0

    def betting_round(self, starting_position: int = 0) -> bool:
        """
        Conduct a betting round.
        Returns False if all players except one have folded.
        """
        active_players = [p for p in self.all_players if not p.folded and not p.all_in]

        if len(active_players) <= 1:
            return False

        # Players who need to act
        players_to_act = active_players.copy()
        last_raiser = None

        # Start from the position after the dealer
        current_pos = starting_position % len(self.all_players)

        while players_to_act:
            player = self.all_players[current_pos]

            # Skip if folded, all-in, or already acted
            if player.folded or player.all_in or player not in players_to_act:
                current_pos = (current_pos + 1) % len(self.all_players)
                continue

            # Player needs to act
            call_amount = self.current_bet - player.current_bet

            # Get player action (this will be handled by UI for human player)
            if isinstance(player, AIBot):
                action, amount = player.make_decision(
                    self.pot, self.current_bet, self.community_cards, self.min_raise
                )

                if action == "fold":
                    player.fold()
                    players_to_act.remove(player)
                elif action == "call":
                    actual_bet = player.bet(call_amount)
                    self.pot += actual_bet
                    players_to_act.remove(player)
                elif action == "check":
                    players_to_act.remove(player)
                elif action == "raise":
                    total_bet = call_amount + amount
                    actual_bet = player.bet(total_bet)
                    self.pot += actual_bet
                    self.current_bet = player.current_bet
                    self.min_raise = amount
                    last_raiser = player
                    # Reset players_to_act (everyone needs to respond to raise)
                    players_to_act = [p for p in active_players if p != player and not p.folded and not p.all_in]

            current_pos = (current_pos + 1) % len(self.all_players)

        # Check if only one player remains
        remaining = [p for p in self.all_players if not p.folded]
        return len(remaining) > 1

    def determine_winners(self) -> List[tuple[Player, int, str]]:
        """
        Determine winners and distribute pot with side pot support.
        Returns list of (player, amount_won, hand_name) tuples.
        """
        active_players = [p for p in self.all_players if not p.folded]

        if len(active_players) == 1:
            # Only one player left - they win only what they contributed
            winner = active_players[0]
            # Calculate total pot that winner is eligible for
            winner_contribution = self.player_contributions.get(winner, 0)
            eligible_pot = min(self.pot, sum(min(self.player_contributions.get(p, 0), winner_contribution)
                                             for p in self.all_players))
            winner.win(eligible_pot)
            return [(winner, eligible_pot, "Opponent(s) folded")]

        # Calculate side pots
        side_pots = self._calculate_side_pots(active_players)

        # Evaluate all hands
        hands = {}
        for player in active_players:
            full_hand = player.hand + self.community_cards
            rank, tiebreaker = HandEvaluator.evaluate_hand(full_hand)
            hand_name = HandEvaluator.get_hand_name(full_hand)
            hands[player] = (rank, tiebreaker, hand_name)

        # Award each side pot
        results = []
        for pot_amount, eligible_players in side_pots:
            # Find best hand among eligible players
            eligible_hands = [(p, hands[p][0], hands[p][1], hands[p][2])
                             for p in eligible_players]
            eligible_hands.sort(key=lambda x: (x[1], x[2]), reverse=True)

            # Find all winners of this pot (ties possible)
            best_rank = eligible_hands[0][1]
            best_tiebreaker = eligible_hands[0][2]
            pot_winners = [h for h in eligible_hands
                          if h[1] == best_rank and h[2] == best_tiebreaker]

            # Split pot among winners
            winners_share = pot_amount // len(pot_winners)
            for player, _, _, hand_name in pot_winners:
                player.win(winners_share)
                # Check if this player already in results (won multiple pots)
                existing = [r for r in results if r[0] == player]
                if existing:
                    # Update amount
                    idx = results.index(existing[0])
                    old_amount = results[idx][1]
                    results[idx] = (player, old_amount + winners_share, hand_name)
                else:
                    results.append((player, winners_share, hand_name))

        return results

    def _calculate_side_pots(self, active_players: List[Player]) -> List[tuple[int, List[Player]]]:
        """
        Calculate side pots based on player contributions.
        Returns list of (pot_amount, eligible_players) tuples.
        """
        # Get contributions of active players
        contributions = [(p, self.player_contributions.get(p, 0)) for p in active_players]

        # Sort by contribution amount
        contributions.sort(key=lambda x: x[1])

        pots = []
        previous_level = 0

        for i, (player, contribution) in enumerate(contributions):
            if contribution > previous_level:
                # Create a pot for this level
                pot_size = (contribution - previous_level) * (len(contributions) - i)

                # Also add contributions from folded players up to this level
                for folded_player in [p for p in self.all_players if p.folded]:
                    folded_contribution = self.player_contributions.get(folded_player, 0)
                    pot_size += max(0, min(contribution, folded_contribution) - previous_level)

                # Players eligible for this pot (all who contributed at least this much)
                eligible = [p for p, c in contributions if c >= contribution]

                pots.append((pot_size, eligible))
                previous_level = contribution

        return pots

    def get_active_players(self) -> List[Player]:
        """Get players still in the hand."""
        return [p for p in self.all_players if not p.folded]

    def is_game_over(self) -> bool:
        """Check if game is over."""
        # Game over if player has no chips
        if self.player.chips <= 0:
            return True

        # Game over if only one player has chips (including the human player)
        players_with_chips = [p for p in self.all_players if p.chips > 0]
        if len(players_with_chips) <= 1:
            return True

        # Game over if player is not in the game anymore (no chips)
        if self.player not in self.all_players:
            return True

        return False

    def move_dealer_button(self):
        """Move dealer button to next player."""
        self.dealer_position = (self.dealer_position + 1) % len(self.all_players)
