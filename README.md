# 🍳 Recipe Assistant

An interactive, AI-powered recipe and meal planning assistant built with **Google ADK (Agent Development Kit)**, **Gemini 2.5 Flash**, **Vertex AI Memory Bank**, **Google Cloud Firestore**, and **Google Cloud Storage**.

![Recipe Assistant Demo](demo.gif)

---

## 🌟 Key Implemented Features

- **🧠 Long-Term Memory (Vertex AI Memory Bank)**: Automatically saves user dietary preferences, restrictions, and severe food allergies across sessions so recommendations are always safe and personalized.
- **🥗 Firestore Recipe Database**: Search, save, and manage recipes in Google Cloud Firestore by ingredients on hand, max prep time, and dietary tags.
- **⭐ Favorites Management**: Mark recipes as favorites, retrieve saved favorite dishes, and update collection items dynamically.
- **📸 AI Dish Image Generation**: Generates high-quality dish photography on demand using `gemini-3.1-flash-lite-image` and stores image assets in Google Cloud Storage.
- **📄 Shareable Cloud Export**: Exports formatted Markdown recipe cards directly to a public Google Cloud Storage bucket for sharing.
- **🌐 Online Recipe Search**: Queries real-world recipes and preparation steps via TheMealDB API.

---

## 📋 Feature Roadmap & Status

| Feature | Status | Technology / Implementation |
| :--- | :---: | :--- |
| **Allergy & Preference Memory** | ✅ Implemented | Vertex AI Memory Bank (`VertexAiMemoryBankService`) |
| **Pantry & Ingredient Search** | ✅ Implemented | Google Cloud Firestore (`search_recipes`) |
| **Favorites Management** | ✅ Implemented | Google Cloud Firestore (`recipes` collection) |
| **AI Food Photography** | ✅ Implemented | Gemini 3.1 Flash Lite Image + Cloud Storage |
| **Recipe Card Cloud Export** | ✅ Implemented | Google Cloud Storage (`export_recipe_to_gcs`) |
| **Online Recipe Lookup** | ✅ Implemented | TheMealDB REST API (`fetch_online_recipes`) |
| **Automated Shopping List** | ⏳ Planned | *Planned, not yet implemented* |

---

## 🛠️ Architecture & Tech Stack

- **Framework**: Google ADK (Agent Development Kit - Python)
- **Primary LLM**: Gemini 2.5 Flash (`gemini-2.5-flash`)
- **Image Generation Model**: Gemini 3.1 Flash Lite Image (`gemini-3.1-flash-lite-image`)
- **Memory Store**: Vertex AI Memory Bank
- **Database**: Google Cloud Firestore
- **Object Storage**: Google Cloud Storage
- **Frontend**: FastAPI proxy server with dark mode glassmorphism UI

---

## 📂 Project Structure

```
recipe-assistant/
├── app/
│   ├── agent.py               # ADK Agent definition & Memory Bank callback registration
│   ├── firestore_tools.py     # Firestore, Cloud Storage, and image generation tool definitions
│   └── deployment_metadata.json # Remote Agent Engine deployment reference metadata
├── frontend/
│   ├── main.py                # FastAPI proxy forwarding client requests to A2A Agent Runtime
│   ├── Dockerfile             # Container image definition for Cloud Run deployment
│   └── static/
│       └── index.html         # Responsive frontend user interface
├── agents-cli-manifest.yaml   # ADK agents-cli deployment configuration
├── project_brief.md           # Original project specification
├── demo.gif                   # Looping video recording demo of the live application
└── README.md                  # Project documentation
```

---

## 🚀 Setup & Local Execution

### 1. Prerequisites & Environment Setup

Ensure you have Python 3.11+, Google Cloud SDK (`gcloud`), and project credentials configured:

```bash
# Clone repository and set up virtual environment
python -m venv .venv
source .venv/bin/activate
pip install -r frontend/requirements.txt
```

Set required environment variables:

```bash
export GOOGLE_CLOUD_PROJECT="YOUR_PROJECT_ID"
export GOOGLE_CLOUD_REGION="us-east4"
export AGENT_ENGINE_RESOURCE_NAME="projects/YOUR_PROJECT_ID/locations/us-east4/reasoningEngines/YOUR_REASONING_ENGINE_ID"
export AGENT_DIRECTORY="app"
```

### 2. Deploy Agent to Vertex AI Agent Runtime

Deploy the agent backend using `agents-cli`:

```bash
agents-cli deploy agent-runtime \
  --agent-directory app \
  --region us-east4 \
  --project YOUR_PROJECT_ID
```

### 3. Run Web Frontend Locally

Start the FastAPI application locally:

```bash
cd frontend
python main.py
```

Open your browser to `http://localhost:8080` (or your configured local host port) to interact with the assistant.

---

## ☁️ Cloud Run Deployment

To containerize and deploy the web frontend to Google Cloud Run:

```bash
gcloud run deploy recipe-assistant-frontend \
  --source ./frontend \
  --region us-east4 \
  --set-env-vars AGENT_ENGINE_RESOURCE_NAME="projects/YOUR_PROJECT_ID/locations/us-east4/reasoningEngines/YOUR_REASONING_ENGINE_ID",AGENT_DIRECTORY="app" \
  --allow-unauthenticated
```
