#!/bin/bash
set -e

echo "Starting bulk ingestion for categorized PDFs..."

# Ingest English Category
echo "Ingesting English MCQs..."
python3 main.py ingest-dir "PDF/English" --subject "English"

# Ingest GK Category
echo "Ingesting GK MCQs..."
python3 main.py ingest-dir "PDF/GK" --subject "GK"

echo "All PDFs processed and database updated."
