"""Test suite for poker game."""
import unittest
from poker_cards import Card, Deck, Rank, Suit
from hand_evaluator import HandEvaluator, HandRank
from player import Player, AIBot
from poker_game import PokerGame


class TestPokerCards(unittest.TestCase):
    """Test poker cards and deck."""

    def test_card_creation(self):
        """Test card creation."""
        card = Card(Rank.ACE, Suit.SPADES)
        self.assertEqual(card.rank, Rank.ACE)
        self.assertEqual(card.suit, Suit.SPADES)
        self.assertEqual(str(card), "A♠")

    def test_deck_creation(self):
        """Test deck has 52 cards."""
        deck = Deck()
        self.assertEqual(len(deck), 52)

    def test_deck_deal(self):
        """Test dealing cards."""
        deck = Deck()
        cards = deck.deal(5)
        self.assertEqual(len(cards), 5)
        self.assertEqual(len(deck), 47)


class TestHandEvaluator(unittest.TestCase):
    """Test hand evaluation."""

    def test_royal_flush(self):
        """Test royal flush detection."""
        cards = [
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.KING, Suit.HEARTS),
            Card(Rank.QUEEN, Suit.HEARTS),
            Card(Rank.JACK, Suit.HEARTS),
            Card(Rank.TEN, Suit.HEARTS)
        ]
        rank, _ = HandEvaluator.evaluate_hand(cards)
        self.assertEqual(rank, HandRank.ROYAL_FLUSH)

    def test_straight_flush(self):
        """Test straight flush detection."""
        cards = [
            Card(Rank.NINE, Suit.CLUBS),
            Card(Rank.EIGHT, Suit.CLUBS),
            Card(Rank.SEVEN, Suit.CLUBS),
            Card(Rank.SIX, Suit.CLUBS),
            Card(Rank.FIVE, Suit.CLUBS)
        ]
        rank, _ = HandEvaluator.evaluate_hand(cards)
        self.assertEqual(rank, HandRank.STRAIGHT_FLUSH)

    def test_four_of_a_kind(self):
        """Test four of a kind detection."""
        cards = [
            Card(Rank.KING, Suit.HEARTS),
            Card(Rank.KING, Suit.DIAMONDS),
            Card(Rank.KING, Suit.CLUBS),
            Card(Rank.KING, Suit.SPADES),
            Card(Rank.ACE, Suit.HEARTS)
        ]
        rank, _ = HandEvaluator.evaluate_hand(cards)
        self.assertEqual(rank, HandRank.FOUR_OF_A_KIND)

    def test_full_house(self):
        """Test full house detection."""
        cards = [
            Card(Rank.KING, Suit.HEARTS),
            Card(Rank.KING, Suit.DIAMONDS),
            Card(Rank.KING, Suit.CLUBS),
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.ACE, Suit.DIAMONDS)
        ]
        rank, _ = HandEvaluator.evaluate_hand(cards)
        self.assertEqual(rank, HandRank.FULL_HOUSE)

    def test_flush(self):
        """Test flush detection."""
        cards = [
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.KING, Suit.HEARTS),
            Card(Rank.NINE, Suit.HEARTS),
            Card(Rank.FIVE, Suit.HEARTS),
            Card(Rank.TWO, Suit.HEARTS)
        ]
        rank, _ = HandEvaluator.evaluate_hand(cards)
        self.assertEqual(rank, HandRank.FLUSH)

    def test_straight(self):
        """Test straight detection."""
        cards = [
            Card(Rank.NINE, Suit.HEARTS),
            Card(Rank.EIGHT, Suit.DIAMONDS),
            Card(Rank.SEVEN, Suit.CLUBS),
            Card(Rank.SIX, Suit.SPADES),
            Card(Rank.FIVE, Suit.HEARTS)
        ]
        rank, _ = HandEvaluator.evaluate_hand(cards)
        self.assertEqual(rank, HandRank.STRAIGHT)

    def test_three_of_a_kind(self):
        """Test three of a kind detection."""
        cards = [
            Card(Rank.KING, Suit.HEARTS),
            Card(Rank.KING, Suit.DIAMONDS),
            Card(Rank.KING, Suit.CLUBS),
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.QUEEN, Suit.DIAMONDS)
        ]
        rank, _ = HandEvaluator.evaluate_hand(cards)
        self.assertEqual(rank, HandRank.THREE_OF_A_KIND)

    def test_two_pair(self):
        """Test two pair detection."""
        cards = [
            Card(Rank.KING, Suit.HEARTS),
            Card(Rank.KING, Suit.DIAMONDS),
            Card(Rank.QUEEN, Suit.CLUBS),
            Card(Rank.QUEEN, Suit.HEARTS),
            Card(Rank.ACE, Suit.DIAMONDS)
        ]
        rank, _ = HandEvaluator.evaluate_hand(cards)
        self.assertEqual(rank, HandRank.TWO_PAIR)

    def test_pair(self):
        """Test pair detection."""
        cards = [
            Card(Rank.KING, Suit.HEARTS),
            Card(Rank.KING, Suit.DIAMONDS),
            Card(Rank.QUEEN, Suit.CLUBS),
            Card(Rank.JACK, Suit.HEARTS),
            Card(Rank.ACE, Suit.DIAMONDS)
        ]
        rank, _ = HandEvaluator.evaluate_hand(cards)
        self.assertEqual(rank, HandRank.PAIR)

    def test_high_card(self):
        """Test high card detection."""
        cards = [
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.KING, Suit.DIAMONDS),
            Card(Rank.NINE, Suit.CLUBS),
            Card(Rank.FIVE, Suit.HEARTS),
            Card(Rank.TWO, Suit.DIAMONDS)
        ]
        rank, _ = HandEvaluator.evaluate_hand(cards)
        self.assertEqual(rank, HandRank.HIGH_CARD)


