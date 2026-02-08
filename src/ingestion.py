import sqlite3
import pdfplumber
import re
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
            question_text TEXT UNIQUE,
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

def extract_text_from_pdf(pdf_path):
    """Extracts raw text from a PDF file."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # x_tolerance=1 helps separate words that are close but not merged
            text += page.extract_text(x_tolerance=1) + "\n"
    return text

def parse_mcqs(text, subject="General"):
    """
    Parses MCQ text into structured data.
    Handles format:
    1. Question text... [Ans: (b)Option]
    (a) Option A
    (b) Option B
    ...
    """
    questions = []
    
    # Split by likely question start
    # Look for "Number." at start of line
    blocks = re.split(r'\n(?=\d+\.)', text)
    
    for block in blocks:
        if not block.strip():
            continue
            
        try:
            # 1. Extract Question Number and Text
            # Content before the first option (a)
            # Question might contain [Ans: ...]
            
            # Split into lines
            lines = block.strip().split('\n')
            if not lines: continue
            
            q_line = lines[0] # "1. Question... [Ans...]"
            
            # Extract Answer from q_line if present: [Ans: (b)...]
            ans_match = re.search(r'\[Ans:\s*\(?([a-d])\)?.*?\]', q_line, re.IGNORECASE)
            correct_ans = ans_match.group(1).upper() if ans_match else None
            
            # Clean Question Text (remove numbering and Ans block)
            q_text = re.sub(r'^\d+\.\s*', '', q_line) # Remove "1. "
            if ans_match:
                q_text = q_text.replace(ans_match.group(0), '').strip()
            
            if not q_text:
                q_text = "Question Text Missing"
                
            # Extract Options
            # Look for (a), (b), (c), (d) in subsequent lines
            # This is simple line-based parsing
            opts = {}
            current_opt = None
            
            for line in lines[1:]:
                line = line.strip()
                
                # Skip page numbers (lines that are just digits)
                if re.match(r'^\d+$', line):
                    continue
                
                # Check if line starts with option label
                opt_match = re.match(r'^\(?([a-d])\)[\.\s]\s*(.*)', line, re.IGNORECASE)
                if opt_match:
                    current_opt = opt_match.group(1).upper()
                    opts[current_opt] = opt_match.group(2).strip()
                elif current_opt:
                    # Append to previous option if multiline
                    opts[current_opt] += " " + line
            
            # Fallback for answer if not in question line, maybe at end?
            if not correct_ans:
                ans_match_end = re.search(r'Answer:\s*\(?([a-d])\)?', block, re.IGNORECASE)
                if ans_match_end:
                    correct_ans = ans_match_end.group(1).upper()
            
            if correct_ans and 'A' in opts and 'B' in opts:
                questions.append((
                    subject,
                    q_text,
                    opts.get('A', ''),
                    opts.get('B', ''),
                    opts.get('C', ''),
                    opts.get('D', ''),
                    correct_ans
                ))
        except Exception as e:
            print(f"Error parsing block: {e}")
            continue
            
    return questions

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

def ingest_pdf(pdf_path, subject="General"):
    print(f"Processing {pdf_path}...")
    init_db()
    text = extract_text_from_pdf(pdf_path)
    print(f"Extracted {len(text)} characters.")
    questions = parse_mcqs(text, subject)
    print(f"Found {len(questions)} valid MCQs.")
    saved_count = save_questions(questions)
    print(f"Saved {saved_count} new questions to database.")

if __name__ == "__main__":
    # Test with a dummy file if needed, or user can run this module directly
    pass
