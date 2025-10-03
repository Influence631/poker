"""Advanced bot intelligence using Claude API for strategic decision making."""
import os
from typing import List, Tuple, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if Anthropic API is available
try:
    import anthropic
    ANTHROPIC_AVAILABLE = bool(os.getenv("ANTHROPIC_API_KEY"))
except ImportError:
    ANTHROPIC_AVAILABLE = False


class ClaudePokerAdvisor:
    """Uses Claude API to provide strategic poker advice."""

    def __init__(self):
        self.client = None
        if ANTHROPIC_AVAILABLE:
            try:
                self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            except Exception as e:
                print(f"Warning: Could not initialize Anthropic client: {e}")
                self.client = None

    def get_decision(self, game_state: dict, difficulty: str) -> Optional[Tuple[str, int]]:
        """
        Get a strategic decision from Claude API.

        Args:
            game_state: Dictionary containing:
                - hand: List of card strings (e.g., ["A♠", "K♠"])
                - community_cards: List of community card strings
                - pot: Current pot size
                - current_bet: Current bet to call
                - player_bet: Player's current bet
                - chips: Player's remaining chips
                - min_raise: Minimum raise amount
                - opponents: Number of active opponents
            difficulty: "easy", "medium", or "hard"

        Returns:
            Tuple of (action, amount) or None if API unavailable
            action: "fold", "call", "check", or "raise"
            amount: bet/raise amount (0 for fold/call/check)
        """
        if not self.client:
            return None

        # Select model based on difficulty
        if difficulty == "easy":
            model = "claude-3-5-haiku-20241022"  # Cheaper, faster model for easy
            temperature = 0.3
        elif difficulty == "medium":
            model = "claude-sonnet-4-20250514"  # Sonnet 4 for medium
            temperature = 0.5
        else:  # hard
            model = "claude-sonnet-4-20250514"  # Sonnet 4 for hard
            temperature = 0.7

        # Build the prompt based on difficulty
        prompt = self._build_prompt(game_state, difficulty)

        try:
            # Call Claude API
            message = self.client.messages.create(
                model=model,
                max_tokens=200,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse the response
            response_text = message.content[0].text.strip()
            return self._parse_response(response_text, game_state)

        except Exception as e:
            print(f"Claude API error: {e}")
            return None

    def _build_prompt(self, game_state: dict, difficulty: str) -> str:
        """Build a prompt for Claude based on game state and difficulty."""
        hand = ", ".join(game_state["hand"])
        community = ", ".join(game_state["community_cards"]) if game_state["community_cards"] else "None"
        pot = game_state["pot"]
        current_bet = game_state["current_bet"]
        player_bet = game_state["player_bet"]
        chips = game_state["chips"]
        min_raise = game_state["min_raise"]
        call_amount = current_bet - player_bet
        opponents = game_state["opponents"]

        # Calculate pot odds
        pot_after_call = pot + call_amount if call_amount > 0 else pot
        pot_odds = f"{pot_after_call / call_amount:.1f}:1" if call_amount > 0 else "N/A"

        # Difficulty-specific personality and skill level
        if difficulty == "easy":
            personality = """You are a BEGINNER poker player with LIMITED poker knowledge:
- You play very cautiously and passively
- You mostly play only premium hands (pairs 9+, AK, AQ)
- You rarely bluff or make aggressive plays
- You often fold to any significant bet
- You don't understand advanced concepts like implied odds or position
- You call too much with weak hands when pot odds are bad
- You're risk-averse and prefer to see cheap flops"""

        elif difficulty == "medium":
            personality = """You are an INTERMEDIATE poker player with SOLID fundamentals:
- You understand and apply pot odds and hand equity
- You play a balanced range based on position
- You can semi-bluff with drawing hands
- You adjust bet sizing based on hand strength and board texture
- You recognize obvious patterns but miss subtle tells
- You play ABC poker - straightforward and predictable
- You understand when to value bet and when to fold"""

        else:  # hard
            personality = """You are an ADVANCED poker player with EXPERT-level skills:
- You expertly calculate pot odds, implied odds, and fold equity
- You use position aggressively and apply maximum pressure
- You recognize board textures and adjust strategy accordingly
- You balance your ranges to remain unpredictable
- You bluff strategically with blockers and good timing
- You thin value bet and can make hero calls/folds
- You exploit opponent tendencies and adjust dynamically
- You understand ICM, range advantage, and advanced concepts"""

        prompt = f"""{personality}

Current poker situation:
- Your hand: {hand}
- Community cards: {community}
- Pot: ${pot}
- Current bet: ${current_bet}
- Your current bet: ${player_bet}
- Amount to call: ${call_amount}
- Your chips: ${chips}
- Pot odds: {pot_odds}
- Minimum raise: ${min_raise}
- Active opponents: {opponents}

Analyze this situation and decide your action. Consider:
1. Hand strength and potential
2. Pot odds and implied odds
3. Position and opponent behavior
4. Your table image and strategy

Respond with ONLY one line in this exact format:
ACTION: [fold/call/check/raise] AMOUNT: [number]

Examples:
- "ACTION: fold AMOUNT: 0"
- "ACTION: call AMOUNT: 0"
- "ACTION: raise AMOUNT: 50"
- "ACTION: check AMOUNT: 0"
"""
        return prompt

    def _parse_response(self, response: str, game_state: dict) -> Tuple[str, int]:
        """Parse Claude's response into action and amount."""
        try:
            # Extract action and amount from response
            lines = response.upper().split('\n')
            action_line = None

            for line in lines:
                if 'ACTION:' in line:
                    action_line = line
                    break

            if not action_line:
                return ("check", 0)  # Default safe action

            # Parse action
            action_part = action_line.split('ACTION:')[1].split('AMOUNT:')[0].strip().lower()

            # Validate action
            if action_part not in ["fold", "call", "check", "raise"]:
                action_part = "check"

            # Parse amount
            amount = 0
            if 'AMOUNT:' in action_line:
                amount_str = action_line.split('AMOUNT:')[1].strip()
                try:
                    amount = int(''.join(filter(str.isdigit, amount_str)))
                except:
                    amount = 0

            # Validate amount
            chips = game_state["chips"]
            min_raise = game_state["min_raise"]
            call_amount = game_state["current_bet"] - game_state["player_bet"]

            if action_part == "raise":
                # Ensure raise amount is valid
                if amount < min_raise:
                    amount = min_raise
                if call_amount + amount > chips:
                    amount = chips - call_amount
                if amount <= 0:
                    action_part = "call" if call_amount > 0 else "check"
                    amount = 0

            return (action_part, amount)

        except Exception as e:
            print(f"Error parsing Claude response: {e}")
            return ("check", 0)  # Safe fallback


# Global instance
_advisor = None


def get_claude_decision(game_state: dict, difficulty: str) -> Optional[Tuple[str, int]]:
    """Get a decision from Claude API (singleton pattern)."""
    global _advisor
    if _advisor is None:
        _advisor = ClaudePokerAdvisor()
    return _advisor.get_decision(game_state, difficulty)


def is_claude_available() -> bool:
    """Check if Claude API is available."""
    return ANTHROPIC_AVAILABLE