class TestPlayer(unittest.TestCase):
    """Test player class."""

    def test_player_creation(self):
        """Test player creation."""
        player = Player("Test", 1000)
        self.assertEqual(player.name, "Test")
        self.assertEqual(player.chips, 1000)
        self.assertFalse(player.folded)

    def test_player_bet(self):
        """Test betting."""
        player = Player("Test", 1000)
        amount = player.bet(100)
        self.assertEqual(amount, 100)
        self.assertEqual(player.chips, 900)
        self.assertEqual(player.current_bet, 100)

    def test_player_all_in(self):
        """Test all-in."""
        player = Player("Test", 100)
        amount = player.bet(200)
        self.assertEqual(amount, 100)
        self.assertEqual(player.chips, 0)
        self.assertTrue(player.all_in)

    def test_player_fold(self):
        """Test folding."""
        player = Player("Test", 1000)
        player.fold()
        self.assertTrue(player.folded)

    def test_player_win(self):
        """Test winning."""
        player = Player("Test", 1000)
        player.win(500)
        self.assertEqual(player.chips, 1500)


class TestAIBot(unittest.TestCase):
    """Test AI bot."""

    def test_ai_creation(self):
        """Test AI bot creation."""
        bot = AIBot("Bot", 1000, "medium")
        self.assertEqual(bot.name, "Bot")
        self.assertEqual(bot.difficulty, "medium")

    def test_ai_makes_decision(self):
        """Test AI makes valid decisions."""
        bot = AIBot("Bot", 1000)
        bot.hand = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.KING, Suit.HEARTS)]

        action, amount = bot.make_decision(100, 0, [], 10)
        self.assertIn(action, ["fold", "call", "raise", "check"])


class TestPokerGame(unittest.TestCase):
    """Test poker game."""

    def test_game_creation(self):
        """Test game creation."""
        player = Player("Test", 1000)
        game = PokerGame(player, num_bots=2)
        self.assertEqual(len(game.all_players), 3)

    def test_start_new_hand(self):
        """Test starting new hand."""
        player = Player("Test", 1000)
        game = PokerGame(player, num_bots=2)
        success = game.start_new_hand()
        self.assertTrue(success)
        self.assertEqual(len(player.hand), 2)
        self.assertGreater(game.pot, 0)  # Blinds posted

    def test_deal_flop(self):
        """Test dealing flop."""
        player = Player("Test", 1000)
        game = PokerGame(player, num_bots=2)
        game.start_new_hand()
        game.deal_flop()
        self.assertEqual(len(game.community_cards), 3)

    def test_deal_turn(self):
        """Test dealing turn."""
        player = Player("Test", 1000)
        game = PokerGame(player, num_bots=2)
        game.start_new_hand()
        game.deal_flop()
        game.deal_turn()
        self.assertEqual(len(game.community_cards), 4)

    def test_deal_river(self):
        """Test dealing river."""
        player = Player("Test", 1000)
        game = PokerGame(player, num_bots=2)
        game.start_new_hand()
        game.deal_flop()
        game.deal_turn()
        game.deal_river()
        self.assertEqual(len(game.community_cards), 5)


if __name__ == "__main__":
    unittest.main()
