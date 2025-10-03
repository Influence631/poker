"""LLM-based answer evaluation with reasoning."""
from typing import Tuple, Dict, List
from poker_cards import Card
import json


class LLMEvaluator:
    """Uses LLM to evaluate poker answers with reasoning."""

    @staticmethod
    def evaluate_answer_with_llm(
        question_type: str,
        user_answer: str,
        correct_value: any,
        context: Dict
    ) -> Tuple[bool, str, str]:
        """
        Evaluate answer using LLM with multi-step reasoning.
        Returns (is_correct, feedback, reasoning)
        """
        # Import anthropic here to avoid dependency if not installed
        try:
            import anthropic
        except ImportError:
            return (False, "LLM evaluation not available. Install: pip install anthropic", "")

        import os
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return (False, "ANTHROPIC_API_KEY not set in environment", "")

        client = anthropic.Anthropic(api_key=api_key)

        # Build evaluation prompt
        if question_type == "outs":
            prompt = LLMEvaluator._build_outs_prompt(user_answer, correct_value, context)
        elif question_type == "pot_odds":
            prompt = LLMEvaluator._build_pot_odds_prompt(user_answer, correct_value, context)
        elif question_type == "win_odds":
            prompt = LLMEvaluator._build_win_odds_prompt(user_answer, correct_value, context)
        else:
            return (False, "Unknown question type", "")

        # First LLM: Evaluate the answer
        try:
            response1 = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            evaluation = response1.content[0].text

            # Second LLM: Judge the first LLM's evaluation
            judge_prompt = f"""You are a poker professor reviewing an evaluation. The student gave this answer:
"{user_answer}"

Another AI evaluated it as:
{evaluation}

Your task:
1. Verify the mathematical calculations are correct
2. Check if the reasoning about outs is sound (remember: outs that help opponent more than you should be reconsidered)
3. Provide final judgment: CORRECT or INCORRECT
4. Give concise feedback to the student

Context:
{json.dumps(context, indent=2)}

Respond in JSON format:
{{
    "is_correct": true/false,
    "feedback": "Brief feedback to student",
    "reasoning": "Your detailed reasoning"
}}"""

            response2 = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": judge_prompt}]
            )

            judge_text = response2.content[0].text

            # Parse JSON response
            # Extract JSON from response (might be wrapped in markdown)
            import re
            json_match = re.search(r'\{.*\}', judge_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return (
                    result.get("is_correct", False),
                    result.get("feedback", "Evaluation completed"),
                    result.get("reasoning", evaluation)
                )
            else:
                return (False, judge_text, evaluation)

        except Exception as e:
            return (False, f"LLM evaluation error: {str(e)}", "")

    @staticmethod
    def _build_outs_prompt(user_answer: str, correct_value: int, context: Dict) -> str:
        """Build prompt for outs evaluation."""
        player_hand = context.get("player_hand", [])
        community_cards = context.get("community_cards", [])
        outs_dict = context.get("outs_dict", {})

        hand_str = ", ".join(str(c) for c in player_hand)
        comm_str = ", ".join(str(c) for c in community_cards)

        outs_breakdown = ""
        for improvement, cards in outs_dict.items():
            cards_str = ", ".join(str(c) for c in cards)
            outs_breakdown += f"- {improvement}: {cards_str}\n"

        return f"""You are a poker professor evaluating a student's answer about OUTS.

CONTEXT:
- Player's hand: {hand_str}
- Community cards: {comm_str}
- Stage: {context.get('stage', 'Unknown')}

QUESTION: How many outs do you have?

CALCULATED OUTS (by simple counting): {correct_value}
Breakdown:
{outs_breakdown}

STUDENT'S ANSWER: "{user_answer}"

IMPORTANT CONSIDERATIONS:
1. The student may have given reasoning (e.g., "I think it's 5 because opponent might have a flush")
2. An "out" is only valid if it improves YOUR hand more than opponents
3. If the student suspects opponents have certain hands, some outs might not be real outs
4. The student should consider what hands opponents might have based on betting patterns
5. A card that completes your straight but gives opponent a flush is NOT a valid out

TASK:
1. Extract the number from the student's answer (may include math like "3+4")
2. Read their reasoning if provided
3. Evaluate if their reasoning about opponent hands is sound
4. If they reasoned well about opponents having better hands, they might be MORE correct than the simple count
5. Provide feedback that teaches proper out counting

Respond with detailed evaluation explaining whether their reasoning is sound."""

    @staticmethod
    def _build_pot_odds_prompt(user_answer: str, correct_value: Tuple[float, str], context: Dict) -> str:
        """Build prompt for pot odds evaluation."""
        pot = context.get("pot", 0)
        call_amount = context.get("call_amount", 0)
        ratio, ratio_str = correct_value

        return f"""You are a poker professor evaluating a student's answer about POT ODDS.

CONTEXT:
- Pot size: ${pot}
- Amount to call: ${call_amount}

QUESTION: What are the pot odds? (Format: X:1)

CORRECT ANSWER: {ratio_str}
Calculation: {pot} / {call_amount} = {ratio:.2f}:1

STUDENT'S ANSWER: "{user_answer}"

TASK:
1. Extract the ratio from their answer
2. Check if the calculation is correct (allow small rounding differences)
3. If they showed their work, verify it
4. Provide feedback

Respond with evaluation."""

    @staticmethod
    def _build_win_odds_prompt(user_answer: str, correct_value: Tuple[float, str], context: Dict) -> str:
        """Build prompt for win odds evaluation."""
        total_outs = context.get("total_outs", 0)
        unknown_cards = context.get("unknown_cards", 0)
        ratio, ratio_str = correct_value

        return f"""You are a poker professor evaluating a student's answer about WIN ODDS.

CONTEXT:
- Total outs: {total_outs}
- Unknown cards remaining: {unknown_cards}

QUESTION: What are your odds to win? (Format: X:1)

CORRECT ANSWER: {ratio_str}
Calculation: ({unknown_cards} - {total_outs}) / {total_outs} = {ratio:.2f}:1

STUDENT'S ANSWER: "{user_answer}"

TASK:
1. Extract the ratio from their answer
2. Check if the calculation is correct
3. If they showed their work, verify it
4. Provide feedback

Respond with evaluation."""

    @staticmethod
    def interactive_chat(context: Dict, ui) -> None:
        """Allow student to ask follow-up questions."""
        try:
            import anthropic
        except ImportError:
            ui.show_message("LLM chat not available. Install: pip install anthropic", "red")
            return

        import os
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            ui.show_message("ANTHROPIC_API_KEY not set in environment", "red")
            return

        client = anthropic.Anthropic(api_key=api_key)

        # Build context for the conversation
        player_hand = context.get("player_hand", [])
        community_cards = context.get("community_cards", [])
        outs_dict = context.get("outs_dict", {})

        hand_str = ", ".join(str(c) for c in player_hand)
        comm_str = ", ".join(str(c) for c in community_cards)

        system_prompt = f"""You are a helpful poker professor. The student just answered questions about this poker situation:

Player's hand: {hand_str}
Community cards: {comm_str}
Stage: {context.get('stage', 'Unknown')}

Available outs:
{json.dumps({k: [str(c) for c in v] for k, v in outs_dict.items()}, indent=2)}

Answer the student's questions about poker strategy, outs, odds, and hand evaluation. Be concise but thorough.
Remember: opponent's possible hands matter when counting outs!"""

        conversation = []

        ui.show_message("\n[bold cyan]═══ Poker Tutor Chat ═══[/bold cyan]", "")
        ui.show_message("[dim]Ask questions about this hand, or type 'exit' to continue playing[/dim]\n", "")

        while True:
            from rich.prompt import Prompt
            question = Prompt.ask("[cyan]You[/cyan]")

            if question.lower() in ["exit", "quit", "done", "continue"]:
                break

            conversation.append({"role": "user", "content": question})

            try:
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1500,
                    system=system_prompt,
                    messages=conversation
                )

                answer = response.content[0].text
                conversation.append({"role": "assistant", "content": answer})

                ui.show_message(f"[green]Tutor:[/green] {answer}\n", "")

            except Exception as e:
                ui.show_message(f"[red]Error: {str(e)}[/red]", "")
                break
