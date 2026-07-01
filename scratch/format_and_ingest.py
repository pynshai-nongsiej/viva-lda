# -*- coding: utf-8 -*-
import os
import csv
import sys

def parse_and_format():
    print("Parsing newdata.txt...")
    with open("newdata.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines()]
        
    questions = []
    i = 0
    total_lines = len(lines)
    
    while i < total_lines:
        line = lines[i]
        if not line:
            i += 1
            continue
            
        q_text = line
        opt_a = lines[i+1][2:].strip()
        opt_b = lines[i+2][2:].strip()
        opt_c = lines[i+3][2:].strip()
        opt_d = lines[i+4][2:].strip()
        ans_text = lines[i+5][4:].strip()
        
        questions.append({
            "q": q_text,
            "a": opt_a,
            "b": opt_b,
            "c": opt_c,
            "d": opt_d,
            "ans": ans_text
        })
        i += 6

    print(f"Successfully parsed {len(questions)} questions.")
    
    # 1. Overwrite newdata.txt cleanly with numbering
    print("Writing formatted newdata.txt...")
    with open("newdata.txt", "w", encoding="utf-8") as f:
        for idx, q in enumerate(questions, 1):
            f.write(f"{idx}. {q['q']}\n")
            f.write(f"   A. {q['a']}\n")
            f.write(f"   B. {q['b']}\n")
            f.write(f"   C. {q['c']}\n")
            f.write(f"   D. {q['d']}\n")
            f.write(f"   Ans: {q['ans']}\n\n")

    # 2. Write csv/newdata.csv
    print("Writing csv/newdata.csv...")
    os.makedirs("csv", exist_ok=True)
    with open("csv/newdata.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Topic", "Subtopic", "Pattern", "Question", "A", "B", "C", "D", "Answer", "Source"])
        for q in questions:
            # Map subtopic
            subtopic = "General"
            q_lower = q["q"].lower()
            if "river" in q_lower or "lake" in q_lower or "ocean" in q_lower or "state" in q_lower or "capital" in q_lower or "border" in q_lower or "planet" in q_lower or "solar" in q_lower or "valley" in q_lower or "island" in q_lower or "desert" in q_lower or "peak" in q_lower or "soil" in q_lower or "mountain" in q_lower:
                subtopic = "Geography"
            elif "king" in q_lower or "emperor" in q_lower or "dynasty" in q_lower or "established" in q_lower or "founded" in q_lower or "revolt" in q_lower or "tragedy" in q_lower or "first female ruler" in q_lower or "invented" in q_lower or "historical" in q_lower or "battle" in q_lower or "war" in q_lower or "mutiny" in q_lower or "movement" in q_lower or "massacre" in q_lower or "partitioned" in q_lower or "ancient" in q_lower or "timeline" in q_lower:
                subtopic = "History"
            elif "article" in q_lower or "constitution" in q_lower or "amendment" in q_lower or "president" in q_lower or "governor" in q_lower or "supreme commander" in q_lower or "high court" in q_lower or "judges" in q_lower or "right" in q_lower or "sabha" in q_lower or "parliament" in q_lower or "court" in q_lower or "minister" in q_lower or "law" in q_lower or "emergency" in q_lower or "officer" in q_lower or "bill" in q_lower:
                subtopic = "Polity"
            elif "cup" in q_lower or "trophy" in q_lower or "sport" in q_lower or "game" in q_lower or "player" in q_lower or "olympic" in q_lower or "cricket" in q_lower or "gymnastic" in q_lower or "award" in q_lower or "nobel" in q_lower:
                subtopic = "Sports"
            elif "vitamin" in q_lower or "disease" in q_lower or "organ" in q_lower or "gland" in q_lower or "scientific name" in q_lower or "blood" in q_lower or "glass" in q_lower or "gas" in q_lower or "chemical" in q_lower or "metal" in q_lower or "bone" in q_lower or "si unit" in q_lower or "electric" in q_lower or "photosynthesis" in q_lower or "cell" in q_lower or "study of" in q_lower or "layer of atmosphere" in q_lower:
                subtopic = "Science"
            elif "computer" in q_lower or "shortcut" in q_lower or "program" in q_lower or "www" in q_lower or "telegraph" in q_lower:
                subtopic = "Computer"
            
            # Special check for Meghalaya questions
            if "meghalaya" in q_lower or "shillong" in q_lower or "khasi" in q_lower or "garo" in q_lower or "jaintia" in q_lower or "sohra" in q_lower or "mawsynram" in q_lower or "tura" in q_lower:
                subtopic = "Meghalaya"

            writer.writerow([
                "GK",
                subtopic,
                "Standard MCQ",
                q["q"],
                q["a"],
                q["b"],
                q["c"],
                q["d"],
                q["ans"],
                "NewDataTxt"
            ])
            
    print("CSV written successfully.")

    # 3. Add to the database using the project's ingestion system
    print("Ingesting questions into the SQLite database...")
    sys.path.append(os.path.abspath("."))
    from src import ingestion
    ingestion.ingest_csv("csv/newdata.csv")

if __name__ == "__main__":
    parse_and_format()
