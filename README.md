# NutriScan: Malnutrition Detection

A comprehensive, AI-powered malnutrition detection and analysis system that combines advanced machine learning models with WHO standards and an interactive chatbot assistant.

## 🚀 New Features

### 🔹 Advanced Reporting System
- **Severity Levels**: Mild, Moderate, Severe classification for skin and nail conditions
- **Confidence Scores**: AI model confidence percentages for predictions
- **WHO Standards Integration**: BMI-for-age percentiles, z-scores, and growth charts
- **NutriScan Risk Assessment**: Comprehensive 0-100 risk scoring system
- **Personalized Recommendations**: Diet, lifestyle, and hydration guidance

### 🔹 AI Chatbot Assistant (GPT/Gemini)
- Uses OpenAI GPT or Google Gemini to generate explanations and recommendations
- Context-aware answers using the current report data
- Safe fallbacks when API keys are missing

### 🔹 Enhanced Visualizations
- **WHO Growth Charts**: Professional BMI-for-age charts with reference curves
- **Risk Indicators**: Color-coded risk level displays
- **Confidence Meters**: Visual representation of AI prediction confidence
- **Severity Badges**: Clear classification of health conditions

## 🧰 LLM Setup (OpenAI or Gemini)

Set the environment variables for your preferred provider (either is fine):

```bash
# OpenAI
set OPENAI_API_KEY=sk-...          # Windows PowerShell
$env:OPENAI_API_KEY="sk-..."       # Windows PowerShell (alt)
export OPENAI_API_KEY=sk-...        # macOS/Linux

# Optional OpenAI model (default: gpt-4o-mini)
set OPENAI_MODEL=gpt-4o-mini

# Google Gemini
set GOOGLE_API_KEY=AIza...          # Windows PowerShell
$env:GOOGLE_API_KEY="AIza..."      # Windows PowerShell (alt)
export GOOGLE_API_KEY=AIza...       # macOS/Linux

# Optional Gemini model (default: gemini-1.5-flash)
set GEMINI_MODEL=gemini-1.5-flash
```

No code changes are needed after setting the keys. The endpoint `/predict/chatbot` will automatically use the available provider (tries OpenAI first, then Gemini).

## 🏗️ System Architecture

```
User Input → Image Analysis → WHO Standards → Risk Assessment → Report Generation → Chatbot (GPT/Gemini)
```

## 🛠️ Installation & Setup

```bash
# From repository root
cd MalnutritionApp
python -m venv .venv
.venv\Scripts\Activate.ps1         # Windows
pip install -r requirements.txt

# (Optional) run DB migration for new report fields
python scripts/migrate_database.py

# Set LLM keys (see above), then run
python run.py
```

Open `http://127.0.0.1:5000`, generate a report, then use the chatbot panel.

## 📁 Project Structure

```
MalnutritionApp/
├── app/
│   ├── predict/
│   │   ├── model.py              # ML models (VGG16, ResNet)
│   │   ├── who_standards.py      # WHO calculations
│   │   ├── llm_provider.py       # GPT/Gemini integration
│   │   └── routes.py             # API endpoints
│   ├── models/
│   │   ├── patient.py            # Patient data model
│   │   └── report.py             # Enhanced report model
│   └── templates/
│       └── predict/
│           └── result.html       # Advanced report UI
├── scripts/
│   └── migrate_database.py       # Database migration
└── requirements.txt               # Dependencies
```

## 🔧 Configuration

Environment variables in use (see `app/config.py`):
- `OPENAI_API_KEY`, `OPENAI_MODEL`
- `GOOGLE_API_KEY`, `GEMINI_MODEL`
- `SECRET_KEY`, `DATABASE_URL`, `UPLOAD_FOLDER`

## 📄 PDF Export Feature

NutriScan now includes comprehensive PDF export functionality for all reports:

### Features
- **Professional PDF Reports**: Generate detailed PDF reports with all analysis data
- **WHO Standards Integration**: Includes BMI percentiles, Z-scores, and WHO classifications
- **Image Analysis Results**: Complete skin and nail health analysis with confidence scores
- **Personalized Recommendations**: Dietary, lifestyle, and hydration recommendations
- **Professional Formatting**: Clean, medical-grade report layout

### Usage
1. Navigate to any report (from Reports list or individual report view)
2. Click the **"Export PDF"** button (green button with PDF icon)
3. The PDF will be automatically downloaded with filename: `nutriscan_report_[PatientName]_[Date].pdf`

### Installation
```bash
# Install PDF dependencies
python install_pdf_deps.py

# Or manually install
pip install reportlab==4.0.9 weasyprint==62.3
```

### PDF Contents
- **Complete Report Overview**: All content from the web report
- **Risk Assessment**: Visual risk indicators and comprehensive scoring
- **Patient Information**: Demographics, physical measurements, and BMI data
- **Image Analysis**: Skin and nail health analysis with actual images included
- **WHO Standards**: BMI-for-age growth chart and percentile analysis
- **Detailed Findings**: Comprehensive skin and nail health interpretation
- **Personalized Recommendations**: Dietary, lifestyle, and hydration guidance
- **Professional Assessment**: Medical-grade analysis with consultation notices
- **Digital Health Report**: Complete clinical-style documentation

## 🔬 Technical Notes

- Matplotlib is configured with the non-interactive `Agg` backend to avoid threading issues in Flask.
- Chatbot generation uses a unified prompt with context injection for explainability.
- If no API key is provided, a safe, generic fallback response is returned.
- PDF generation uses ReportLab for professional document formatting.

---

**Built with ❤️ for better child nutrition and health outcomes**


