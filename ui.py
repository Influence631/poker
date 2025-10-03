"""Visual UI using rich library."""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.prompt import Prompt, IntPrompt, Confirm
from rich import box
from typing import List, Optional
from poker_cards import Card
from player import Player
from hand_evaluator import HandEvaluator


class PokerUI:
    """Handles all UI rendering and input."""

    def __init__(self):
        self.console = Console()

    def clear(self):
        """Clear the console."""
        self.console.clear()

    def show_title(self):
        """Show game title."""
        title = Text("POKER LEARNING GAME", style="bold magenta", justify="center")
        self.console.print(Panel(title, border_style="bright_blue"))
        self.console.print()

    def show_main_menu(self) -> str:
        """Show main menu and get user choice."""
        self.clear()
        self.show_title()

        menu_table = Table(show_header=False, box=box.ROUNDED, border_style="cyan")
        menu_table.add_column("Option", style="bold yellow")
        menu_table.add_column("Description")

        menu_table.add_row("1", "Play Poker")
        menu_table.add_row("2", "Visit Store")
        menu_table.add_row("3", "View Stats")
        menu_table.add_row("4", "Exit")

        self.console.print(menu_table)
        self.console.print()

        return Prompt.ask("Choose an option", choices=["1", "2", "3", "4"], default="1")

    def show_game_state(self, player: Player, all_players: List[Player],
                       community_cards: List[Card], pot: int, current_bet: int,
                       dealer_position: int):
        """Show current game state."""
        self.clear()
        self.show_title()

        # Community cards - Make them MUCH more visible
        if community_cards:
            # Create large, spaced out card display
            cards_display = "     ".join(f"[bold white on blue] {card} [/bold white on blue]" for card in community_cards)
            stage = ""
            if len(community_cards) == 3:
                stage = "FLOP"
            elif len(community_cards) == 4:
                stage = "TURN"
            elif len(community_cards) == 5:
                stage = "RIVER"

            self.console.print(Panel(
                f"[bold yellow]{stage}[/bold yellow]\n\n{cards_display}",
                title="[bold green]COMMUNITY CARDS[/bold green]",
                border_style="bright_green",
                padding=(1, 2)
            ))
        else:
            self.console.print(Panel(
                "[bold yellow]PRE-FLOP[/bold yellow]\n\n[dim]No community cards yet[/dim]",
                title="[bold green]COMMUNITY CARDS[/bold green]",
                border_style="green",
                padding=(1, 2)
            ))

        # Pot info
        pot_text = f"[bold yellow]Pot:[/bold yellow] ${pot}  [bold yellow]Current Bet:[/bold yellow] ${current_bet}"
        self.console.print(Panel(pot_text, border_style="yellow"))

        # Players
        player_table = Table(show_header=True, box=box.ROUNDED, border_style="blue")
        player_table.add_column("Player", style="bold")
        player_table.add_column("Chips", justify="right", style="green")
        player_table.add_column("Bet", justify="right", style="yellow")
        player_table.add_column("Status", style="cyan")

        for i, p in enumerate(all_players):
            status = ""
            if p.folded:
                status = "[bold red on white]FOLDED[/bold red on white]"
            elif p.all_in:
                status = "[magenta]All In[/magenta]"
            else:
                status = "[green]Active[/green]"

            if i == dealer_position:
                status += " [bold](D)[/bold]"

            name_style = "bold cyan" if p == player else ""
            player_name = f"[{name_style}]{p.name}[/{name_style}]" if name_style else p.name

            # Add FOLDED label to player name if they folded
            if p.folded:
                player_name = f"{player_name} [bold red]✗ FOLDED[/bold red]"

            player_table.add_row(
                player_name,
                f"${p.chips}",
                f"${p.current_bet}",
                status
            )

        self.console.print(player_table)
        self.console.print()

        # Player's hand - Make it more visible
        hand_cards = "     ".join(f"[bold black on white] {card} [/bold black on white]" for card in player.hand)
        if len(player.hand) == 2 and len(community_cards) >= 3:
            hand_name = HandEvaluator.get_hand_name(player.hand + community_cards)
            hand_info = f"{hand_cards}\n\n[dim]Current Hand: {hand_name}[/dim]"
        else:
            hand_info = hand_cards

        self.console.print(Panel(
            hand_info,
            title="[bold cyan]YOUR HAND[/bold cyan]",
            border_style="bright_cyan",
            padding=(1, 2)
        ))
        self.console.print()

    def ask_educational_question(self, question: str, hint: str = "") -> str:
        """Ask an educational question."""
        self.console.print(Panel(
            f"[bold yellow]Educational Question:[/bold yellow]\n{question}",
            border_style="yellow"
        ))

        if hint:
            self.console.print(f"[dim]Hint: {hint}[/dim]")

        return Prompt.ask("[cyan]Your answer[/cyan]")

    def show_feedback(self, is_correct: bool, feedback: str, show_outs: Optional[str] = None):
        """Show feedback on answer."""
        if is_correct:
            self.console.print(Panel(
                f"[bold green]✓ {feedback}[/bold green]",
                border_style="green"
            ))
        else:
            self.console.print(Panel(
                f"[bold red]✗ {feedback}[/bold red]",
                border_style="red"
            ))

        if show_outs:
            self.console.print(Panel(
                f"[yellow]Out Cards:[/yellow]\n{show_outs}",
                border_style="yellow"
            ))

        self.console.print()
        Prompt.ask("[dim]Press Enter to continue[/dim]", default="")

    def get_player_action(self, current_bet: int, player_bet: int, player_chips: int,
                         min_raise: int) -> tuple[str, int]:
        """Get player's betting action."""
        call_amount = current_bet - player_bet

        options = []
        if call_amount == 0:
            options.append("check")
            options.append("bet")
        else:
            options.append("fold")
            if call_amount <= player_chips:
                options.append("call")
            if player_chips > call_amount:
                options.append("raise")

        # Show options
        action_table = Table(show_header=False, box=box.ROUNDED, border_style="yellow")
        action_table.add_column("Action", style="bold")
        action_table.add_column("Description")

        if "fold" in options:
            action_table.add_row("fold", "Give up your hand")
        if "check" in options:
            action_table.add_row("check", "Pass the action (no bet)")
        if "call" in options:
            action_table.add_row("call", f"Match the current bet (${call_amount})")
        if "bet" in options:
            action_table.add_row("bet", "Make the first bet")
        if "raise" in options:
            action_table.add_row("raise", f"Increase the bet (min ${min_raise})")

        self.console.print(action_table)

        action = Prompt.ask("[bold cyan]Your action[/bold cyan]", choices=options)

        amount = 0
        if action == "call":
            amount = call_amount
        elif action == "bet" or action == "raise":
            max_bet = player_chips - (call_amount if action == "raise" else 0)
            min_bet = min_raise if action == "raise" else min_raise

            amount = IntPrompt.ask(
                f"[cyan]Enter amount[/cyan] (${min_bet} - ${max_bet})",
                default=min_bet
            )
            amount = max(min_bet, min(amount, max_bet))

        return (action, amount)

    def show_winners(self, winners: List[tuple[Player, int, str]]):
        """Show hand winners."""
        winner_table = Table(show_header=True, box=box.DOUBLE, border_style="gold1")
        winner_table.add_column("Winner", style="bold green")
        winner_table.add_column("Hand", style="cyan")
        winner_table.add_column("Won", justify="right", style="yellow")

        for player, amount, hand_name in winners:
            winner_table.add_row(player.name, hand_name, f"${amount}")

        self.console.print()
        self.console.print(Panel(
            winner_table,
            title="[bold]Hand Results[/bold]",
            border_style="gold1"
        ))
        self.console.print()

    def show_message(self, message: str, style: str = ""):
        """Show a message."""
        if style:
            self.console.print(f"[{style}]{message}[/{style}]")
        else:
            self.console.print(message)

    def show_bot_action(self, bot_name: str, action: str, amount: int = 0):
        """Show bot's action with a pause for visibility."""
        import time

        if action == "fold":
            msg = f"  {bot_name} folds"
            style = "red"
        elif action == "check":
            msg = f"  {bot_name} checks"
            style = "cyan"
        elif action == "call":
            msg = f"  {bot_name} calls ${amount}"
            style = "yellow"
        elif action == "raise":
            msg = f"  {bot_name} raises ${amount}"
            style = "bold yellow"
        else:
            msg = f"  {bot_name} {action}"
            style = ""

        self.console.print(f"[{style}]► {msg}[/{style}]")
        time.sleep(0.8)  # Pause to make bot actions visible

    def show_store(self, current_chips: int) -> Optional[int]:
        """Show store menu. Returns chips to add or None."""
        self.clear()
        self.show_title()

        self.console.print(Panel(
            f"[bold cyan]Your Chips:[/bold cyan] ${current_chips}",
            border_style="green"
        ))
        self.console.print()

        store_table = Table(show_header=True, box=box.ROUNDED, border_style="yellow")
        store_table.add_column("Item", style="bold")
        store_table.add_column("Cost", justify="right", style="green")

        store_table.add_row("Free Chips", "$500 - FREE!")

        self.console.print(store_table)
        self.console.print()

        choice = Prompt.ask(
            "[cyan]Get free chips? (y/n/exit)[/cyan]",
            choices=["y", "n", "yes", "no", "exit"],
            default="y"
        ).lower()

        if choice in ["y", "yes"]:
            return 500
        return None

    def show_stats(self, player: Player):
        """Show player stats."""
        self.clear()
        self.show_title()

        stats_table = Table(show_header=False, box=box.ROUNDED, border_style="cyan")
        stats_table.add_column("Stat", style="bold yellow")
        stats_table.add_column("Value", style="green")

        stats_table.add_row("Player Name", player.name)
        stats_table.add_row("Current Chips", f"${player.chips}")

        self.console.print(Panel(stats_table, title="[bold]Player Statistics[/bold]"))
        self.console.print()

        Prompt.ask("[dim]Press Enter to continue[/dim]", default="")

    def ask_continue(self, message: str = "Continue to next hand?") -> bool:
        """Ask if player wants to continue."""
        return Confirm.ask(f"[cyan]{message}[/cyan]", default=True)

    def ask_bot_difficulty(self) -> str:
        """Ask for bot difficulty level."""
        self.console.print()
        difficulty_table = Table(show_header=False, box=box.ROUNDED, border_style="yellow")
        difficulty_table.add_column("Level", style="bold")
        difficulty_table.add_column("Description")

        difficulty_table.add_row("easy", "Passive bots, rarely bluff")
        difficulty_table.add_row("medium", "Balanced play, moderate bluffing")
        difficulty_table.add_row("hard", "Aggressive bots, frequent bluffs")

        self.console.print(difficulty_table)
        self.console.print()

        return Prompt.ask(
            "[cyan]Select bot difficulty[/cyan]",
            choices=["easy", "medium", "hard"],
            default="medium"
        )

    def show_game_over(self, won: bool):
        """Show game over screen."""
        self.clear()

        if won:
            msg = "[bold green]Congratulations! You won all the chips![/bold green]"
        else:
            msg = "[bold red]Game Over! You ran out of chips.[/bold red]"

        self.console.print(Panel(msg, border_style="yellow"))
        self.console.print()
