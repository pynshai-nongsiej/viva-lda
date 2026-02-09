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
    """Extracts raw text with gap detection for Fill in the Blanks."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words(x_tolerance=2, y_tolerance=2)
            if not words: continue
            
            # Sort words by top then left
            words.sort(key=lambda w: (w['top'], w['x0']))
            
            current_line_top = words[0]['top']
            line_text = ""
            for i, w in enumerate(words):
                # New line detection (y-threshold of 5)
                if abs(w['top'] - current_line_top) > 5:
                    text += line_text.strip() + "\n"
                    line_text = ""
                    current_line_top = w['top']
                
                # Gap detection within the same line
                if i > 0 and abs(w['top'] - current_line_top) <= 5:
                    prev_w = words[i-1]
                    gap = w['x0'] - prev_w['x1']
                    
                    # Detect potential "Fill in the Blank" gaps
                    # Only insert if gap is moderate (likely a blank) and not just trailing space before [Ans:]
                    if 25 < gap < 100: 
                        line_text += " _______ "
                    elif gap > 2:
                        line_text += " "
                
                line_text += w['text']
            
            text += line_text.strip() + "\n"
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
                
            # 2. Extract Options
            opts = {}
            current_opt = None
            
            for line in lines[1:]:
                line = line.strip()
                if not line or re.match(r'^\d+$', line): continue
                
                opt_match = re.match(r'^\(?([a-d])\)[\.\s]\s*(.*)', line, re.IGNORECASE)
                if opt_match:
                    current_opt = opt_match.group(1).upper()
                    opts[current_opt] = opt_match.group(2).strip()
                elif current_opt:
                    opts[current_opt] += " " + line

            # 3. Fallback for horizontal options (typical in Error Detection)
            if not opts or len(opts) < 2:
                # Look for (A) / (B) / (C) / (D)
                if "(A)" in q_line and "(B)" in q_line:
                    opts = {'A': 'Part (A)', 'B': 'Part (B)', 'C': 'Part (C)', 'D': 'Part (D)'}
                # Look for sentence improvement answers like [Ans: (C) are]
                elif ans_match and "No improvement" in block:
                     opts = {'A': '-', 'B': '-', 'C': '-', 'D': 'No improvement'}

            # 4. Final Fallback for Answer
            if not correct_ans:
                ans_match_end = re.search(r'Answer:\s*\(?([a-d])\)?', block, re.IGNORECASE)
                if ans_match_end:
                    correct_ans = ans_match_end.group(1).upper()
            
            if correct_ans and ('A' in opts or 'D' in opts):
                # Ensure all options exist to avoid DB errors
                q_data = (
                    subject,
                    q_text,
                    opts.get('A', 'Option A'),
                    opts.get('B', 'Option B'),
                    opts.get('C', 'Option C'),
                    opts.get('D', 'Option D'),
                    correct_ans
                )
                questions.append(q_data)
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
    print(f"Processing {pdf_path} for subject: {subject}...")
    init_db()
    text = extract_text_from_pdf(pdf_path)
    if not text.strip():
        print(f"Warning: No text extracted from {pdf_path}")
        return
    print(f"Extracted {len(text)} characters.")
    questions = parse_mcqs(text, subject)
    print(f"Found {len(questions)} valid MCQs.")
    saved_count = save_questions(questions)
    print(f"Saved {saved_count} new questions to database.")

def ingest_directory(directory_path, base_subject=None):
    """Recursively ingest all PDFs in a directory."""
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.lower().endswith(".pdf"):
                full_path = os.path.join(root, file)
                
                # Derive a clean sub-subject from filename
                # Remove common prefixes like "MPSC LDA " and extension
                sub_subject = file
                sub_subject = re.sub(r'^(MPSC\s+LDA|MPSC\s+Meghalaya\s+LDA)\s+', '', sub_subject, flags=re.IGNORECASE)
                sub_subject = re.sub(r'\.pdf$', '', sub_subject, flags=re.IGNORECASE)
                sub_subject = re.sub(r'\s*MCQs$', '', sub_subject, flags=re.IGNORECASE)
                
                if base_subject:
                    subject = f"{base_subject} - {sub_subject}"
                else:
                    # Use directory name as base if nothing else
                    parent_dir = os.path.basename(root)
                    if parent_dir and parent_dir != os.path.basename(directory_path):
                         subject = f"{parent_dir} - {sub_subject}"
                    else:
                         subject = sub_subject
                         
                ingest_pdf(full_path, subject)

if __name__ == "__main__":
    # Test with a dummy file if needed, or user can run this module directly
    pass
