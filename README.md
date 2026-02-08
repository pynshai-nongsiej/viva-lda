# Viva-LDA: Offline MPSC LDA Memory Revision System

**Viva-LDA** is a high-performance, offline, voice-interactive revision system designed to help aspirants prepare for the MPSC LDA examination. It combines Spaced Repetition (SRS) with a conversational interface and real-time visual analytics to optimize memory retention.

## Features

-   **Pro-Grade Voice Interaction**: 
    -   **TTS**: Reads questions using high-quality neural models (Jenny Dioco).
    -   **STT**: Listens to your answers using **Faster-Whisper** (small.en) for near-human accuracy with Indian accents.
-   **Visual Dashboard**: A beautiful, real-time terminal dashboard powered by `rich`, featuring progress bars, mastery tracking, and live feedback.
-   **Excel Analytics**: Automatically exports detailed session data to `data/analytics_dashboard.xlsx` for long-term tracking.
-   **Spaced Repetition System (SRS)**: An intelligent memory engine (using `sklearn` SGDRegressor) tracks your performance and prioritizes weak topics.
-   **PDF Ingestion**: Automatically extracts MCQs from PDF files to populate your local database.
-   **100% Offline**: No internet required after initial setup.

## Prerequisites

-   **Python 3.10+**
-   **Audio Hardware**: Microphone and Speakers.
-   **System libraries**:
    -   **macOS**: `brew install portaudio` (Required for microphone access)
    -   **Linux**: `sudo apt-get install portaudio19-dev`

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

3.  **Download TTS Model**
    -   Download `en_GB-jenny_dioco-medium.onnx` and `en_GB-jenny_dioco-medium.onnx.json`.
    -   Place them in `models/piper/`.
    *(Note: The Whisper STT model will download automatically on the first run ~480MB)*

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

### 3. Debug Mode (Silent)
Test the logic without voice interaction.
```bash
python3 main.py --debug start
```

## Analytics
After every session, a detailed report is generated at `data/analytics_report.txt`.
It includes:
-   **Overall Progress**: Total questions seen and mastery level.
-   **Subject Performance**: A clear table showing recall rates per subject.
-   **Priority Areas**: Highlights the subjects you need to focus on.
-   **Detailed Log**: A list of every question reviewed, sorted by priority.

## Project Structure
-   `src/session.py`: Manages the quiz flow and Excel export.
-   `src/voice.py`: Handles Neural TTS and Whisper STT.
-   `src/memory.py`: The SRS logic and machine learning model.
-   `src/ui.py`: The Rich Dashboard component.
-   `src/analytics.py`: Data aggregation and Excel export logic.
-   `data/`: Stores the SQLite database (`questions.db`) and Excel reports.

## License
[MIT](LICENSE)
