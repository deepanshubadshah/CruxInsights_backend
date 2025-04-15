# CruxInsight Backend

This is the **Django backend** for the CruxInsight project. It fetches and analyzes Chrome UX Report (CrUX) data for one or more URLs and returns useful performance insights via a REST API.

---

## 🚀 Features

- Fetch CrUX data using Google's public API
- Support for single and multiple URLs
- Calculate aggregated statistics (avg, sum, min, max)
- Filter & sort metrics server-side
- Insight and recommendation generation
- Full exception handling

---

## 🛠️ Getting Started

### 📦 Requirements

- Python 3.8+
- pip
- virtualenv (optional, recommended)

### 🔧 Setup

```bash
# Clone the repo
git clone https://github.com/deepanshubadshah/CruxInsights_backend.git
cd cruxinsight_backend

# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
python manage.py runserver
