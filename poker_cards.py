"""Poker card and deck implementation."""
import random
from enum import Enum
from typing import List, Tuple


class Suit(Enum):
    """Card suits."""
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"


class Rank(Enum):
    """Card ranks."""
    TWO = (2, "2")
    THREE = (3, "3")
    FOUR = (4, "4")
    FIVE = (5, "5")
    SIX = (6, "6")
    SEVEN = (7, "7")
    EIGHT = (8, "8")
    NINE = (9, "9")
    TEN = (10, "10")
    JACK = (11, "J")
    QUEEN = (12, "Q")
    KING = (13, "K")
    ACE = (14, "A")

    def __init__(self, num_value: int, display: str):
        self._num_value = num_value
        self._display = display

    @property
    def value(self):
        return self._num_value

    @property
    def display(self):
        return self._display


class Card:
    """Represents a playing card."""

    def __init__(self, rank: Rank, suit: Suit):
        self.rank = rank
        self.suit = suit

    def __str__(self) -> str:
        return f"{self.rank.display}{self.suit.value}"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self) -> int:
        return hash((self.rank, self.suit))


class Deck:
    """Represents a deck of cards."""

    def __init__(self):
        self.cards: List[Card] = []
        self.reset()

    def reset(self):
        """Reset and shuffle the deck."""
        self.cards = [Card(rank, suit) for suit in Suit for rank in Rank]
        self.shuffle()

    def shuffle(self):
        """Shuffle the deck."""
        random.shuffle(self.cards)

    def deal(self, num_cards: int = 1) -> List[Card]:
        """Deal cards from the deck."""
        if num_cards > len(self.cards):
            raise ValueError("Not enough cards in deck")
        dealt = self.cards[:num_cards]
        self.cards = self.cards[num_cards:]
        return dealt

    def __len__(self) -> int:
        return len(self.cards)
