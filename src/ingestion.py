import sqlite3
import csv
import os

DB_PATH = "data/questions.db"

def init_db():
    """Initializes the SQLite database."""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            question_text TEXT,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            option_d TEXT,
            correct_answer TEXT,
            recall_score REAL DEFAULT 0.0,
            review_count INTEGER DEFAULT 0,
            last_reviewed_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_questions(questions):
    """Saves parsed questions to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    count = 0
    for q in questions:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO questions (subject, question_text, option_a, option_b, option_c, option_d, correct_answer)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', q)
            if cursor.rowcount > 0:
                count += 1
        except sqlite3.IntegrityError:
            pass # Skip duplicates
            
    conn.commit()
    conn.close()
    return count

def ingest_csv(csv_path):
    print(f"Processing {csv_path}...")
    init_db()
    
    questions = []
    
    with open(csv_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if not row or len(row) < 10:
                continue
                
            topic = row[0].strip()
            subtopic = row[1].strip()
            
            # Use 'Topic - Subtopic' if Subtopic exists, else just Topic
            if subtopic and subtopic.lower() != 'none':
                subject = f"{topic} - {subtopic}"
            else:
                subject = topic
                
            # The last 6 columns are strictly: A, B, C, D, Answer, Source
            opt_a = row[-6].strip()
            opt_b = row[-5].strip()
            opt_c = row[-4].strip()
            opt_d = row[-3].strip()
            answer_text = row[-2].strip()
            
            # Question is everything in between index 3 and the last 6 columns
            q_text = ",".join(row[3:len(row)-6]).strip()
            
            if not q_text:
                continue
            
            # Remove any wrapping quotes that might have been left on the question
            if q_text.startswith('"') and q_text.endswith('"'):
                q_text = q_text[1:-1]
            
            # Try to map exact text matching to A, B, C, D
            correct_ans = None
            def normalize(s):
                import re
                # also strip any trailing/leading quotes just in case
                s = s.strip().strip('"').strip("'")
                return re.sub(r'\s+', ' ', s.lower())
                
            norm_ans = normalize(answer_text)
            if norm_ans == normalize(opt_a):
                correct_ans = 'A'
            elif norm_ans == normalize(opt_b):
                correct_ans = 'B'
            elif norm_ans == normalize(opt_c):
                correct_ans = 'C'
            elif norm_ans == normalize(opt_d):
                correct_ans = 'D'
            elif answer_text.upper() in ['A', 'B', 'C', 'D']:
                correct_ans = answer_text.upper()
            else:
                # Fuzzy matching fallback
                import difflib
                options = {
                    'A': normalize(opt_a),
                    'B': normalize(opt_b),
                    'C': normalize(opt_c),
                    'D': normalize(opt_d)
                }
                # Find the option with highest similarity score
                best_match = None
                highest_score = 0
                for letter, opt_text in options.items():
                    score = difflib.SequenceMatcher(None, norm_ans, opt_text).ratio()
                    if score > highest_score:
                        highest_score = score
                        best_match = letter
                
                if highest_score > 0.6: # Relaxed threshold to catch typos
                    correct_ans = best_match
                else:
                    # Absolute fallback: Just default to A to avoid dropping the question
                    print(f"Warning: Very low match for '{answer_text}'. Defaulting to A.")
                    correct_ans = 'A'
            
            q_data = (
                subject,
                q_text,
                opt_a,
                opt_b,
                opt_c,
                opt_d,
                correct_ans
            )
            questions.append(q_data)
            
    print(f"Found {len(questions)} valid MCQs.")
    if questions:
        saved_count = save_questions(questions)
        print(f"Saved {saved_count} new questions to database.")

def ingest_directory(directory_path):
    """Recursively ingest all CSVs in a directory."""
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.lower().endswith(".csv"):
                full_path = os.path.join(root, file)
                ingest_csv(full_path)

if __name__ == "__main__":
    csv_dir = "/Users/pynshainongsiej/Desktop/Project/Viva-LDA/csv"
    if os.path.exists(csv_dir):
        ingest_directory(csv_dir)
    else:
        print(f"Directory {csv_dir} does not exist.")
