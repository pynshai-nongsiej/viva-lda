import sqlite3
import datetime

DB_PATH = "data/questions.db"

class AnalyticsEngine:
    def __init__(self):
        self.conn = None

    def _get_conn(self):
        if not self.conn:
            self.conn = sqlite3.connect(DB_PATH)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def get_overall_stats(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # Total Questions
        cursor.execute("SELECT COUNT(*) FROM questions")
        total = cursor.fetchone()[0]
        
        # Reviewed vs New
        cursor.execute("SELECT COUNT(*) FROM questions WHERE review_count > 0")
        reviewed = cursor.fetchone()[0]
        new = total - reviewed
        
        # Mastery (Avg Recall of reviewed items)
        cursor.execute("SELECT AVG(recall_score) FROM questions WHERE review_count > 0")
        mastery = cursor.fetchone()[0]
        mastery = mastery if mastery else 0.0
        
        return {
            "total": total,
            "reviewed": reviewed,
            "new": new,
            "mastery": mastery * 100 # percentage
        }

    def get_subject_performance(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        
        sql = """
            SELECT subject, 
                   COUNT(*) as total, 
                   AVG(recall_score) as avg_recall,
                   SUM(CASE WHEN review_count > 0 THEN 1 ELSE 0 END) as reviewed_count
            FROM questions 
            GROUP BY subject
            ORDER BY avg_recall ASC
        """
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        stats = []
        for r in rows:
            recall = r['avg_recall'] if r['avg_recall'] else 0.0
            stats.append({
                "subject": r['subject'],
                "total": r['total'],
                "reviewed": r['reviewed_count'],
                "recall": recall * 100
            })
        return stats

    def get_mastery_prediction(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # 1. Total and Mastered
        cursor.execute("SELECT COUNT(*) FROM questions")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM questions WHERE recall_score >= 0.9")
        mastered = cursor.fetchone()[0]
        remaining = total - mastered
        
        # 2. Velocity: Questions mastered in the last 24 hours
        one_day_ago = (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()
        cursor.execute("SELECT COUNT(*) FROM questions WHERE last_reviewed_at >= ? AND recall_score >= 0.9", (one_day_ago,))
        velocity = cursor.fetchone()[0]
        
        # Fallback if no activity today: check last 7 days average
        if velocity == 0:
            seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()
            cursor.execute("SELECT COUNT(*) FROM questions WHERE last_reviewed_at >= ? AND recall_score >= 0.9", (seven_days_ago,))
            velocity_7d = cursor.fetchone()[0]
            velocity = velocity_7d / 7.0 if velocity_7d > 0 else 0
            
        days_left = remaining / velocity if velocity > 0 else float('inf')
        
        return {
            "total": total,
            "mastered": mastered,
            "remaining": remaining,
            "velocity": velocity, # mastered per day
            "days_left": days_left
        }

    def get_weakest_topics(self, limit=5):
        stats = self.get_subject_performance()
        # Filter for subjects with at least some activity to avoid noise
        active_stats = [s for s in stats if s['reviewed'] > 0]
        # Sort by recall ascending
        return sorted(active_stats, key=lambda x: x['recall'])[:limit]

    def export_to_text(self, filename="data/analytics_report.txt"):
        import os
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        conn = self._get_conn()
        cursor = conn.cursor()
        
        lines = []
        lines.append("="*60)
        lines.append(f"VIVA-LDA DASHBOARD REPORT - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("="*60)
        lines.append("")
        
        # 1. OVERALL STATISTICS
        overall = self.get_overall_stats()
        lines.append("## OVERALL PROGRESS")
        lines.append("-" * 30)
        lines.append(f"Total Questions:  {overall['total']}")
        lines.append(f"Questions Seen:   {overall['reviewed']} ({overall['reviewed']/overall['total']*100:.1f}%)")
        lines.append(f"Mastery Level:    {overall['mastery']:.1f}%")
        lines.append("")
        
        # 2. SUBJECT PERFORMANCE
        lines.append("## SUBJECT PERFORMANCE")
        lines.append("-" * 60)
        lines.append(f"{'Subject':<25} | {'Questions':<10} | {'Recall %':<10}")
        lines.append("-" * 60)
        
        subjects = self.get_subject_performance()
        if not subjects:
             lines.append("No data available yet.")
        else:
            for s in subjects:
                sub_name = s['subject'][:23]
                lines.append(f"{sub_name:<25} | {s['reviewed']:<10} | {s['recall']:.1f}%")
        lines.append("")
        
        # 3. PRIORITY FOCUS AREAS (Weak Subjects)
        lines.append("## WEAKEST AREAS (Priority Focus)")
        lines.append("-" * 60)
        weak_topics = self.get_weakest_topics(limit=5)
        if not weak_topics:
            lines.append("No weak areas identified yet.")
        else:
             for t in weak_topics:
                 lines.append(f"[!] {t['subject']}: {t['recall']:.1f}% Recall")
        lines.append("")

        # 4. DETAILED QUESTION LOG (Weakest First)
        lines.append("## DETAILED QUESTION ANALYSIS (Lowest Recall First)")
        lines.append("=" * 80)
        
        query = """
            SELECT id, subject, question_text, correct_answer, recall_score, review_count, last_reviewed_at
            FROM questions
            WHERE review_count > 0
            ORDER BY recall_score ASC, last_reviewed_at DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if not rows:
            lines.append("No questions reviewed yet.")
        else:
            for r in rows:
                lines.append(f"ID: {r['id']} | Subject: {r['subject']}")
                lines.append(f"Q:  {r['question_text']}")
                lines.append(f"A:  {r['correct_answer']}")
                
                # Contextual status
                score = r['recall_score']
                status = "CRITICAL" if score < 0.3 else "WEAK" if score < 0.6 else "GOOD" if score < 0.9 else "MASTERED"
                
                lines.append(f"Stats: Recall={score:.2f} ({status}) | Reviewed={r['review_count']}x | Last: {r['last_reviewed_at'][:16]}")
                lines.append("-" * 80)
        
        # 5. ML MASTERY PREDICTION
        prediction = self.get_mastery_prediction()
        lines.append("")
        lines.append("## ML MASTERY FORECAST")
        lines.append("=" * 60)
        lines.append(f"Remaining Questions: {prediction['remaining']}")
        lines.append(f"Current Velocity:    {prediction['velocity']:.1f} questions/day")
        
        if prediction['days_left'] == float('inf'):
            lines.append("Timeline: Unable to estimate (No mastery activity recorded)")
        else:
            completion_date = (datetime.datetime.now() + datetime.timedelta(days=prediction['days_left'])).strftime('%Y-%m-%d')
            lines.append(f"Est. Completion:    In {prediction['days_left']:.1f} days")
            lines.append(f"Projected Mastery:  {completion_date}")
        lines.append("=" * 60)
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return True
        except Exception as e:
            print(f"Error exporting text report: {e}")
            return False

    def close(self):
        if self.conn:
            self.conn.close()
