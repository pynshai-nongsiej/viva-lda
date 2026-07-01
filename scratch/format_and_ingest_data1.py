# -*- coding: utf-8 -*-
import os
import re
import csv
import sys

def parse_data1():
    print("Parsing data1.txt...")
    with open("data1.txt", "r", encoding="utf-8") as f:
        content = f.read()
        
    # Split content by "Q" followed by digits followed by "."
    # We can use a regex to find all question starts: e.g. r'Q\d+\.'
    # But wait, Q85 has statements etc. Let's do a line-by-line check.
    lines = [line.strip() for line in content.split("\n")]
    
    questions = []
    i = 0
    total_lines = len(lines)
    
    while i < total_lines:
        line = lines[i]
        match = re.match(r'^Q(\d+)\.\s*(.*)', line)
        if match:
            q_num = int(match.group(1))
            q_first_line = match.group(2)
            
            # Read until (A) is found
            q_lines = [q_first_line]
            i += 1
            while i < total_lines and not lines[i].startswith("(A)"):
                if lines[i]:
                    q_lines.append(lines[i])
                i += 1
                
            q_text = "\n".join(q_lines).strip()
            
            # Parse options
            opt_a, opt_b, opt_c, opt_d, ans_letter = "", "", "", "", ""
            
            if i < total_lines and lines[i].startswith("(A)"):
                opt_a = lines[i][3:].strip()
                i += 1
            if i < total_lines and lines[i].startswith("(B)"):
                opt_b = lines[i][3:].strip()
                i += 1
            if i < total_lines and lines[i].startswith("(C)"):
                opt_c = lines[i][3:].strip()
                i += 1
            if i < total_lines and lines[i].startswith("(D)"):
                opt_d = lines[i][3:].strip()
                i += 1
                
            # Find the answer line
            while i < total_lines and not (lines[i].startswith("Answer:") or lines[i].startswith("Ans:")):
                i += 1
                
            if i < total_lines:
                ans_line = lines[i]
                ans_match = re.search(r'\(([A-D])\)', ans_line)
                if ans_match:
                    ans_letter = ans_match.group(1)
                i += 1
                
            # Get correct answer text
            ans_text = ""
            if ans_letter == "A":
                ans_text = opt_a
            elif ans_letter == "B":
                ans_text = opt_b
            elif ans_letter == "C":
                ans_text = opt_c
            elif ans_letter == "D":
                ans_text = opt_d
                
            questions.append({
                "num": q_num,
                "q": q_text,
                "a": opt_a,
                "b": opt_b,
                "c": opt_c,
                "d": opt_d,
                "ans_letter": ans_letter,
                "ans_text": ans_text
            })
        else:
            i += 1
            
    return questions

def main():
    questions = parse_data1()
    print(f"Parsed {len(questions)} questions.")
    
    # Check for any missing fields
    errors = []
    for q in questions:
        if not q["q"]:
            errors.append(f"Q{q['num']}: Missing question text")
        if not q["a"] or not q["b"] or not q["c"] or not q["d"]:
            errors.append(f"Q{q['num']}: Missing one or more options")
        if not q["ans_letter"] or not q["ans_text"]:
            errors.append(f"Q{q['num']}: Missing answer or option mapping")
            
    if errors:
        print(f"Validation errors found: {len(errors)}")
        for e in errors[:10]:
            print("  ", e)
        # We don't stop if they are minor, but let's see
    else:
        print("All questions validated successfully!")
        
    # 1. Format data1.txt in place
    print("Writing cleanly formatted data1.txt...")
    with open("data1.txt", "w", encoding="utf-8") as f:
        f.write("MPSC Lower Division Assistant (LDA) Predicted Paper\n\n")
        
        # We can write it by parts
        current_part = None
        for q in sorted(questions, key=lambda x: x["num"]):
            num = q["num"]
            # Determine if we should print a part header
            part = None
            if 1 <= num <= 50:
                part = "PART-A: GENERAL ENGLISH"
            elif 51 <= num <= 75:
                part = "PART-B: COMPUTER KNOWLEDGE"
            elif 76 <= num <= 95:
                part = "PART-C: GENERAL REASONING"
            elif 96 <= num <= 110:
                part = "PART-D: GENERAL APTITUDE"
                
            if part != current_part:
                f.write(f"{'='*72}\n")
                f.write(f"{part}\n")
                f.write(f"{'='*72}\n\n")
                current_part = part
                
            # Write question
            f.write(f"{num}. {q['q']}\n")
            f.write(f"   A. {q['a']}\n")
            f.write(f"   B. {q['b']}\n")
            f.write(f"   C. {q['c']}\n")
            f.write(f"   D. {q['d']}\n")
            f.write(f"   Ans: {q['ans_text']}\n\n")
            
    # 2. Write csv/data1.csv
    print("Writing csv/data1.csv...")
    os.makedirs("csv", exist_ok=True)
    with open("csv/data1.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Topic", "Subtopic", "Pattern", "Question", "A", "B", "C", "D", "Answer", "Source"])
        for q in questions:
            num = q["num"]
            topic = "GK"
            subtopic = "General"
            
            if 1 <= num <= 50:
                topic = "English"
                subtopic = "General"
            elif 51 <= num <= 75:
                topic = "GK"
                subtopic = "Computer"
            elif 76 <= num <= 95:
                topic = "GK"
                subtopic = "Reasoning"
            elif 96 <= num <= 110:
                topic = "GK"
                subtopic = "Aptitude"
                
            writer.writerow([
                topic,
                subtopic,
                "Standard MCQ",
                q["q"],
                q["a"],
                q["b"],
                q["c"],
                q["d"],
                q["ans_text"],
                "data1"
            ])
            
    print("CSV written successfully.")
    
    # 3. Ingest into database
    print("Ingesting questions into questions.db...")
    sys.path.append(os.path.abspath("."))
    from src import ingestion
    ingestion.ingest_csv("csv/data1.csv")
    print("Ingestion complete.")

if __name__ == "__main__":
    main()
