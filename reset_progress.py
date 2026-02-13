import sqlite3
import os
import shutil

DB_PATH = "data/questions.db"
MODELS_DIR = "models"
ANALYTICS_FILE = "data/analytics_report.txt"

def reset_database():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    print("Resetting database progress...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Reset progress-related columns
        cursor.execute("""
            UPDATE questions 
            SET review_count = 0, 
                last_reviewed_at = NULL, 
                recall_score = 0
        """)
        
        conn.commit()
        conn.close()
        print("Done: Database progress reset.")
    except Exception as e:
        print(f"Error resetting database: {e}")

def delete_models():
    if os.path.exists(MODELS_DIR):
        print("Cleaning up ML models...")
        try:
            shutil.rmtree(MODELS_DIR)
            os.makedirs(MODELS_DIR) # Recreate empty dir
            print("Done: ML models cleared.")
        except Exception as e:
            print(f"Error deleting models: {e}")
    else:
        print("Models directory not found. Skipping.")

def delete_analytics():
    if os.path.exists(ANALYTICS_FILE):
        print("Deleting analytics report...")
        try:
            os.remove(ANALYTICS_FILE)
            print("Done: Analytics report deleted.")
        except Exception as e:
            print(f"Error deleting analytics file: {e}")
    else:
        print("Analytics file not found. Skipping.")

def main():
    print("=== Viva-LDA Progress Reset Utility ===")
    print("Warning: This will PERMANENTLY delete your learning progress.")
    print("Ingested questions will be preserved, but scores and history will be cleared.")
    
    # Confirmation prompt
    confirm = input("\nAre you sure you want to proceed? (yes/no): ").lower()
    if confirm == 'yes':
        reset_database()
        delete_models()
        delete_analytics()
        print("\nReset Complete. You can now start a fresh session.")
    else:
        print("\nReset aborted.")

if __name__ == "__main__":
    main()
