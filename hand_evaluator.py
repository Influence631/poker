"""Poker hand evaluation logic."""
from typing import List, Tuple, Dict
from collections import Counter
from poker_cards import Card, Rank


class HandRank:
    """Hand ranking constants."""
    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10

    NAMES = {
        1: "High Card",
        2: "Pair",
        3: "Two Pair",
        4: "Three of a Kind",
        5: "Straight",
        6: "Flush",
        7: "Full House",
        8: "Four of a Kind",
        9: "Straight Flush",
        10: "Royal Flush"
    }


class HandEvaluator:
    """Evaluates poker hands."""

    @staticmethod
    def evaluate_hand(cards: List[Card]) -> Tuple[int, List[int]]:
        """
        Evaluate a poker hand.
        Returns (hand_rank, tiebreakers) where tiebreakers are in descending priority.
        """
        if len(cards) < 5:
            raise ValueError("Need at least 5 cards to evaluate hand")

        # For hands with more than 5 cards, find the best 5-card combination
        if len(cards) > 5:
            return HandEvaluator._best_five_card_hand(cards)

        ranks = sorted([card.rank.value for card in cards], reverse=True)
        suits = [card.suit for card in cards]
        rank_counts = Counter(ranks)

        is_flush = len(set(suits)) == 1
        is_straight = HandEvaluator._is_straight(ranks)

        # Check for Royal Flush
        if is_flush and is_straight and min(ranks) == 10:
            return (HandRank.ROYAL_FLUSH, [14])

        # Check for Straight Flush
        if is_flush and is_straight:
            return (HandRank.STRAIGHT_FLUSH, [max(ranks)])

        # Check for Four of a Kind
        if 4 in rank_counts.values():
            quad = [r for r, c in rank_counts.items() if c == 4][0]
            kicker = [r for r, c in rank_counts.items() if c == 1][0]
            return (HandRank.FOUR_OF_A_KIND, [quad, kicker])

        # Check for Full House
        if 3 in rank_counts.values() and 2 in rank_counts.values():
            trips = [r for r, c in rank_counts.items() if c == 3][0]
            pair = [r for r, c in rank_counts.items() if c == 2][0]
            return (HandRank.FULL_HOUSE, [trips, pair])

        # Check for Flush
        if is_flush:
            return (HandRank.FLUSH, ranks)

        # Check for Straight
        if is_straight:
            return (HandRank.STRAIGHT, [max(ranks)])

        # Check for Three of a Kind
        if 3 in rank_counts.values():
            trips = [r for r, c in rank_counts.items() if c == 3][0]
            kickers = sorted([r for r, c in rank_counts.items() if c == 1], reverse=True)
            return (HandRank.THREE_OF_A_KIND, [trips] + kickers)

        # Check for Two Pair
        pairs = [r for r, c in rank_counts.items() if c == 2]
        if len(pairs) == 2:
            pairs.sort(reverse=True)
            kicker = [r for r, c in rank_counts.items() if c == 1][0]
            return (HandRank.TWO_PAIR, pairs + [kicker])

        # Check for Pair
        if 2 in rank_counts.values():
            pair = [r for r, c in rank_counts.items() if c == 2][0]
            kickers = sorted([r for r, c in rank_counts.items() if c == 1], reverse=True)
            return (HandRank.PAIR, [pair] + kickers)

        # High Card
        return (HandRank.HIGH_CARD, ranks)

    @staticmethod
    def _is_straight(ranks: List[int]) -> bool:
        """Check if ranks form a straight."""
        sorted_ranks = sorted(set(ranks))
        if len(sorted_ranks) != 5:
            return False

        # Check for regular straight
        if sorted_ranks[-1] - sorted_ranks[0] == 4:
            return True

        # Check for A-2-3-4-5 (wheel)
        if sorted_ranks == [2, 3, 4, 5, 14]:
            return True

        return False

    @staticmethod
    def _best_five_card_hand(cards: List[Card]) -> Tuple[int, List[int]]:
        """Find the best 5-card hand from 6 or 7 cards."""
        from itertools import combinations

        best_rank = 0
        best_tiebreakers = []

        for combo in combinations(cards, 5):
            rank, tiebreakers = HandEvaluator.evaluate_hand(list(combo))
            if rank > best_rank or (rank == best_rank and tiebreakers > best_tiebreakers):
                best_rank = rank
                best_tiebreakers = tiebreakers

        return (best_rank, best_tiebreakers)

    @staticmethod
    def compare_hands(hand1: List[Card], hand2: List[Card]) -> int:
        """
        Compare two hands.
        Returns: 1 if hand1 wins, -1 if hand2 wins, 0 if tie.
        """
        rank1, tie1 = HandEvaluator.evaluate_hand(hand1)
        rank2, tie2 = HandEvaluator.evaluate_hand(hand2)

        if rank1 > rank2:
            return 1
        elif rank1 < rank2:
            return -1
        else:
            if tie1 > tie2:
                return 1
            elif tie1 < tie2:
                return -1
            else:
                return 0

    @staticmethod
    def get_hand_name(cards: List[Card]) -> str:
        """Get the name of the hand."""
        rank, _ = HandEvaluator.evaluate_hand(cards)
        return HandRank.NAMES[rank]

    @staticmethod
    def calculate_outs(player_cards: List[Card], community_cards: List[Card],
                       known_cards: List[Card]) -> Dict[str, List[Card]]:
        """
        Calculate outs for improving the hand.
        Returns a dict mapping improvement types to lists of out cards.
        """
        from poker_cards import Deck, Suit, Rank

        # Get all unknown cards
        all_known = set(player_cards + community_cards + known_cards)
        deck_cards = [Card(rank, suit) for suit in Suit for rank in Rank]
        unknown_cards = [c for c in deck_cards if c not in all_known]

        current_hand = player_cards + community_cards
        current_rank, _ = HandEvaluator.evaluate_hand(current_hand) if len(current_hand) >= 5 else (0, [])

        outs = {}

        for card in unknown_cards:
            test_hand = current_hand + [card]
            if len(test_hand) >= 5:
                new_rank, _ = HandEvaluator.evaluate_hand(test_hand)
                if new_rank > current_rank:
                    improvement = HandRank.NAMES[new_rank]
                    if improvement not in outs:
                        outs[improvement] = []
                    outs[improvement].append(card)

        return outs
