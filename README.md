# EL-105: AI Sales Playbook Assistant 🚀

A production-ready Retrieval-Augmented Generation (RAG) assistant designed to help sales teams handle customer objections in real-time. It retrieves the best objection handlers from a company playbook and generates structured, context-rich responses using LLaMA 3.3.

![Project Status](https://img.shields.io/badge/Status-Complete-success)
![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue)
![Database](https://img.shields.io/badge/Database-Supabase%20%2B%20pgvector-green)

---

## 🏗️ Architecture Stack

*   **Frontend**: HTML5, CSS3 (Glassmorphism design), Vanilla JS served via Flask.
*   **Backend**: Python FastAPI (Handles REST API, RAG Pipeline).
*   **Language Model**: Groq API (`llama-3.3-70b-versatile`).
*   **Embeddings**: Sentence Transformers (`all-MiniLM-L6-v2`) processing locally.
*   **Database**: Supabase PostgreSQL + `pgvector` for semantic search.

---

## 🛠️ Step-by-Step Setup Guide

Follow these instructions to get the project running locally. Code blocks will specify where commands differ between **Windows** and **Linux/macOS**.

### 1. Prerequisites 
*   **Python 3.9+** installed on your system.
*   A **Supabase account** and a new project database.
*   A **Groq API Key** (available for free at console.groq.com).

### 2. Configure Environment Variables
Inside the `backend/` directory, create a `.env` file (or copy the example):
```env
# backend/.env

# Supabase Configuration
SUPABASE_URL=https://[YOUR_PROJECT_ID].supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Groq API Configuration
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama-3.3-70b-versatile

# Server Configuration
FASTAPI_PORT=8000
FLASK_PORT=5000
```

### 3. Create a Virtual Environment & Install Dependencies

**On Windows (PowerShell/Command Prompt):**
```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

**On Linux/macOS:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

*(Note: The first time you run the backend or seeding script, `sentence-transformers` will automatically download the 80MB embedding model.)*

### 4. Set Up the Supabase Database
You must create the necessary tables and Vector extensions in Supabase.
1. Log in to your [Supabase Dashboard](https://supabase.com/dashboard).
2. Navigate to your project -> **SQL Editor**.
3. Open the `setup_supabase.sql` file located in the project root.
4. Copy all of the SQL text, paste it into the Supabase editor, and click **Run**.

### 5. Seed the Playbook Data
Once the database tables exist, populate them with the markdown playbook data:

**On Windows & Linux:**
```bash
python seed.py
```
*You should see output confirming 22 chunks have been embedded and inserted into your database.*

---

## 🚀 Starting the Servers

The project uses a dual-server architecture to prevent CORS issues and cleanly separate the frontend UI from the backend logic. You will need **two separate terminal windows**. Ensure your virtual environment is active in both!

**Terminal 1: Start the FastAPI Backend**
```bash
# Windows & Linux:
cd backend
python main.py
```
*(The backend will run on http://localhost:8000 and display the Swagger API docs at `/docs`)*

**Terminal 2: Start the Flask Frontend Server**
```bash
# Windows & Linux:
python server.py
# Note: Keep the command execution in the project root folder.
```

### 🎉 You're Done!
Open your web browser and navigate to:
**http://localhost:5000**

You can now test the assistant by typing objections like *"Your product is way too expensive,"* or *"We already use Competitor X."*

---

## 📂 Project Structure

```text
AI-Sales-Playbook-Assistant/
├── backend/                           # Core FastAPI API Server
│   ├── rag/                           # RAG Pipeline Logic
│   │   ├── chunker.py                 # Parses markdown playbook into semantic chunks
│   │   ├── embeddings.py              # Generates embeddings via sentence-transformers
│   │   ├── generator.py               # Assembles prompt & executes Groq LLM logic 
│   │   └── retriever.py               # Semantic vector search via Supabase pgvector
│   ├── routes/                        # API Endpoints
│   │   ├── history.py                 # GET/DELETE chat conversation history
│   │   ├── playbook.py                # Playbook stats & re-seeding triggers
│   │   └── query.py                   # Main objection processing route
│   ├── .env                           # Environment variables configuration
│   ├── config.py                      # Parses env vars for backend use
│   ├── database.py                    # Interface for Supabase Database operations
│   ├── main.py                        # FastAPI application entrypoint & CORS config
│   └── requirements.txt               # Backend Python dependencies
├── frontend/                          # HTML/CSS/JS User Interface
│   ├── css/                           
│   │   └── style.css                  # Custom styling & glassmorphism theme
│   ├── js/                            
│   │   └── app.js                     # UI state, API fetching & markdown rendering
│   └── index.html                     # Main chat dashboard layout
├── data/
│   └── sales_playbook.md              # Document holding 20+ objection handlers
├── .gitignore                         # Project git ignore definitions
├── README.md                          # Setup documentation
├── seed.py                            # Utility script to generate vectors and index DB
├── server.py                          # Flask server hosting UI & proxying API requests
├── setup_db.py                        # Utility helper for SQL setup instructions
└── setup_supabase.sql                 # SQL schema for tables, pgvector, & RPC functions
```
