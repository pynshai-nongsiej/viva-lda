#!/usr/bin/env python3
import sys
import os
import argparse
from src import ingestion, session

def main():
    parser = argparse.ArgumentParser(description="Offline MPSC LDA Memory Revision System")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Ingest Command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest a PDF file")
    ingest_parser.add_argument("pdf_path", help="Path to the PDF file")
    ingest_parser.add_argument("--subject", default="General", help="Subject tag for questions")

    # Start Session Command
    start_parser = subparsers.add_parser("start", help="Start a revision session")
    start_parser.add_argument("-n", "--count", type=int, default=10, help="Number of questions")

    args = parser.parse_args()
    
    if args.command == "ingest":
        if not os.path.exists(args.pdf_path):
            print(f"Error: File not found: {args.pdf_path}")
            return
        ingestion.ingest_pdf(args.pdf_path, args.subject)

    elif args.command == "start":
        mgr = session.SessionManager()
        mgr.run_session(count=args.count)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
