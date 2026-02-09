# Viva-LDA: Offline MPSC LDA Memory Revision System

**Viva-LDA** is a high-performance, offline memory revision system designed to help aspirants prepare for the MPSC LDA examination. It combines Spaced Repetition (SRS) with a rich terminal interface and detailed analytics to optimize memory retention.

## Features

-   **Visual Dashboard**: A beautiful, real-time terminal dashboard powered by `rich`, featuring progress bars, mastery tracking, and live feedback.
-   **Detailed Analytics**: Automatically exports a comprehensive text report to `data/analytics_report.txt` after every session.
-   **Spaced Repetition System (SRS)**: An intelligent memory engine (using `sklearn` SGDRegressor) tracks your performance and prioritizes weak topics.
-   **PDF Ingestion**: Automatically extracts MCQs from PDF files to populate your local database.
-   **100% Offline**: No internet required.

## Prerequisites

-   **Python 3.10+**

## Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/pynshainongsiej/viva-lda.git
    cd Viva-LDA
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### 1. Ingesting Questions
Populate the database with MCQs from your PDF study material.
```bash
python3 main.py ingest "PDF/Indian History.pdf" --subject "History"
```

### 2. Starting a Revision Session
Run the main interactive session. command-line arguments allow customization.
```bash
# Default session (10 questions)
python3 main.py start

# Custom length
python3 main.py start --count 20
```

## Analytics
After every session, a detailed report is generated at `data/analytics_report.txt`.
It includes:
-   **Overall Progress**: Total questions seen and mastery level.
-   **Subject Performance**: A clear table showing recall rates per subject.
-   **Priority Areas**: Highlights the subjects you need to focus on.
-   **Detailed Log**: A list of every question reviewed, sorted by priority.

## Project Structure
-   `src/session.py`: Manages the quiz flow and analytics export.
-   `src/memory.py`: The SRS logic and machine learning model.
-   `src/ui.py`: The Rich Dashboard component.
-   `src/analytics.py`: Data aggregation and report generation logic.
-   `data/`: Stores the SQLite database (`questions.db`) and reports.

## License
[MIT](LICENSE)
