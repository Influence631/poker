# Poker Learning Game

An educational poker game built in Python that helps players learn poker concepts through interactive questions.

## Features

- **Single Player vs AI Bots**: Play Texas Hold'em against 3 AI opponents
- **Educational Questions**: Answer questions about pot odds, outs, and equity before making decisions
- **Visual UI**: Beautiful command-line interface using the Rich library
- **Token Store**: Get free chips from the store when you run low
- **Persistent Progress**: Your chips are saved between sessions
- **Full Poker Rules**: Proper betting rounds, blinds, and hand evaluation

## Installation

1. Install Python 3.7 or higher
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. **(Optional)** For LLM-powered evaluation, set your Anthropic API key:
```bash
# Windows
set ANTHROPIC_API_KEY=your_api_key_here

# Linux/Mac
export ANTHROPIC_API_KEY=your_api_key_here
```

Get your API key from: https://console.anthropic.com/

## Running the Game

```bash
python main.py
```

## How to Play

1. **Main Menu**: Choose from playing poker, visiting the store, viewing stats, or exiting
2. **Store**: Get free chips when you need them
3. **Poker Game**:
   - Play Texas Hold'em against AI bots
   - After the flop, answer educational questions about:
     - Pot odds: Calculate the ratio of bet to pot
     - Outs: Count cards that improve your hand
     - Equity: Estimate your win probability
   - Make betting decisions (fold, check, call, raise)
   - Win chips by having the best hand!

## Game Controls

- Use number keys to select menu options
- Type answers to educational questions
- Enter betting amounts when raising
- Follow on-screen prompts

## Educational Component

The game helps you learn poker by asking questions before key decisions:

- **Pot Odds**: Calculate as a ratio (e.g., 3:1) - Avi Rubin style
- **Outs**: Count cards that improve your hand (considers opponent hands)
- **Win Odds**: Calculate odds to win as a ratio (e.g., 4.6:1)
- **LLM Evaluation**: AI professor evaluates your reasoning, not just numbers
- **Interactive Tutor**: Ask follow-up questions about the hand

### Advanced Features:
- Answer with equations (e.g., "3 + 4 + 2" for 9 outs)
- Provide reasoning (e.g., "5, because opponent might have flush")
- LLM considers your strategic thinking about opponent hands
- Two-stage LLM evaluation: evaluator + judge for accuracy
- Interactive chat to discuss hands and strategy

When you answer incorrectly, the game shows:
1. The correct answer with calculations
2. Detailed breakdown of outs (organized by rank and suit)
3. AI reasoning about why your answer is right/wrong
4. Option to chat with poker tutor about the hand

## Testing

Run the test suite:
```bash
python test_poker.py
```

All 25 tests should pass, covering:
- Card and deck functionality
- Hand evaluation (all poker hands)
- Player and AI bot behavior
- Game flow and betting rounds

## File Structure

- `main.py` - Main game controller
- `poker_game.py` - Game logic and flow
- `poker_cards.py` - Card and deck classes
- `hand_evaluator.py` - Hand ranking evaluation
- `player.py` - Player and AI bot classes
- `education.py` - Educational questions and answer evaluation
- `ui.py` - Visual interface using Rich library
- `test_poker.py` - Comprehensive test suite
- `player_data.json` - Saved player progress (auto-generated)

## Credits

Built with Python and the Rich library for beautiful terminal output.
