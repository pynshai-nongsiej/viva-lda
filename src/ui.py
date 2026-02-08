from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
from src.analytics import AnalyticsEngine

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
        title = Text("Viva-LDA: Offline Memory Revision System", style="bold white on blue", justify="center")
        return Panel(title, style="blue")

    def generate_question_area(self):
        if not self.current_question:
            content = Text("Preparing Session...", justify="center", style="dim")
        else:
            q_text = Text(self.current_question['question_text'], style="bold cyan", justify="center")
            
            opts = Table(box=None, show_header=False, expand=True)
            opts.add_column("Key", style="bold yellow", width=10)
            opts.add_column("Text", style="white")
            
            opts.add_row("(A)", self.current_question['option_a'])
            opts.add_row(" ", "")
            opts.add_row("(B)", self.current_question['option_b'])
            opts.add_row(" ", "")
            opts.add_row("(C)", self.current_question['option_c'])
            opts.add_row(" ", "")
            opts.add_row("(D)", self.current_question['option_d'])
            
            content = Table.grid(expand=True)
            content.add_row(Panel(q_text, box=box.HEAVY, title=f"Question {self.current_index}/{self.total_questions}"))
            content.add_row(Panel(opts, title="Options"))
            
            if self.user_answer:
                ans_text = Text(f"You said: {self.user_answer}", style="bold magenta")
                content.add_row(Panel(ans_text, style="magenta"))
                
            if self.feedback:
                fb_style = "green" if "Correct" in self.feedback else "red"
                content.add_row(Panel(Text(self.feedback, style=f"bold {fb_style}"), title="Result"))

        return Panel(content, title="Active Revision", border_style="green")

    def generate_sidebar(self):
        stats = self.analytics.get_overall_stats()
        weak_topics = self.analytics.get_weakest_topics()
        
        # Overall Stats Table
        stat_table = Table(title="Overall Progress", box=box.SIMPLE)
        stat_table.add_column("Metric", style="cyan")
        stat_table.add_column("Value", style="green")
        stat_table.add_row("Total Qs", str(stats['total']))
        stat_table.add_row("Mastered", f"{int(stats['mastery'])}%")
        stat_table.add_row("Reviewed", str(stats['reviewed']))
        
        # Weak Topics Table
        weak_table = Table(title="Focus Areas", box=box.SIMPLE)
        weak_table.add_column("Subject", style="red")
        weak_table.add_column("Recall", style="dim")
        for topic in weak_topics:
            weak_table.add_row(topic['subject'][:15], f"{int(topic['recall'])}%")

        # Current Session Stats
        session_table = Table(title="Current Session", box=box.SIMPLE)
        session_table.add_column("Metric")
        session_table.add_column("Value")
        session_table.add_row("Score", f"{self.score}/{self.current_index}")
        
        content = Table.grid(expand=True)
        content.add_row(stat_table)
        content.add_row(Text("\n"))
        content.add_row(weak_table)
        content.add_row(Text("\n"))
        content.add_row(session_table)
        
        return Panel(content, title="Analytics", border_style="yellow")

    def generate_footer(self):
        return Panel(Text(self.status_message, style="dim italic"), title="System Status")

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
