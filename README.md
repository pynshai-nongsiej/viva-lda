# Viva-LDA: Offline MPSC LDA Memory Revision System

**Viva-LDA** is an offline, voice-interactive revision system designed to help aspirants prepare for the MPSC LDA (Meghalaya Public Service Commission - Lower Division Assistant) examination. It combines Spaced Repetition (SRS) with a conversational interface to optimize memory retention.

## Features

-   **Voice-Interactive Quizzes**: The system reads questions and options aloud, and you answer by speaking (A, B, C, D).
-   **Spaced Repetition System (SRS)**: An intelligent memory engine (using `sklearn` SGDRegressor) tracks your performance and schedules reviews based on your recall probability.
-   **PDF Ingestion**: Automatically extracting Multiple Choice Questions (MCQs) from PDF files to build your question database.
-   **Offline First**: Designed to run locally without internet access, using offline text-to-speech (Piper) and speech-to-text (VosK/Whisper) models.
-   **Rich Terminal UI**: A beautiful dashboard powered by `rich` to visualize your session progress.

## Prerequisites

-   **Python 3.8+**
-   **macOS** (Verified on macOS, likely works on Linux with adjustments)
-   **Audio Hardware**: Microphone and Speakers

## Installation

1.  **Clone the Repository**
    ```bash
    git clone <your-repo-url>
    cd Viva-LDA
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Download Voice Models**
    The system requires external models for speech processing. These are too large for GitHub and must be placed in the `models/` directory.

    -   **Text-to-Speech (Piper)**:
        -   Download the `en_GB-jenny_dioco-medium.onnx` and its JSON config.
        -   Place them in `models/piper/`.
    -   **Speech-to-Text (Whisper)**:
        -   The system uses `faster-whisper`. It will attempt to download the `small.en` model automatically on the first run, or you can pre-download it.

    *Note: Ensure your `models/` directory structure looks like this:*
    ```
    models/
    └── piper/
        ├── en_GB-jenny_dioco-medium.onnx
        └── en_GB-jenny_dioco-medium.onnx.json
    ```

## Usage

### 1. Ingesting Questions
Before starting a session, you need to populate the database with questions from your study material (PDFs).

```bash
# Syntax
python3 main.py ingest <path_to_pdf> --subject "<Subject Name>"

# Example
python3 main.py ingest "PDF/Indian History.pdf" --subject "History"
```
*Note: The ingestion script expects MCQs in a specific format (Question followed by Options A/B/C/D).*

### 2. Starting a Revision Session
Run the main interactive session. The system will select questions based on your memory needs.

```bash
# Start a session with default 10 questions
python3 main.py start

# Start a session with 20 questions
python3 main.py start -n 20
```

### 3. Debug Mode (No Voice)
If you want to test the logic without speaking, use the debug flag. You can type your answers.

```bash
python3 main.py start --debug
```

## Project Structure

-   `main.py`: Entry point for the application.
-   `src/session.py`: Manages the quiz flow and selects questions.
-   `src/voice.py`: Handles TTS and STT operations.
-   `src/memory.py`: The "brain" containing the SRS logic and machine learning model.
-   `src/ingestion.py`: Logic for parsing PDFs.
-   `src/ui.py`: Dashboard rendering.
-   `data/`: Stores the SQLite database (`questions.db`).
-   `models/`: Stores the AI models (ignored by git).

## License
[MIT](LICENSE)
