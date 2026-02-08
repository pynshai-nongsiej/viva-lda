import sqlite3
import random
import time
from datetime import datetime
from src import memory, voice

DB_PATH = "data/questions.db"

class SessionManager:
    def __init__(self):
        self.mem_engine = memory.MemoryEngine()
        self.total_questions = 0
        self.correct_count = 0
        self.start_time = None

    def get_questions_for_session(self, total_count=10):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        questions = []
        selected_ids = set()
        
        # 1. Priorities
        # Try to get some weak, some new, some review
        # Heuristic: 
        # - Up to 50% Weak (review_count > 0, sorted by recall)
        # - Up to 20% New (review_count = 0)
        # - Rest Random Review
        
        target_weak = int(total_count * 0.5)
        target_new = int(total_count * 0.2)
        
        # Fetch Weak
        cursor.execute("SELECT * FROM questions WHERE review_count > 0 ORDER BY recall_score ASC LIMIT ?", (target_weak,))
        rows = cursor.fetchall()
        for r in rows:
            questions.append(dict(r))
            selected_ids.add(r['id'])
            
        # Fetch New
        cursor.execute("SELECT * FROM questions WHERE review_count = 0 ORDER BY RANDOM() LIMIT ?", (target_new,))
        rows = cursor.fetchall()
        for r in rows:
            if r['id'] not in selected_ids:
                questions.append(dict(r))
                selected_ids.add(r['id'])
        
        # Fill remainder with anything available (Prioritize having *questions* over category)
        # First try to fill with more review items
        remainder = total_count - len(questions)
        if remainder > 0:
            placeholders = ','.join('?' * len(selected_ids)) if selected_ids else '-1'
            sql = f"SELECT * FROM questions WHERE id NOT IN ({placeholders}) AND review_count > 0 ORDER BY RANDOM() LIMIT ?"
            cursor.execute(sql, (*selected_ids, remainder))
            rows = cursor.fetchall()
            for r in rows:
                questions.append(dict(r))
                selected_ids.add(r['id'])
                
        # If still need more, fill with NEW
        remainder = total_count - len(questions)
        if remainder > 0:
            placeholders = ','.join('?' * len(selected_ids)) if selected_ids else '-1'
            sql = f"SELECT * FROM questions WHERE id NOT IN ({placeholders}) AND review_count = 0 ORDER BY RANDOM() LIMIT ?"
            cursor.execute(sql, (*selected_ids, remainder))
            rows = cursor.fetchall()
            for r in rows:
                questions.append(dict(r))
                selected_ids.add(r['id'])

        conn.close()
        random.shuffle(questions)
        return questions

    def run_session(self, count=10):
        from rich.live import Live
        from src.ui import DashboardUI
        
        dashboard = DashboardUI()
        
        # Initial Fetch
        questions = self.get_questions_for_session(count)
        
        if not questions:
            print("No questions found in database. Please ingest a PDF first.")
            return

        self.start_time = time.time()
        self.total_questions = len(questions)
        self.correct_count = 0
        
        # Verify Voice System
        try:
            dashboard.update_state(status="Initializing Voice System...")
            voice.load_stt_model() # This checks for model existence
        except Exception as e:
            print(f"Voice system error: {e}")
            return

        with Live(dashboard.get_renderable(), refresh_per_second=4, screen=True) as live:
            for i, q in enumerate(questions):
                # Update Dashboard for new Question
                dashboard.update_state(
                    question=q, 
                    index=i+1, 
                    total=len(questions), 
                    score=self.correct_count,
                    status="Reading Question...",
                    answer=None,
                    feedback=None
                )
                live.update(dashboard.get_renderable())
                
                # Speak Question
                text = f"Question: {q['question_text']}"
                voice.speak(text)
                
                # Speak Options
                options_text = ""
                if q['option_a']: options_text += f"Option A: {q['option_a']}. "
                if q['option_b']: options_text += f"Option B: {q['option_b']}. "
                if q['option_c']: options_text += f"Option C: {q['option_c']}. "
                if q['option_d']: options_text += f"Option D: {q['option_d']}. "
                
                dashboard.update_state(status="Reading Options...")
                live.update(dashboard.get_renderable())
                voice.speak(options_text)
                
                # Listen
                dashboard.update_state(status="Listening for Answer...", feedback=None)
                live.update(dashboard.get_renderable())
                
                voice.speak("Your answer?")
                
                # Create options context for fuzzy matching
                options_ctx = {
                    'A': q['option_a'],
                    'B': q['option_b'],
                    'C': q['option_c'],
                    'D': q['option_d']
                }
                
                start_response = time.time()
                user_ans = voice.listen_for_answer(timeout=7, options=options_ctx)
                response_time = time.time() - start_response
                
                correct_ans = q['correct_answer']
                is_correct = False
                
                if user_ans:
                    dashboard.update_state(answer=user_ans)
                    live.update(dashboard.get_renderable())
                    
                    if user_ans.upper() == correct_ans.upper():
                        voice.speak("Correct.")
                        is_correct = True
                        self.correct_count += 1
                        dashboard.update_state(feedback="Correct!", score=self.correct_count)
                    else:
                        correct_text = q[f'option_{correct_ans.lower()}']
                        voice.speak(f"Wrong. The answer is {correct_ans}. {correct_text}")
                        dashboard.update_state(feedback=f"Wrong! Answer: {correct_ans}")
                else:
                    correct_text = q[f'option_{correct_ans.lower()}']
                    voice.speak(f"Time up. The answer is {correct_ans}. {correct_text}")
                    dashboard.update_state(feedback=f"Time Up! Answer: {correct_ans}")
                
                live.update(dashboard.get_renderable())

                # Update Memory
                dashboard.update_state(status="Updating Memory...")
                live.update(dashboard.get_renderable())
                
                try:
                    self.mem_engine.update_question_stats(q['id'], is_correct, response_time)
                except Exception as e:
                    # Log error silently or to debug
                    pass
                
                # Short pause
                time.sleep(2)

        self.end_session()

    def end_session(self):
        duration = time.time() - self.start_time
        msg = f"Session complete. Score: {self.correct_count}/{self.total_questions}. Duration: {int(duration)} seconds."
        print(msg)
        voice.speak(msg)
