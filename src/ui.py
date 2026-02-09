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
    
    def format_question(self, text, subject):
        if not text: return text
        import re
        
        # Error Detection / Correction Patterns
        if "Error" in subject or "/" in text:
            # Highlight dividers
            text = text.replace(" / ", " [bold red]/[/] ")
            # Highlight segment markers like (A), (B), (C), (D)
            text = re.sub(r'(\([A-D]\))', r'[bold magenta]\1[/bold magenta]', text)
            # Ensure "No error" is distinct
            text = text.replace("No error", "[italic dim]No error[/italic dim]")
            
        # Fill in the Blanks Patterns
        if "Fill in the Blanks" in subject:
            # Look for existing gaps
            if "___" not in text and "_" not in text:
                # Heuristic: If we see two spaces or a space before/after certain words, 
                # but since extract_text might have collapsed them, let's look for 
                # explicit underscores if they were parsed.
                # If not, we might need a more advanced parser, but for now 
                # let's assume ingestion preserved them if they were characters.
                pass
            # Highlight underscores
            text = re.sub(r'(_+)', r'[bold yellow]\1[/bold yellow]', text)
            
        return text

    def generate_selection_menu(self, subjects):
        table = Table(box=box.DOUBLE, expand=True, border_style="bold magenta")
        table.add_column("Key", style="bold yellow", width=10, justify="center")
        table.add_column("Subject Name", style="bold white")
        table.add_column("Progress", justify="right")
        
        table.add_row("[0]", "ALL SUBJECTS", "Combined Strategy")
        for i, sub in enumerate(subjects):
            table.add_row(f"[{i+1}]", sub, "Targeted Review")
            
        content = Table.grid(expand=True)
        content.add_row(Text("\n" * 2))
        content.add_row(Panel(table, title="[b white]Select Training Subject[/b white]", subtitle="Enter number to begin", border_style="magenta"))
        
        return content

    def generate_header(self):
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="center", ratio=2)
        grid.add_column(justify="right", ratio=1)
        
        grid.add_row(
            Text(datetime.datetime.now().strftime("%Y-%m-%d"), style="dim"),
            Text("VIVA-LDA v3.0 | Intelligent MCQ Recall", style="bold white"),
            Text("Category-Based Revision", style="dim")
        )
        return Panel(grid, style="white on blue", box=box.HORIZONTALS)

    def generate_question_area(self):
        if not self.current_question:
            content = Text("Preparing Session...", justify="center", style="dim")
        else:
            subject_tag = f"[b yellow]{self.current_question.get('subject', 'General')}[/b yellow]"
            q_raw = self.current_question['question_text']
            q_formatted = self.format_question(q_raw, self.current_question.get('subject', ''))
            q_text = Text.from_markup(q_formatted, justify="left")
            
            # Options Table
            opts = Table(box=box.SIMPLE_HEAD, show_header=False, expand=True, border_style="dim")
            opts.add_column("Key", style="bold yellow", width=10, justify="center")
            opts.add_column("Text", style="white")
            
            opts.add_row("[A]", self.current_question['option_a'])
            opts.add_row("[B]", self.current_question['option_b'])
            opts.add_row("[C]", self.current_question['option_c'])
            opts.add_row("[D]", self.current_question['option_d'])
            
            content = Table.grid(expand=True)
            content.add_row(Panel(q_text, box=box.ROUNDED, border_style="blue", title=f"{subject_tag} | Question {self.current_index}/{self.total_questions}", title_align="left"))
            content.add_row(Text(" "))
            content.add_row(opts)
            content.add_row(Text(" "))
            
            # Feedback Area
            feedback_panel = None
            if self.feedback:
                is_correct = "Correct" in self.feedback
                color = "green" if is_correct else "red"
                symbol = "✓" if is_correct else "✗"
                feedback_panel = Panel(Text(f"{symbol} {self.feedback}", justify="center", style=f"bold white"), box=box.HEAVY, border_style=color, style="on grey15" if not is_correct else "on grey7")
            elif self.user_answer:
                 feedback_panel = Panel(Text(f"Evaluating: {self.user_answer}...", justify="center", style="bold magenta"), border_style="magenta")
            else:
                 feedback_panel = Panel(Text("Type your answer (A/B/C/D) and press Enter", justify="center", style="italic dim"), border_style="dim")
            
            content.add_row(feedback_panel)

        return Panel(content, title="Revision Center", border_style="cyan")

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

    def get_renderable(self, mode="session", subjects=None):
        self.layout["header"].update(self.generate_header())
        self.layout["sidebar"].update(self.generate_sidebar())
        self.layout["footer"].update(self.generate_footer())
        
        if mode == "selection" and subjects:
            self.layout["question_area"].update(self.generate_selection_menu(subjects))
        else:
            self.layout["question_area"].update(self.generate_question_area())
            
        return self.layout

    def update_state(self, question=None, answer=None, feedback=None, index=0, total=0, score=0, status=None):
        if question: self.current_question = question
        if answer is not None: self.user_answer = answer # Can be None to clear
        if feedback is not None: self.feedback = feedback
        if index: self.current_index = index
        if total: self.total_questions = total
        if score: self.score = score
        if status: self.status_message = status
