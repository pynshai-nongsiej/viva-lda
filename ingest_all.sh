#!/bin/bash
set -e

echo "Starting bulk ingestion..."

python3 main.py ingest "PDF/MPSC LDA Biology MCQs.pdf" --subject "Biology"
python3 main.py ingest "PDF/MPSC LDA Chemistry MCQs.pdf" --subject "Chemistry"
python3 main.py ingest "PDF/MPSC LDA Economy MCQs.pdf" --subject "Economy"
python3 main.py ingest "PDF/MPSC LDA Geography MCQs.pdf" --subject "Geography"
python3 main.py ingest "PDF/MPSC LDA Indian History MCQs.pdf" --subject "Indian History"
python3 main.py ingest "PDF/MPSC LDA Miscellaneous MCQs.pdf" --subject "Miscellaneous"
python3 main.py ingest "PDF/MPSC LDA Physics MCQs.pdf" --subject "Physics"
python3 main.py ingest "PDF/MPSC LDA Polity MCQs.pdf" --subject "Polity"
python3 main.py ingest "PDF/MPSC LDA World History MCQs.pdf" --subject "World History"
python3 main.py ingest "PDF/Meghalayamindset.pdf" --subject "Meghalaya General Knowledge"

echo "All PDFs processed."
