# Food Po - AI Nutrition Planner

An interactive 3D Infinite Gallery application powered by a FastAPI backend that uses OpenAI to compute synthetic food rankings and generates spoken audio coaching.

## Setup Instructions for the Team

**1. Clone the repository**
```bash
git clone https://github.com/SaranBodduluri/Foodpo.git
cd Foodpo
```

**2. Install Backend Requirements**
You need Python installed. Run this in your terminal to grab all dependencies:
```bash
pip install -r requirements.txt
```

**3. Configure your API Keys**
- Duplicate the `.env.example` file and rename the copy to `.env`
- Open `.env` and paste in the OpenAI API Key provided by Saran next to `OPENAI_API_KEY=`
*(Do not upload the .env file to GitHub!)*

## Running the Application Locally

You need to run **both** the backend Python server and the frontend HTML server simultaneously.

**Step A: Start the FastAPI Backend (Terminal 1)**
From the root `Foodpo` folder, run:
```bash
python -m uvicorn services.api.main:app --reload
```
*(Leave this terminal window running in the background).*

**Step B: Start the Frontend UI (Terminal 2)**
Open a *new* separate terminal window, navigate to the web folder, and start a local HTTP server to bypass browser CORS origin policies:
```bash
cd services/web
python -m http.server 8080
```

**Step C: Open the App!**
In your web browser (Chrome/Edge recommended for Voice Dictation), go directly to:
**http://localhost:8080**
