# -*- coding: utf-8 -*-
import sys

def inspect_file():
    with open("newdata.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines()]
    
    questions = []
    current_q = {}
    
    i = 0
    total_lines = len(lines)
    errors = []
    
    while i < total_lines:
        line = lines[i]
        if not line:
            i += 1
            continue
        
        # We expect a question block
        # Find next 5 lines
        q_text = line
        opt_a, opt_b, opt_c, opt_d, ans = "", "", "", "", ""
        
        # Read options
        try:
            if i + 1 < total_lines and lines[i+1].startswith("A."):
                opt_a = lines[i+1][2:].strip()
            else:
                errors.append((i, "Expected A. got: " + (lines[i+1] if i+1 < total_lines else "EOF")))
                i += 1
                continue
                
            if i + 2 < total_lines and lines[i+2].startswith("B."):
                opt_b = lines[i+2][2:].strip()
            else:
                errors.append((i, "Expected B. got: " + (lines[i+2] if i+2 < total_lines else "EOF")))
                i += 1
                continue
                
            if i + 3 < total_lines and lines[i+3].startswith("C."):
                opt_c = lines[i+3][2:].strip()
            else:
                errors.append((i, "Expected C. got: " + (lines[i+3] if i+3 < total_lines else "EOF")))
                i += 1
                continue
                
            if i + 4 < total_lines and lines[i+4].startswith("D."):
                opt_d = lines[i+4][2:].strip()
            else:
                errors.append((i, "Expected D. got: " + (lines[i+4] if i+4 < total_lines else "EOF")))
                i += 1
                continue
                
            if i + 5 < total_lines and lines[i+5].startswith("Ans:"):
                ans = lines[i+5][4:].strip()
            else:
                errors.append((i, "Expected Ans: got: " + (lines[i+5] if i+5 < total_lines else "EOF")))
                i += 1
                continue
                
            questions.append({
                "line_no": i + 1,
                "q": q_text,
                "a": opt_a,
                "b": opt_b,
                "c": opt_c,
                "d": opt_d,
                "ans": ans
            })
            i += 6
        except Exception as e:
            errors.append((i, "Exception: " + str(e)))
            i += 1
            
    print(f"Total parsed questions: {len(questions)}")
    print(f"Total parsing errors: {len(errors)}")
    if errors:
        print("First 10 errors:")
        for err_i, err_msg in errors[:10]:
            print(f"  Line {err_i+1}: {err_msg}")

if __name__ == "__main__":
    inspect_file()
