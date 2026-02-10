import sqlite3
import random
import time
from datetime import datetime
from src import memory
from rich.prompt import Prompt
from rich.console import Console

DB_PATH = "data/questions.db"
console = Console()

class SessionManager:
    def __init__(self):
        self.mem_engine = memory.MemoryEngine()
        self.total_questions = 0
        self.correct_count = 0
        self.start_time = None

    def get_questions_for_session(self, total_count=20, subject=None):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        questions = []
        selected_ids = set()
        
        # Base SQL condition
        where_clause = "WHERE subject = ?" if subject else "WHERE 1=1"
        params = [subject] if subject else [] # This line was `params = [subject]` in the instruction, but that would break if subject is None. Reverting to original logic.
        # 1. Priorities
        # Try to get some weak, some new, some review
        target_weak = int(total_count * 0.5)
        target_new = int(total_count * 0.2)
        
        # Fetch Weak
        cursor.execute(f"SELECT * FROM questions {where_clause} AND review_count > 0 ORDER BY recall_score ASC LIMIT ?", (*params, target_weak))
        rows = cursor.fetchall()
        for r in rows:
            questions.append(dict(r))
            selected_ids.add(r['id'])
            
        # Fetch New
        cursor.execute(f"SELECT * FROM questions {where_clause} AND review_count = 0 ORDER BY RANDOM() LIMIT ?", (*params, target_new))
        rows = cursor.fetchall()
        for r in rows:
            if r['id'] not in selected_ids:
                questions.append(dict(r))
                selected_ids.add(r['id'])
        
        # Fill remainder with anything available
        remainder = total_count - len(questions)
        if remainder > 0:
            placeholders = ','.join('?' * len(selected_ids)) if selected_ids else '-1'
            sql = f"SELECT * FROM questions {where_clause} AND id NOT IN ({placeholders}) AND review_count > 0 ORDER BY RANDOM() LIMIT ?"
            cursor.execute(sql, (*params, *selected_ids, remainder))
            rows = cursor.fetchall()
            for r in rows:
                questions.append(dict(r))
                selected_ids.add(r['id'])
                
        # If still need more, fill with ANY remaining
        remainder = total_count - len(questions)
        if remainder > 0:
            placeholders = ','.join('?' * len(selected_ids)) if selected_ids else '-1'
            sql = f"SELECT * FROM questions {where_clause} AND id NOT IN ({placeholders}) ORDER BY RANDOM() LIMIT ?"
            cursor.execute(sql, (*params, *selected_ids, remainder))
            rows = cursor.fetchall()
            for r in rows:
                questions.append(dict(r))
                selected_ids.add(r['id'])

        conn.close()
        random.shuffle(questions)
        return questions

    def get_available_subjects(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT subject FROM questions")
        subs = [r[0] for r in cursor.fetchall()]
        conn.close()
        return sorted(subs)

    def run_session(self, count=20, subject=None):
        from rich.live import Live
        from src.ui import DashboardUI
        
        dashboard = DashboardUI()
        
        # Interactive Subject Selection if not provided
        if subject is None:
            available = self.get_available_subjects()
            if available:
                dashboard.update_state(status="Select Subject to Begin...")
                console.clear()
                console.print(dashboard.get_renderable(mode="selection", subjects=available))
                
                choices = [str(i) for i in range(len(available) + 1)]
                choice = Prompt.ask("\nSelect Subject", choices=choices, default="0")
                
                if choice != "0":
                    subject = available[int(choice) - 1]
                    dashboard.update_state(status=f"Subject: {subject} Selected.")

        # Initial Fetch
        questions = self.get_questions_for_session(count, subject)
        
        if not questions:
            console.print("[red]No questions found in database. Please ingest a PDF first.[/red]")
            return

        self.start_time = time.time()
        self.total_questions = len(questions)
        self.correct_count = 0
        
        dashboard.update_state(status="Starting Session...")

        # We can't use live.update() inside input().
        # So we use a loop where we print the dashboard, then ask for input below it.
        # But DashboardUI is designed for full screen.
        # Let's use Live to show the question, then stop it briefly to take input?
        # Or better: Just use Live and capturing input might be tricky if we want to type IN the dashboard.
        # Simplest: Live is active, but we use console.input() which might break the layout.
        # Taking a cue from previous debug mode: print dashboard then standard input.
        # Actually proper TUI input is complex.
        # Compromise: We will update the dashboard with "Waiting for Input", 
        # then pause the Live context to accept input via standard Prompt, then resume.
        
        for i, q in enumerate(questions):
            # 1. Update Dashboard with Question
            dashboard.update_state(
                question=q, 
                index=i+1, 
                total=len(questions), 
                score=self.correct_count,
                status="Waiting for Answer...",
                answer=None,
                feedback=None
            )
            
            # Print the dashboard once
            console.clear()
            console.print(dashboard.get_renderable())
            
            start_response = time.time()
            
            # 2. Get Input
            # Using rich Prompt for cleaner input
            console.print("\n")
            user_ans = Prompt.ask("Your Answer", choices=["A", "B", "C", "D", "a", "b", "c", "d"], default="A")
            user_ans = user_ans.upper()
            
            response_time = time.time() - start_response
            
            correct_ans = q['correct_answer']
            is_correct = False
            
            feedback_msg = ""
            if user_ans == correct_ans.upper():
                is_correct = True
                self.correct_count += 1
                feedback_msg = "Correct!"
                dashboard.update_state(feedback="Correct!", score=self.correct_count, answer=user_ans)
            else:
                correct_text = q[f'option_{correct_ans.lower()}']
                feedback_msg = f"Wrong! The answer is {correct_ans}."
                dashboard.update_state(feedback=f"Wrong! Ans: {correct_ans}", answer=user_ans)
            
            # 3. Show Feedback briefly
            console.clear()
            console.print(dashboard.get_renderable())
            time.sleep(1.5)

            # Update Memory
            try:
                self.mem_engine.update_question_stats(q['id'], is_correct, response_time)
            except Exception as e:
                pass
            
        # Export Analytics
        dashboard.update_state(status="Exporting Analytics Report...")
        console.clear()
        console.print(dashboard.get_renderable())
        
        print("\n\nExporting data...")
        dashboard.analytics.export_to_text()
        print("Detailed report saved to data/analytics_report.txt")
        
        self.end_session()

    def end_session(self):
        duration = time.time() - self.start_time
        msg = f"Session complete. Score: {self.correct_count}/{self.total_questions}. Duration: {int(duration)} seconds."
        console.print(f"[bold green]{msg}[/bold green]")
