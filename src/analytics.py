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

    def get_weakest_topics(self, limit=5):
        stats = self.get_subject_performance()
        # Filter for subjects with at least some activity to avoid noise
        active_stats = [s for s in stats if s['reviewed'] > 0]
        # Sort by recall ascending
        return sorted(active_stats, key=lambda x: x['recall'])[:limit]

    def close(self):
        if self.conn:
            self.conn.close()
