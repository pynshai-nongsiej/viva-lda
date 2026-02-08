#!/usr/bin/env python3
import sys
import os
import argparse
from src import ingestion, session, voice

def main():
    parser = argparse.ArgumentParser(description="Offline MPSC LDA Memory Revision System")
    parser.add_argument("--debug", action="store_true", help="Enable text-only debug mode (no voice)")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Ingest Command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest a PDF file")
    ingest_parser.add_argument("pdf_path", help="Path to the PDF file")
    ingest_parser.add_argument("--subject", default="General", help="Subject tag for questions")

    # Start Session Command
    start_parser = subparsers.add_parser("start", help="Start a revision session")
    start_parser.add_argument("-n", "--count", type=int, default=10, help="Number of questions")

    args = parser.parse_args()
    
    # Set global debug mode
    if args.debug:
        voice.DEBUG_MODE = True
        print("DEBUG MODE ENABLED: Voice disabled. Use text input.")

    if args.command == "ingest":
        if not os.path.exists(args.pdf_path):
            print(f"Error: File not found: {args.pdf_path}")
            return
        ingestion.ingest_pdf(args.pdf_path, args.subject)

    elif args.command == "start":
        # Check model first only if NOT in debug mode
        if not voice.DEBUG_MODE:
            try:
                voice.load_stt_model()
            except FileNotFoundError:
                print("Vosk model not found. Attempting to download...")
                print("Please run the setup script or download the model manually.")
                return
            except Exception as e:
                print(f"Error initializing voice system: {e}")
                return
            
        mgr = session.SessionManager()
        mgr.run_session(count=args.count)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
