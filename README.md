# Viva-LDA: Offline MPSC LDA Memory Revision System

**Viva-LDA v3.0** is a high-performance, offline memory revision system designed for MPSC LDA aspirants. It features an intelligent Spaced Repetition (SRS) engine, a premium TUI dashboard, and detailed analytics.

## ✨ New in v3.0
- **Categorized Ingestion**: Support for nested PDF structures (English, GK, etc.).
- **Bulk Ingestion Script**: `ingest_all.sh` for one-click database setup.
- **Subject Filtering**: Start sessions focused on specific subjects (e.g., `English`).
- **Enhanced TUI**: Premium styling with colored feedback and subject tagging.

## 🚀 Features
- **Visual Dashboard**: Beautiful real-time terminal dashboard with progress bars and mastery tracking.
- **Detailed Analytics**: Automatic export to `data/analytics_report.txt`.
- **Intelligent SRS**: ML-powered question prioritization based on recall performance.
- **Offline First**: All data and processing stay on your machine.

## 📦 Installation
1. **Clone & Enter**
   ```bash
   git clone https://github.com/pynshainongsiej/viva-lda.git
   cd Viva-LDA
   ```
2. **Install Deps**
   ```bash
   pip install -r requirements.txt
   ```

## 🛠 Usage

### 1. Ingesting Questions (Bulk)
To reset the database and ingest all PDFs in the `PDF/` folder:
```bash
bash ingest_all.sh
```

### 2. Manual Ingestion
```bash
# Ingest a single PDF
python3 main.py ingest "PDF/GK/MPSC LDA Biology MCQs.pdf" --subject "GK"

# Ingest an entire directory
python3 main.py ingest-dir "PDF/English" --subject "English"
```

### 3. Revision Sessions
```bash
# Standard session (Automatically opens interactive selection menu)
python3 main.py start

# Specific subject revision (Bypass menu)
python3 main.py start --subject "English" --count 15
```

## 📊 Analytics
Reports are saved to `data/analytics_report.txt` after every session, detailing:
- Mastery levels and recall rates.
- Weakest topics requiring focus.
- Historical progress logs.

## 📂 Structure
- `src/`: Core logic (UI, Session, SRS, Analytics).
- `PDF/`: Categorized study material (English / GK).
- `data/`: Local SQLite database and reports.

## 📜 License
MIT
