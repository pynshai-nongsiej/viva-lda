import sqlite3
import numpy as np
import pickle
import os
import time
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler
from datetime import datetime

# Feature definitions:
# 1. Repetition Count
# 2. Days since last review
# 3. Previous Recall Prob (or average score history)
# 4. Last Response Time (normalized)

MODEL_PATH = "models/memory_model.pkl"
SCALER_PATH = "models/scaler.pkl"
DB_PATH = "data/questions.db"

class MemoryEngine:
    def __init__(self):
        self.model = SGDRegressor(loss='squared_error', penalty='l2', learning_rate='invscaling', eta0=0.01)
        self.scaler = StandardScaler()
        self.is_fitted = False
        self._load_model()

    def _load_model(self):
        if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
            try:
                with open(MODEL_PATH, 'rb') as f:
                    self.model = pickle.load(f)
                with open(SCALER_PATH, 'rb') as f:
                    self.scaler = pickle.load(f)
                self.is_fitted = True
                print("Loaded existing memory model.")
            except Exception as e:
                print(f"Failed to load model: {e}. Starting fresh.")
        else:
            print("No existing model found. Starting fresh.")
            # Initialize with dummy data to enable partial_fit immediately if needed
            # Or handle first fit carefully
    
    def _save_model(self):
        os.makedirs("models", exist_ok=True)
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(self.model, f)
        with open(SCALER_PATH, 'wb') as f:
            pickle.dump(self.scaler, f)

    def get_features(self, question_data):
        """
        Constructs feature vector from question data.
        question_data: tuple or dict containing:
        - review_count
        - last_reviewed_at (timestamp)
        - (optional) avg_response_time or similar interaction history
        """
        # For simplicity, let's assume we fetch these from DB or pass them in
        # We need to calculate 'days_since_last_review'
        
        last_reviewed = question_data.get('last_reviewed_at')
        if not last_reviewed:
            days_since = 1000.0 # Treat new questions as "very old" or handle separately? 
            # Actually, new questions have likelihood 0 of recall if never seen, 
            # but usually we want to PRIORITIZE them.
            # Let's say days_since = 0 for new? No, that implies immediate review.
            days_since = 0.0 
        else:
            # Parse timestamp if string
            if isinstance(last_reviewed, str):
                try:
                    last_ts = datetime.fromisoformat(last_reviewed).timestamp()
                except:
                    last_ts = time.time() # validation fallback
            else:
                last_ts = last_reviewed
            
            days_since = (time.time() - last_ts) / (86400.0)
            
        review_count = question_data.get('review_count', 0)
        
        # Feature vector: [review_count, days_since]
        # We can add more 'classical' features later
        return np.array([[review_count, days_since]])

    def train(self, features, label):
        """
        updates the model with new experience.
        label: 1.0 (Correct), 0.0 (Incorrect)
        """
        # If not fitted, we need to fit on a batch or use partial_fit with classes?
        # SGDRegressor is strictly regression. Label is float.
        
        # We need to scale features first. 
        # For SGD, scaling is critical. 
        # Ideally, we partial_fit the scaler too, but StandardScaler doesn't support partial_fit well without mean/var history.
        # Simple fix: Re-fit scaler on current batch? No, that forgets history.
        # Use `partial_fit` on scaler provided by sklearn in newer versions or manual scaling.
        # Let's implementation a simple manual scaling or assume ranges.
        # Or just use the scaler's partial_fit if available. (It is available in 1.3+)
        
        self.scaler.partial_fit(features)
        X_scaled = self.scaler.transform(features)
        
        self.model.partial_fit(X_scaled, [label])
        self.is_fitted = True
        self._save_model()

    def predict_recall(self, features):
        if not self.is_fitted:
            # Heuristic fallback if model is cold
            # New questions (review_count=0) -> 0.0 recall (force review)
            # Old questions -> decays with time
            return 0.5 
            
        X_scaled = self.scaler.transform(features)
        prediction = self.model.predict(X_scaled)[0]
        return max(0.0, min(1.0, prediction)) # Clip to [0, 1]

    def update_question_stats(self, question_id, is_correct, response_time):
        """
        Updates the DB with the result of a review and triggers model training.
        """
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get current stats
        cursor.execute("SELECT review_count, last_reviewed_at FROM questions WHERE id=?", (question_id,))
        row = cursor.fetchone()
        
        if not row:
            return
            
        old_count, last_ts = row
        old_count = old_count if old_count else 0
        
        # Prepare features for training (state BEFORE this review)
        features = self.get_features({
            'review_count': old_count,
            'last_reviewed_at': last_ts
        })
        
        # Label: 1.0 if correct, else 0.0
        # Maybe weight by response time? 
        # If correct but slow (e.g. > 10s), label = 0.5?
        target = 1.0 if is_correct else 0.0
        if is_correct and response_time > 10.0:
            target = 0.7 # "Hard" correct
        
        # Train model
        self.train(features, target)
        
        # Update DB
        new_count = old_count + 1
        new_ts = datetime.now().isoformat()
        
        # Predict NEW recall score for scheduling (future state)
        # We can just store the model's current prediction for "now", but scheduling 
        # looks at the *lowest* recall score.
        # Just update the record with the target so we have history, 
        # or store the model's prediction for ONE DAY from now?
        # Let's store the current 'strength' (0-1).
        
        cursor.execute("""
            UPDATE questions 
            SET review_count=?, last_reviewed_at=?, recall_score=?
            WHERE id=?
        """, (new_count, new_ts, target, question_id))
        
        conn.commit()
        conn.close()

if __name__ == "__main__":
    # Smoke test
    mem = MemoryEngine()
    feats = np.array([[1, 0.5]]) # 1 review, 0.5 days ago
    print("Prediction:", mem.predict_recall(feats))
    mem.train(feats, 1.0)
    print("Prediction after training:", mem.predict_recall(feats))
