# Bot AI Decision-Making Process

## Overview
The poker bots use a combination of hand strength evaluation, pot odds calculation, and difficulty-based behavioral patterns to make decisions.

## Decision Process (player.py:63-160)

### 1. Hand Strength Evaluation

**Pre-flop (before community cards):**
- Evaluates pocket cards using `_evaluate_preflop_hand()` (player.py:162-182)
- Considers:
  - **Pairs**: Strength = 0.5 + (rank/28) - Higher pairs are stronger
  - **High cards**: Base strength from high card rank
  - **Suited bonus**: +0.1 if both cards same suit
  - **Connected bonus**: +0.05 if cards are close (potential straight)

**Post-flop (with community cards):**
- Uses full hand evaluator to rank hand (pair, two pair, straight, etc.)
- Normalizes to 0-1 scale (hand_rank / 10.0)

### 2. Difficulty Adjustments (player.py:87-108)

**Easy Bots:**
- Hand strength multiplied by 0.8 (overestimates weak hands)
- Aggression: 0.3 (passive)
- Bluff rate: 0.05 (rarely bluffs)
- Pre-flop: Even more passive (aggression × 0.4, bluff × 0.3)

**Medium Bots:**
- Hand strength × 1.0 (accurate assessment)
- Aggression: 0.5 (balanced)
- Bluff rate: 0.15 (moderate bluffing)
- Pre-flop: Reduced aggression (aggression × 0.4, bluff × 0.3)

**Hard Bots:**
- Hand strength × 1.1 (slightly optimistic but smart)
- Aggression: 0.7 (aggressive)
- Bluff rate: 0.25 (bluffs frequently)
- Pre-flop: Still aggressive but measured (aggression × 0.4, bluff × 0.3)

### 3. Decision Logic (player.py:115-160)

Bots calculate **pot odds**: `call_amount / (pot + call_amount)`

#### Weak Hand (< 0.3)
- **If no bet to call (call_amount == 0):**
  - Sometimes bluff-bet: `random() < bluff_rate × aggression`
  - Otherwise check
- **If facing a bet:**
  - Fold if pot odds > 0.4 (bad odds)
  - Occasionally bluff call: `random() < bluff_rate`
  - Usually fold

#### Medium Hand (0.3 - 0.65)
- **If no bet:**
  - Sometimes bet for value: `random() < aggression × 0.6`
  - Bet size: 40-70% of pot
  - Otherwise check
- **If facing a bet:**
  - Call if bet is small (≤ 30% of stack)
  - Otherwise fold

#### Strong Hand (≥ 0.65)
- **If no bet:**
  - Usually bet (85% of time)
  - Bet size: 50-120% of pot
  - Occasionally slow-play (check to trap)
- **If facing a bet:**
  - Decide to raise: `random() < aggression`
  - Raise size: 60-150% of pot
  - Otherwise call

### 4. Randomness & Unpredictability

- Small random adjustment to hand strength: ±0.08 to ±0.15 depending on difficulty
- This prevents bots from being perfectly predictable
- Harder bots have less randomness (more consistent play)

## Example Scenarios

### Scenario 1: Easy Bot with Pair of 7s Pre-flop
1. Hand strength: 0.5 + (7/28) = 0.75
2. Difficulty adjustment: 0.75 × 0.8 = 0.6
3. Pre-flop reduction: 0.6 × 0.85 = 0.51
4. Randomness: ±0.15 → Final: ~0.36-0.66
5. Decision: Likely checks/calls, rarely raises (aggression only 0.3 × 0.4 = 0.12)

### Scenario 2: Hard Bot with Ace-King Suited Pre-flop
1. Hand strength: (14/28) + (13/56) + 0.1 (suited) + 0.05 (connected) = 0.88
2. Difficulty adjustment: 0.88 × 1.1 = 0.97 → capped at 0.95
3. Pre-flop reduction: 0.95 × 0.85 = 0.81
4. Randomness: ±0.08 → Final: ~0.73-0.89
5. Decision: Strong hand - will bet/raise aggressively (aggression 0.7 × 0.4 = 0.28, still reasonable)

### Scenario 3: Medium Bot with Flush Draw on Flop
1. Hand rank ~4-5 (depending on high card)
2. Hand strength: 0.4-0.5
3. No pre-flop reduction (we're past flop)
4. Decision: Medium hand territory - might bet for semi-bluff or call reasonable bets
5. Considers pot odds if facing bet

## Why Bots Behave Realistically

1. **Pre-flop caution**: All bots are 60% less aggressive pre-flop, mimicking real players who play tight early
2. **Position awareness**: Built into betting order (UTG, button, blinds)
3. **Pot odds consideration**: Won't chase bad odds (usually)
4. **Bluffing**: All difficulties bluff occasionally, more so on higher difficulty
5. **Hand reading**: Implicitly evaluates current bet size relative to pot
6. **Randomness**: Doesn't play perfectly every time

## Weaknesses (Room for Improvement)

- Doesn't track opponent behavior/patterns
- No concept of table image or player history
- Doesn't adjust to opponent tendencies
- Position play could be more sophisticated
- No range-based thinking (just evaluates own hand)
