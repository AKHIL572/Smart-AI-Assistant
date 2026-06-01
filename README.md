# Smart AI Assistant

> A multi-tool AI assistant built with Streamlit and Google Gemini — chat with AI, analyze food images, summarize YouTube videos, and query PDF documents, all in one app.

---

## Overview

**Smart AI Assistant** is a locally-run Streamlit web app that brings four AI-powered tools together in a single clean interface. It uses Google Gemini under the hood to handle everything from general conversation to structured nutrition extraction from food photos.

---

## Features

### 💬 AI Chat
- Conversational chat interface with persistent message history
- Ask anything — general knowledge, writing help, coding, and more

### 🍽️ Food Image Analyzer
- Upload a photo of any food item
- AI extracts a structured nutrition breakdown: Calories, Protein, Carbs, Fats, and a Health Score
- Download the results as **PDF**, **Excel**, or **CSV** reports

### 🎥 YouTube Summarizer
- Paste any YouTube video URL
- App fetches the transcript and generates a concise AI summary
- Includes thumbnail preview and progress feedback

### 📄 PDF Chat
- Upload any PDF document
- Ask questions and get AI-powered answers based on the document content

---

## Tech Stack

| Tool | Purpose |
|---|---|
| [Python](https://www.python.org/) | Core language |
| [Streamlit](https://streamlit.io/) | Web UI framework |
| [Google Generative AI](https://ai.google.dev/) | Gemini model for AI inference |
| [Pillow](https://python-pillow.org/) | Image handling |
| [PyPDF2](https://pypdf2.readthedocs.io/) | PDF text extraction |
| [youtube-transcript-api](https://pypi.org/project/youtube-transcript-api/) | YouTube transcript fetching |
| [fpdf](https://pyfpdf.github.io/fpdf2/) | PDF report generation |
| [pandas](https://pandas.pydata.org/) | Data handling for reports |
| [openpyxl](https://openpyxl.readthedocs.io/) | Excel report generation |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | Environment variable management |

---

## Getting Started

### Prerequisites

- Python 3.8 or higher
- A [Google Gemini API key](https://ai.google.dev/)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/smart-ai-assistant.git
cd smart-ai-assistant

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_google_gemini_api_key_here
```

> ⚠️ Never commit your `.env` file. Make sure it's listed in `.gitignore`.

### Run the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

---

## Project Structure

```
smart-ai-assistant/
├── app.py                # Main Streamlit application
├── requirements.txt      # Python dependencies
├── .env                  # API key (not committed)
├── project_logo.png      # Optional sidebar logo
└── venv/                 # Local virtual environment (not committed)
```

---

## Usage Guide

1. Launch the app with `streamlit run app.py`
2. Select a feature from the **sidebar**:
   - **Chat** — type a message and converse with Gemini
   - **Food Analyzer** — upload a food image and click Analyze
   - **YouTube Summarizer** — paste a YouTube URL and click Summarize
   - **PDF Chat** — upload a PDF, type your question, and click Ask
3. Download reports from the Food Analyzer using the PDF / Excel / CSV buttons

---

## Notes & Limitations

- Requires a valid `GOOGLE_API_KEY` — the app validates this on startup and will show an error if missing
- YouTube summarization depends on videos having available transcripts; some videos may not have them
- PDF extraction is limited by page count and character thresholds to stay within model context limits
- `project_logo.png` is optional; the sidebar will render without it if the file is absent

---

## .gitignore Recommendations

```
venv/
.env
__pycache__/
*.pyc
```

---

## License

MIT

---

## Contributing

Pull requests are welcome. To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request
