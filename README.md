# BOM Intelligence Agent v2 🚀

An end-to-end, AI-powered Full Stack application designed to intelligently analyze Bill of Materials (BOM) Excel/CSV files. By leveraging advanced Machine Learning and Knowledge Graphs, this tool automates component lifecycle monitoring, pricing analysis, availability tracking, and drop-in replacement detection for hardware engineers.

## 🌟 Key Features

- **Automated BOM Parsing:** Upload any standard BOM Excel/CSV file. The system automatically normalizes header columns and extracts components, manufacturers, and designators using intelligent heuristics.
- **Knowledge Graph Integration:** Powered by `networkx`, the application constructs a semantic relational graph mapping all components to their parent PCBs/Assemblies, enabling deep impact analysis if a part becomes obsolete.
- **LangGraph AI Orchestration:** Utilizes an advanced `langgraph` state machine to deploy an intelligent reasoning agent. The agent dynamically checks lifecycle statuses, and automatically routes to an "Alternative Search" pipeline if a component faces a PCN (Product Change Notification) or EOL (End of Life) event.
- **NVIDIA NIM Integration:** Natively connects to NVIDIA's high-performance LLM APIs (specifically `moonshotai/kimi-k2.5`) for rapid, structured component intelligence extraction and parameter matching.
- **Real-Time Interactive Dashboard:** A stunning, modern React-based frontend built with Vite and Recharts, designed to look and feel like a professional PowerBI hardware intelligence dashboard.

## 🛠️ Technology Stack

- **Frontend:** React, Vite, Vanilla CSS, Recharts, Lucide-React
- **Backend:** Python, FastAPI, Uvicorn, LangChain, LangGraph, NetworkX
- **AI Core:** NVIDIA NIM APIs (Moonshot Kimi-K2.5)

## 🚀 Getting Started

### Prerequisites
- Node.js (v18+)
- Python (3.10+)
- An active NVIDIA NIM API Key

### Backend Setup
1. Navigate to the backend directory: `cd backend`
2. Create a `.env` file and add your API key: `NVIDIA_API_KEY=your_key_here`
3. Install dependencies: `pip install -r requirements.txt`
4. Start the backend intelligence server: `python server.py` (Runs on http://localhost:8000)

### Frontend Setup
1. Navigate to the frontend directory: `cd frontend`
2. Install UI dependencies: `npm install`
3. Start the Vite dev server: `npm run dev`
4. Navigate to the provided local URL to access the dashboard!
