"""Player and AI bot classes."""
from typing import List, Optional
from poker_cards import Card
from hand_evaluator import HandEvaluator
import random


class Player:
    """Represents a poker player."""

    def __init__(self, name: str, chips: int = 1000):
        self.name = name
        self.chips = chips
        self.hand: List[Card] = []
        self.current_bet = 0
        self.folded = False
        self.all_in = False

    def receive_cards(self, cards: List[Card]):
        """Receive cards."""
        self.hand = cards

    def bet(self, amount: int) -> int:
        """Place a bet. Returns actual amount bet."""
        if amount >= self.chips:
            # All in
            actual_bet = self.chips
            self.chips = 0
            self.all_in = True
        else:
            actual_bet = amount
            self.chips -= amount

        self.current_bet += actual_bet
        return actual_bet

    def fold(self):
        """Fold the hand."""
        self.folded = True

    def win(self, amount: int):
        """Win chips."""
        self.chips += amount

    def reset_for_new_hand(self):
        """Reset player state for new hand."""
        self.hand = []
        self.current_bet = 0
        self.folded = False
        self.all_in = False

    def __str__(self) -> str:
        return f"{self.name} (${self.chips})"


class AIBot(Player):
    """AI bot player with decision-making logic."""

    def __init__(self, name: str, chips: int = 1000, difficulty: str = "medium"):
        super().__init__(name, chips)
        self.difficulty = difficulty

    def _calculate_outs(self, community_cards: List[Card]) -> int:
        """Calculate the number of outs to improve the hand."""
        if len(self.hand) != 2 or len(community_cards) < 3:
            return 0

        from poker_cards import Rank, Suit, Card as PokerCard

        full_hand = self.hand + community_cards
        current_rank, current_tie = HandEvaluator.evaluate_hand(full_hand)

        # Get all known cards
        known_cards = set(full_hand)

        # Create all possible cards and filter out known ones
        all_cards = [PokerCard(rank, suit) for suit in Suit for rank in Rank]
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

    def make_decision(self, pot: int, current_bet: int, community_cards: List[Card],
                      min_raise: int) -> tuple[str, int]:
        """
        Make a betting decision using pot odds.
        Returns (action, amount) where action is 'fold', 'call', 'raise', or 'check'
        """
        call_amount = current_bet - self.current_bet

        # Can't continue if no chips
        if self.chips == 0:
            return ("check", 0)

        # Check if pre-flop or post-flop
        is_preflop = len(community_cards) == 0
        is_postflop = len(community_cards) >= 3

        # Calculate hand strength
        if is_postflop:
            full_hand = self.hand + community_cards
            hand_rank, _ = HandEvaluator.evaluate_hand(full_hand)
            hand_strength = hand_rank / 10.0  # Normalize to 0-1
        else:
            # Pre-flop: evaluate pocket cards
            hand_strength = self._evaluate_preflop_hand()

        # Difficulty-based adjustments
        aggression = 0.5  # Base aggression
        bluff_rate = 0.15  # Base bluff rate
        pot_odds_threshold = 1.0  # How strictly to follow pot odds

        if self.difficulty == "easy":
            hand_strength *= 0.85
            aggression = 0.35
            bluff_rate = 0.05
            pot_odds_threshold = 1.2  # Requires better odds to call
        elif self.difficulty == "medium":
            hand_strength *= 1.0
            aggression = 0.55
            bluff_rate = 0.15
            pot_odds_threshold = 1.0
        elif self.difficulty == "hard":
            hand_strength *= 1.05
            aggression = 0.75
            bluff_rate = 0.25
            pot_odds_threshold = 0.9  # More willing to take marginal spots

        # Add some randomness (less for harder bots)
        randomness = 0.12 if self.difficulty == "easy" else 0.06
        hand_strength += random.uniform(-randomness, randomness)
        hand_strength = max(0.05, min(0.95, hand_strength))

        # POST-FLOP: Use pot odds calculation
        if is_postflop and call_amount > 0:
            # Calculate pot odds: (pot + call_amount) / call_amount
            pot_after_call = pot + call_amount
            pot_odds_ratio = pot_after_call / call_amount if call_amount > 0 else 0

            # Calculate outs
            outs = self._calculate_outs(community_cards)

            # Calculate odds against hitting
            known_cards_count = len(self.hand) + len(community_cards)
            unknown_cards = 52 - known_cards_count

            if outs > 0:
                odds_against_ratio = (unknown_cards - outs) / outs
            else:
                odds_against_ratio = 999  # Very high

            # Decision based on pot odds vs odds against
            # If pot odds > odds against (adjusted by threshold), it's profitable to call
            should_call_by_odds = pot_odds_ratio > (odds_against_ratio * pot_odds_threshold)

            # Strong made hand (no need for outs)
            if hand_rank >= 6:  # Flush or better
                # Almost always call/raise with strong hands
                if random.random() < 0.9:
                    if random.random() < aggression and self.chips > call_amount + min_raise:
                        # Raise
                        raise_size = int(pot * random.uniform(0.7, 1.5))
                        raise_size = max(min_raise, min(raise_size, self.chips - call_amount))
                        return ("raise", raise_size)
                    else:
                        return ("call", min(call_amount, self.chips))
                else:
                    return ("call", min(call_amount, self.chips))

            # Medium-strong hand with drawing potential
            elif hand_rank >= 3 or should_call_by_odds:
                # Call if pot odds are favorable or hand is decent
                if call_amount <= self.chips:
                    # Consider raising if hand is strong enough and odds are very good
                    if hand_rank >= 4 and random.random() < aggression * 0.5:
                        raise_size = int(pot * random.uniform(0.5, 1.0))
                        raise_size = max(min_raise, min(raise_size, self.chips - call_amount))
                        if raise_size > 0:
                            return ("raise", raise_size)
                    return ("call", min(call_amount, self.chips))
                else:
                    return ("fold", 0)

            # Weak hand
            else:
                # Only call if pot odds are very good or bluffing
                if should_call_by_odds and call_amount <= self.chips * 0.2:
                    return ("call", min(call_amount, self.chips))
                elif random.random() < bluff_rate * 0.5:
                    return ("call", min(call_amount, self.chips))
                else:
                    return ("fold", 0)

        # NO BET TO CALL: Decide whether to check or bet
        if call_amount == 0:
            # Strong hand: usually bet
            if hand_strength >= 0.65:
                if random.random() < (0.8 + aggression * 0.2):
                    bet_size = int(pot * random.uniform(0.5, 1.0))
                    bet_size = max(min_raise, min(bet_size, self.chips))
                    return ("raise", bet_size)
                else:
                    # Slow play occasionally
                    return ("check", 0)

            # Medium hand: sometimes bet
            elif hand_strength >= 0.4:
                if random.random() < (aggression * 0.7):
                    bet_size = int(pot * random.uniform(0.4, 0.7))
                    bet_size = max(min_raise, min(bet_size, self.chips))
                    return ("raise", bet_size)
                return ("check", 0)

            # Weak hand: mostly check, occasionally bluff
            else:
                if random.random() < bluff_rate * aggression:
                    bet_size = int(pot * random.uniform(0.3, 0.6))
                    bet_size = max(min_raise, min(bet_size, self.chips))
                    return ("raise", bet_size)
                return ("check", 0)

        # PRE-FLOP WITH BET: Simplified decision
        if is_preflop:
            pot_odds = call_amount / (pot + call_amount) if (pot + call_amount) > 0 else 0

            if hand_strength >= 0.7:
                # Strong pre-flop hand: raise or call
                if random.random() < aggression and self.chips > call_amount + min_raise:
                    raise_size = int(pot * random.uniform(0.5, 1.0))
                    raise_size = max(min_raise, min(raise_size, self.chips - call_amount))
                    return ("raise", raise_size)
                return ("call", min(call_amount, self.chips))
            elif hand_strength >= 0.45:
                # Decent hand: call if odds are good
                if call_amount <= self.chips * 0.3:
                    return ("call", min(call_amount, self.chips))
                return ("fold", 0)
            else:
                # Weak hand: usually fold unless pot odds are amazing
                if pot_odds < 0.15 or random.random() < bluff_rate:
                    return ("call", min(call_amount, self.chips))
                return ("fold", 0)

        # Default: call if affordable, otherwise fold
        if call_amount <= self.chips:
            return ("call", min(call_amount, self.chips))
        return ("fold", 0)

    def _evaluate_preflop_hand(self) -> float:
        """Evaluate pre-flop hand strength (0-1)."""
        if len(self.hand) != 2:
            return 0.3

        card1, card2 = self.hand
        rank1, rank2 = card1.rank.value, card2.rank.value

        # Pair
        if rank1 == rank2:
            return 0.5 + (rank1 / 28.0)  # Higher pairs are better

        # High cards
        high = max(rank1, rank2)
        low = min(rank1, rank2)

        # Suited
        suited_bonus = 0.1 if card1.suit == card2.suit else 0

        # Connected (potential straight)
        connected_bonus = 0.05 if abs(rank1 - rank2) <= 2 else 0

        # Base strength on high card
        base_strength = (high / 28.0) + (low / 56.0)

        return min(1.0, base_strength + suited_bonus + connected_bonus)
