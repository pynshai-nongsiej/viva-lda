from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
from rich.progress import Progress, BarColumn, TextColumn
from rich.align import Align
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
        self.status_message = "Initializing System..."
        
        # Exam Goals (Passing Requirements)
        self.goals = {
            "English": {"marks": 100, "questions": 50},
            "GK": {"marks": 80, "questions": 40},
            "Computer": {"marks": 50, "questions": 25}
        }
        
        self.setup_layout()

    def setup_layout(self):
        """Creates a bento-style layout with a stable content container."""
        self.layout.split(
            Layout(name="header", size=4),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=3)
        )
        self.layout["body"].split_row(
            Layout(name="main_container", ratio=3),
            Layout(name="sidebar", ratio=1)
        )

    def generate_header(self):
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="right", ratio=1)
        
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        date_str = datetime.datetime.now().strftime("%d %b %Y")
        
        grid.add_row(
            Text(f"📅 {date_str}", style="bold cyan"),
            Text("VIVA-LDA v4.0 | ELITE PREP ENGINE", style="bold white on blue", justify="center"),
            Text(f"🕒 {time_str}", style="bold magenta")
        )
        return Panel(grid, box=box.DOUBLE, border_style="blue")

    def generate_footer(self):
        return Panel(Align.center(Text(f" {self.status_message} ", style="italic yellow")), border_style="dim")

    def format_question(self, text, subject):
        if not text: return text
        import re
        text = re.sub(r'(\([A-D]\))', r'[bold magenta]\1[/bold magenta]', text)
        text = re.sub(r'(_+)', r'[bold yellow]\1[/bold yellow]', text)
        return text

    def generate_question_area(self):
        if not self.current_question:
            return Panel(Align.center(Text("\n\nReady for session...", style="dim")), title="Module", border_style="blue")
        
        subject = self.current_question.get('subject', 'General')
        q_text = self.current_question['question_text']
        q_formatted = self.format_question(q_text, subject)
        
        header = Table.grid(expand=True)
        header.add_row(
            Text(f"SUBJECT: {subject.upper()}", style="bold yellow"),
            Text(f"PROGRESS: {self.current_index}/{self.total_questions}", style="bold cyan", justify="right")
        )
        
        opts_table = Table(box=box.SIMPLE, show_header=False, expand=True)
        opts_table.add_column("Key", style="bold reverse", width=5)
        opts_table.add_column("Value")
        opts_table.add_row(" A ", self.current_question['option_a'])
        opts_table.add_row(" B ", self.current_question['option_b'])
        opts_table.add_row(" C ", self.current_question['option_c'])
        opts_table.add_row(" D ", self.current_question['option_d'])

        content = Table.grid(expand=True)
        content.add_row(Panel(header, border_style="dim"))
        content.add_row(Text("\n"))
        content.add_row(Text.from_markup(q_formatted))
        content.add_row(Text("\n"))
        content.add_row(opts_table)
        return Panel(content, title="Focus Module", border_style="bright_blue")

    def generate_feedback_area(self):
        if not self.user_answer:
            return Panel(Align.center(Text("WAITING FOR INPUT", style="blink bold dim")), title="System Status", border_style="dim")
        
        is_correct = "Correct" in str(self.feedback)
        color = "green" if is_correct else "red"
        glyph = "✓" if is_correct else "✗"
        msg = f"[bold {color}]{glyph} {self.feedback}[/]"
        return Panel(Align.center(msg, vertical="middle"), title="Feedback", border_style=color)

    def generate_sidebar(self):
        goal_table = Table(title="EXAM TARGETS", box=box.MINIMAL, expand=True, title_style="bold underline")
        goal_table.add_column("Subject", style="bold")
        goal_table.add_column("Current", justify="right")
        goal_table.add_column("Target", justify="right", style="dim")
        
        subject_stats = self.analytics.get_subject_performance()
        for sub_name, goal in self.goals.items():
            actual_count = 0
            for s in subject_stats:
                if sub_name.lower() in s['subject'].lower():
                    actual_count += s['total']
            goal_table.add_row(sub_name, str(actual_count), str(goal['questions']))

        stats = self.analytics.get_overall_stats()
        mastery_progress = Progress(
            TextColumn("[bold blue]Mastery"),
            BarColumn(bar_width=None, complete_style="blue"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        )
        mastery_progress.add_task("mastery", total=100, completed=stats['mastery'])
        
        prediction = self.analytics.get_mastery_prediction()
        days = f"{prediction['days_left']:.1f}" if prediction['days_left'] != float('inf') else "---"
        
        sidebar_content = Table.grid(expand=True)
        sidebar_content.add_row(Panel(goal_table, border_style="yellow"))
        sidebar_content.add_row(Panel(mastery_progress, title="Overall Skill", border_style="blue"))
        sidebar_content.add_row(Panel(Align.center(Text(f"ETA Mastery: {days} Days", style="bold green")), border_style="green"))
        return Panel(sidebar_content, title="Analytics", border_style="magenta")

    def generate_selection_menu(self, subjects):
        table = Table(box=box.DOUBLE, expand=True, border_style="bold blue")
        table.add_column("ID", style="bold yellow", width=5, justify="center")
        table.add_column("Training Suite", style="bold white")
        table.add_column("Recall", justify="right")
        
        table.add_row("0", "OMNIBUS TRAINING (All Subjects)", "Hybrid")
        
        subject_perf = self.analytics.get_subject_performance()
        perf_map = {p['subject']: p['recall'] for p in subject_perf}

        for i, sub in enumerate(subjects):
            recall = perf_map.get(sub, 0.0)
            color = "green" if recall > 80 else "yellow" if recall > 50 else "red"
            table.add_row(str(i+1), sub, f"[{color}]{int(recall)}%[/]")
            
        return Panel(table, title="CORE NAVIGATION", subtitle="Select ID and press Enter", border_style="bright_blue")

    def get_renderable(self, mode="session", subjects=None):
        self.layout["header"].update(self.generate_header())
        self.layout["footer"].update(self.generate_footer())
        self.layout["sidebar"].update(self.generate_sidebar())
        
        if mode == "selection" and subjects:
            self.layout["main_container"].update(self.generate_selection_menu(subjects))
        else:
            # Re-split or update existing session structure
            session_layout = Layout()
            session_layout.split_column(
                Layout(self.generate_question_area(), ratio=3),
                Layout(self.generate_feedback_area(), size=10)
            )
            self.layout["main_container"].update(session_layout)
            
        return self.layout

    def update_state(self, question=None, answer=None, feedback=None, index=0, total=0, score=0, status=None):
        if question: self.current_question = question
        if answer is not None: self.user_answer = answer
        if feedback is not None: self.feedback = feedback
        if index: self.current_index = index
        if total: self.total_questions = total
        if score: self.score = score
        if status: self.status_message = status
