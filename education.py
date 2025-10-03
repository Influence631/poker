"""Educational component for poker learning."""
from typing import List, Dict, Optional, Tuple
from poker_cards import Card, Rank, Suit
from hand_evaluator import HandEvaluator
import re


class PokerEducation:
    """Handles educational questions and answer evaluation."""

    @staticmethod
    def calculate_pot_odds(pot: int, bet_to_call: int) -> Tuple[float, str]:
        """
        Calculate pot odds as a ratio (Avi Rubin style).
        Returns (ratio_value, ratio_string) e.g., (3.0, "3:1")
        """
        if bet_to_call == 0:
            return (0.0, "0:1")
        ratio = pot / bet_to_call
        # Format as X:1 or X.Y:1
        if ratio >= 10:
            ratio_str = f"{ratio:.0f}:1"
        else:
            ratio_str = f"{ratio:.1f}:1"
        return (ratio, ratio_str)

    @staticmethod
    def calculate_outs(player_hand: List[Card], community_cards: List[Card],
                      known_cards: List[Card] = None) -> Dict[str, List[Card]]:
        """Calculate outs and return them categorized by improvement type."""
        if known_cards is None:
            known_cards = []
        return HandEvaluator.calculate_outs(player_hand, community_cards, known_cards)

    @staticmethod
    def count_total_outs(outs_dict: Dict[str, List[Card]]) -> int:
        """Count total number of outs."""
        return sum(len(cards) for cards in outs_dict.values())

    @staticmethod
    def calculate_equity(outs: int, num_community_cards: int) -> Tuple[float, str]:
        """
        Calculate win odds as a ratio (Avi Rubin style).
        Uses the formula: (52 - known_cards - outs) : outs
        Returns (ratio_value, ratio_string) e.g., (4.6, "4.6:1")
        """
        # Known cards = 2 hole + community cards
        known_cards = 2 + num_community_cards
        unknown_cards = 52 - known_cards

        if outs == 0:
            return (999.0, "999:1")  # Essentially impossible

        # Cards that don't help : cards that help
        losing_cards = unknown_cards - outs
        ratio = losing_cards / outs

        # Format as X:1 or X.Y:1
        if ratio >= 10:
            ratio_str = f"{ratio:.0f}:1"
        else:
            ratio_str = f"{ratio:.1f}:1"

        return (ratio, ratio_str)

    @staticmethod
    def evaluate_answer(question_type: str, user_answer: str, correct_answer: any,
                       tolerance: float = 1.0) -> Tuple[bool, str]:
        """
        Evaluate user's answer.
        Returns (is_correct, feedback_message)
        """
        user_answer = user_answer.strip().lower()

        if question_type == "pot_odds":
            # Extract ratio from answer (e.g., "3:1" or "3.5:1")
            correct_ratio, correct_str = correct_answer
            user_ratio = PokerEducation._extract_ratio(user_answer)

            if user_ratio is None:
                return (False, f"Invalid answer format. Please provide a ratio like '3:1' or '3.5:1'")

            is_correct = abs(user_ratio - correct_ratio) <= tolerance

            if is_correct:
                return (True, f"Correct! The pot odds are {correct_str}")
            else:
                return (False, f"Not quite. The pot odds are {correct_str}. "
                              f"Formula: pot / bet to call")

        elif question_type == "outs":
            correct_count = correct_answer
            user_value = PokerEducation._extract_number(user_answer)

            if user_value is None:
                return (False, f"Invalid answer format. Please provide a number.")

            is_correct = user_value == correct_count

            if is_correct:
                return (True, f"Correct! You have {correct_count} outs.")
            else:
                return (False, f"Not quite. You have {correct_count} outs.")

        elif question_type == "win_odds":
            # Win odds as a ratio (like 4.6:1)
            correct_ratio, correct_str = correct_answer
            user_ratio = PokerEducation._extract_ratio(user_answer)

            if user_ratio is None:
                return (False, f"Invalid answer format. Please provide a ratio like '4:1' or '4.6:1'")

            is_correct = abs(user_ratio - correct_ratio) <= tolerance

            if is_correct:
                return (True, f"Correct! Your odds to win are {correct_str}")
            else:
                return (False, f"Not quite. Your odds to win are {correct_str}. "
                              f"Formula: (unknown cards - outs) / outs")

        elif question_type == "hand_strength":
            correct_name = correct_answer.lower()
            is_correct = correct_name in user_answer

            if is_correct:
                return (True, f"Correct! You have {correct_answer}.")
            else:
                return (False, f"Not quite. You have {correct_answer}.")

        return (False, "Unknown question type")

    @staticmethod
    def _extract_number(text: str) -> Optional[float]:
        """Extract a number from text, including evaluating equations."""
        # Remove common words
        text = text.replace("percent", "").replace("%", "").replace("outs", "").strip()

        # Try to evaluate as a mathematical expression
        try:
            # Only allow safe mathematical operations
            allowed_chars = set('0123456789+-*/(). ')
            if all(c in allowed_chars for c in text):
                result = eval(text, {"__builtins__": {}}, {})
                if isinstance(result, (int, float)):
                    return float(result)
        except:
            pass

        # Try to find a single number
        match = re.search(r'-?\d+\.?\d*', text)
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
        return None

    @staticmethod
    def _extract_ratio(text: str) -> Optional[float]:
        """Extract a ratio from text (e.g., '3:1' or '3.5:1')."""
        # Look for pattern like "3:1" or "3.5:1"
        match = re.search(r'(\d+\.?\d*)\s*:\s*1', text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None

        # Also try just a number
        return PokerEducation._extract_number(text)

    @staticmethod
    def get_out_cards_display(outs_dict: Dict[str, List[Card]]) -> str:
        """Get a formatted string displaying all out cards, organized by rank and suit."""
        if not outs_dict:
            return "No outs available (you likely have a strong hand already!)"

        result = []
        for improvement, cards in outs_dict.items():
            result.append(f"\n[bold]{improvement}[/bold] ({len(cards)} outs):")

            # Group cards by rank
            from collections import defaultdict
            by_rank = defaultdict(list)
            for card in cards:
                by_rank[card.rank.display].append(card.suit.value)

            # Sort ranks by value (descending)
            sorted_ranks = sorted(by_rank.items(),
                                key=lambda x: next(r for r in cards if r.rank.display == x[0]).rank.value,
                                reverse=True)

            for rank, suits in sorted_ranks:
                suits_str = ", ".join(suits)
                result.append(f"  {rank}: {suits_str}")

        return "\n".join(result)

    @staticmethod
    def should_call_based_on_odds(pot_odds_ratio: float, win_odds_ratio: float) -> bool:
        """
        Determine if calling is profitable based on Avi Rubin style odds comparison.
        If pot odds > win odds, then calling is profitable.
        E.g., pot odds 5:1, win odds 4:1 -> 5 > 4, profitable!
        """
        return pot_odds_ratio > win_odds_ratio

    @staticmethod
    def get_recommendation(pot_odds_ratio: float, win_odds_ratio: float, pot_odds_str: str,
                          win_odds_str: str, hand_strength: int) -> str:
        """Get a recommendation for the player."""
        from hand_evaluator import HandRank

        if hand_strength >= HandRank.THREE_OF_A_KIND:
            return "You have a strong hand! Consider betting or raising."

        if pot_odds_ratio > win_odds_ratio:
            return (f"Good pot odds! Pot odds ({pot_odds_str}) > Win odds ({win_odds_str}). "
                   f"Calling is profitable!")
        elif pot_odds_ratio > win_odds_ratio * 0.9:
            return (f"Close odds. Pot odds ({pot_odds_str}) ≈ Win odds ({win_odds_str}). "
                   f"Marginal call.")
        else:
            return (f"Poor pot odds. Pot odds ({pot_odds_str}) < Win odds ({win_odds_str}). "
                   f"Consider folding.")
