from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
from rich.progress import Progress, BarColumn, TextColumn
from src.analytics import AnalyticsEngine
import datetime

class DashboardUI:
    def __init__(self):
        self.layout = Layout()
        self.analytics = AnalyticsEngine()
        self.total_questions = 0
        self.current_index = 0
        self.score = 0
        self.current_question = None
        self.user_answer = None
        self.feedback = None
        self.status_message = "Listening..."
        
        self.setup_layout()

    def setup_layout(self):
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        self.layout["main"].split_row(
            Layout(name="question_area", ratio=2),
            Layout(name="sidebar", ratio=1)
        )

    def generate_header(self):
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="center", ratio=2)
        grid.add_column(justify="right", ratio=1)
        
        grid.add_row(
            Text(datetime.datetime.now().strftime("%Y-%m-%d"), style="dim"),
            Text("Viva-LDA: Offline Memory Revision System", style="bold white"),
            Text("v2.0 (Whisper+Excel)", style="dim")
        )
        return Panel(grid, style="white on blue")

    def generate_question_area(self):
        if not self.current_question:
            content = Text("Preparing Session...", justify="center", style="dim")
        else:
            q_text = Text(self.current_question['question_text'], style="bold cyan size=20", justify="center")
            
            # Options Table
            opts = Table(box=box.ROUNDED, show_header=False, expand=True, border_style="dim")
            opts.add_column("Key", style="bold yellow", width=8, justify="center")
            opts.add_column("Text", style="white")
            
            opts.add_row("A", self.current_question['option_a'])
            opts.add_row("B", self.current_question['option_b'])
            opts.add_row("C", self.current_question['option_c'])
            opts.add_row("D", self.current_question['option_d'])
            
            content = Table.grid(expand=True)
            content.add_row(Panel(q_text, box=box.HEAVY, border_style="cyan", title=f"[b]Question {self.current_index}/{self.total_questions}[/b]"))
            content.add_row(Text(" "))
            content.add_row(opts)
            content.add_row(Text(" "))
            
            # Feedback Area
            feedback_panel = None
            if self.feedback:
                color = "green" if "Correct" in self.feedback else "red"
                feedback_panel = Panel(Text(self.feedback, justify="center", style=f"bold white on {color}"), box=box.DOUBLE, border_style=color)
            elif self.user_answer:
                 feedback_panel = Panel(Text(f"You said: {self.user_answer}", justify="center", style="bold magenta"), border_style="magenta", title="Processing")
            else:
                 feedback_panel = Panel(Text("Waiting for answer...", justify="center", style="dim"), border_style="dim")
            
            content.add_row(feedback_panel)

        return Panel(content, title="Active Revision", border_style="green")

    def generate_sidebar(self):
        stats = self.analytics.get_overall_stats()
        weak_topics = self.analytics.get_weakest_topics(limit=5)
        
        # Mastery Progress Bar
        mastery_pct = int(stats['mastery'])
        
        mastery_bar = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None, complete_style="blue", finished_style="green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        )
        mastery_bar.add_task("Mastery", total=100, completed=mastery_pct)
        
        # Session Progress Bar
        session_pct = 0
        if self.current_index > 0:
            session_pct = (self.score / self.current_index) * 100
            
        session_bar = Progress(
            TextColumn("[bold yellow]{task.description}"),
            BarColumn(bar_width=None, complete_style="yellow", finished_style="green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        )
        session_bar.add_task("Session Accuracy", total=100, completed=session_pct)

        # Overview Grid
        grid = Table.grid(expand=True)
        grid.add_row(mastery_bar)
        grid.add_row(Text(" "))
        grid.add_row(session_bar)
        grid.add_row(Text(" "))
        
        # Stats Table
        stat_table = Table(box=box.SIMPLE, expand=True)
        stat_table.add_column("Metric", style="dim")
        stat_table.add_column("Value", justify="right", style="bold white")
        stat_table.add_row("Total Qs", str(stats['total']))
        stat_table.add_row("Reviewed", str(stats['reviewed']))
        stat_table.add_row("Unseen", str(stats['new']))
        
        # Weak Topics Table
        weak_table = Table(title="[b red]Focus Areas[/]", box=box.SIMPLE, expand=True, title_style="red")
        weak_table.add_column("Topic")
        weak_table.add_column("Recall", justify="right")
        for topic in weak_topics:
            color = "red" if topic['recall'] < 50 else "yellow"
            weak_table.add_row(topic['subject'][:15], f"[{color}]{int(topic['recall'])}%[/]")

        content = Table.grid(expand=True)
        content.add_row(Panel(grid, title="Performance", border_style="blue"))
        content.add_row(Panel(stat_table, title="Database", border_style="dim"))
        content.add_row(Panel(weak_table, title="Weakest Topics", border_style="red"))
        
        return Panel(content, title="Analytics", border_style="yellow")

    def generate_footer(self):
        return Panel(Text(self.status_message, style="italic cyan", justify="center"), style="black on white")

    def get_renderable(self):
        self.layout["header"].update(self.generate_header())
        self.layout["question_area"].update(self.generate_question_area())
        self.layout["sidebar"].update(self.generate_sidebar())
        self.layout["footer"].update(self.generate_footer())
        return self.layout

    def update_state(self, question=None, answer=None, feedback=None, index=0, total=0, score=0, status=None):
        if question: self.current_question = question
        if answer is not None: self.user_answer = answer # Can be None to clear
        if feedback is not None: self.feedback = feedback
        if index: self.current_index = index
        if total: self.total_questions = total
        if score: self.score = score
        if status: self.status_message = status
