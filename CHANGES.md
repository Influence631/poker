# Changes Made to Fix Issues

## Issue #1: Store - Multiple Free Token Claims
**Problem:** Couldn't get free tokens multiple times, pressing 'y' would exit the store.

**Solution:**
- Changed store to loop until user chooses to exit
- Added explicit choices: y/n/exit
- Now you can claim $500 multiple times in one visit

**Files Modified:** `main.py`, `ui.py`

---

## Issue #2: Equation Answers
**Problem:** Couldn't answer with equations like "3 + 4 + 2"

**Solution:**
- Modified `_extract_number()` to safely evaluate mathematical expressions
- Supports +, -, *, /, parentheses
- Example: "3 + 4 + 2" = 9, "2 * 5" = 10

**Files Modified:** `education.py`

---

## Issue #3: Clearer Question Hints
**Problem:** Unclear what "by the FLOP" means - should I count outs for turn or both turn and river?

**Solution:**
- Added stage-specific question wording:
  - **Flop**: "How many outs do you have for the TURN card? (Count cards that would improve your hand on the next card)"
  - **Turn**: "How many outs do you have for the RIVER card? (Count cards that would improve your hand on the final card)"
  - **River**: "How many outs did you have? (This is for learning - the hand is complete)"
- Added clearer hints explaining what to count

**Files Modified:** `main.py`

---

## Issue #4: Outs Display Formatting
**Problem:** Outs displayed in long lines, hard to read:
```
Two Pair (9 outs): Q♥, 9♦, Q♦, A♦, 9♣, A♣, 9♠, Q♠, A♠
```

**Solution:**
- Organized outs by rank, then suit
- Display format:
```
Two Pair (9 outs):
  A: ♥, ♦, ♣, ♠
  Q: ♥, ♦, ♠
  9: ♦, ♣, ♠
```

**Files Modified:** `education.py`

---

## Issue #5: Outs Should Consider Opponent Hands
**Problem:** Simple counting doesn't account for opponents. A card that gives you a straight but gives opponent a flush shouldn't count as an out.

**Solution:**
- Integrated LLM evaluation system
- Two-stage evaluation:
  1. **Evaluator LLM**: Reads your answer and reasoning
  2. **Judge LLM**: Verifies calculations and strategic thinking
- Students can now explain reasoning:
  - Example: "5, because opponent might have flush"
  - LLM evaluates if the reasoning is sound
- Considers opponent ranges and betting patterns

**Files Created:** `llm_evaluator.py`, `SETUP.md`
**Files Modified:** `main.py`, `requirements.txt`, `README.md`

---

## Issue #6: Interactive Learning
**Problem:** Need ability to discuss hands and ask follow-up questions.

**Solution:**
- Added interactive poker tutor chat after each evaluation
- Prompt: "Want to discuss this hand with the poker tutor?"
- Can ask questions about:
  - Why certain cards are/aren't outs
  - Opponent hand ranges
  - Betting strategy
  - Hand evaluation
- Type 'exit' to continue playing

**Files Modified:** `llm_evaluator.py`, `main.py`

---

## Additional Improvements

### Pot Odds - Avi Rubin Style
- Changed from percentage (e.g., 33%) to ratio (e.g., 3:1)
- Follows Professor Avi Rubin's teaching method
- Formula: pot / bet to call

### Win Odds - Proper Calculation
- Uses formula: (unknown cards - outs) : outs
- Displayed as ratio (e.g., 4.6:1)
- Easier to compare with pot odds

### Visual Improvements
- Community cards now in large, highlighted boxes
- Shows stage clearly: FLOP, TURN, RIVER, PRE-FLOP
- Player hand cards in contrasting colors
- Bot actions display sequentially with 0.8s pause

### Game Flow
- Fixed continue prompt - "n" now properly exits
- Won't start new hand when you say no

---

## How to Use New Features

### Basic (Without LLM)
Everything works without API key:
- Answer with numbers or equations
- Get basic evaluation
- See formatted outs

### Advanced (With LLM)
Set `ANTHROPIC_API_KEY` environment variable:
- Answer with reasoning
- Get strategic feedback
- Chat with poker tutor
- Discuss opponent hands

See `SETUP.md` for detailed instructions.

---

## Testing

All 25 unit tests still pass:
```bash
python test_poker.py
```

Game is fully playable without LLM features.
