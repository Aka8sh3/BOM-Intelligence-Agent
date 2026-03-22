# 🚀 BOM Intelligence Platform

Welcome to the **BOM Intelligence Platform**! This is a complete, full-stack application designed to help hardware engineers analyze their Bill of Materials (BOM) using real-time AI.

It takes a standard Excel or CSV file of hardware components, builds an intelligent semantic map of how they all connect, and then uses Advanced AI (NVIDIA Meta Llama-3.1-70B & Moonshot Kimi-2.5) to instantly tell you if any parts are obsolete, too expensive, or out of stock. If a part *is* obsolete, the AI acts as an autonomous agent to hunt down perfect drop-in replacements for you!

This guide is written for absolute beginners. If you've just downloaded this project and want to run it on your own computer, **start here!**

---

## 🌟 How It Works

*   **1. You upload an Excel/CSV file:** It instantly reads your parts list.
*   **2. It builds an AI "Semantic Knowledge Graph":** Using a local **FalkorDB** instance, the AI autonomously studies your engineering components and dynamically infers hidden physical/electrical relationships (e.g. `(Gate IC)-[:DRIVES]->(SiC MOSFET)`).
*   **3. It deploys an AI "Agent":** Using a technology called **LangGraph**, it sends an AI agent to research every single part in real-time, checking for lifecycle warnings, stock availability, and manufacturer pricing.
*   **4. You get a PowerBI Dashboard:** All the results are displayed on a beautiful, interactive Next.js/React dashboard!

---

## 🛠️ What You Need to Install First

Before you can run the code, you need to install four standard pieces of developer software on your computer.

1.  **Git:** Used to download the code. [Download Git here](https://gitforwindows.org/)
2.  **Docker Desktop:** Needed to run the FalkorDB Knowledge Graph database. [Download Docker here](https://www.docker.com/products/docker-desktop/)
3.  **Node.js (v18+):** Needed to run the User Interface (the website). [Download Node.js here](https://nodejs.org/) (Choose the "LTS" version).
4.  **Python 3 (v3.10+):** Needed to run the AI and Backend Server. [Download Python here](https://www.python.org/downloads/).
    *   *⚠️ CRITICAL Python Step:* When installing Python on Windows, look closely at the very first installation screen and **check the box that says "Add python.exe to PATH"** before you click Install!

---

## 🚀 Step-by-Step Installation Guide

Once those four things are installed, open your computer's terminal (Command Prompt) and follow these steps exactly!

### Step 1: Download the Project
In your terminal, download the code to your computer and navigate into the folder:
```bash
git clone https://github.com/Aka8sh3/BOM-Intelligence-Agent.git
cd BOM-Intelligence-Agent
```

---

### Step 2: Start the Knowledge Graph Database (Terminal 1)
Start the FalkorDB engine and the visual browser UI.
```bash
docker run -p 6379:6379 -p 3000:3000 falkordb/falkordb
```
*(Leave this terminal window open!)*

---

### Step 3: Set up the AI Backend (Terminal 2)
The "Backend" is the Python engine that talks to NVIDIA's AI.

1.  Open a **second** terminal window and navigate into the backend folder:
    ```bash
    cd BOM-Intelligence-Agent/backend
    ```
2.  Install the Python libraries:
    ```bash
    pip install -r requirements.txt
    ```
3.  Unlock the NVIDIA AI:
    *   Create a text file inside this `backend` folder and name it exactly `.env` (don't forget the dot!).
    *   Open it in Notepad and paste your secret NVIDIA NIM API Key inside it like this:
        `NVIDIA_API_KEY=nvapi-your-secret-key-goes-here`
4.  Start the AI Server:
    ```bash
    python server.py
    ```
    *(Leave this terminal window open!)*

---

### Step 4: Set up the Website Frontend (Terminal 3)
Now we need to start the actual visual dashboard. 

1.  Open a **third** terminal window and navigate into the frontend folder:
    ```bash
    cd BOM-Intelligence-Agent/frontend
    ```
2.  Install the website code packages:
    ```bash
    npm install
    ```
3.  Start the website:
    ```bash
    npm run dev
    ```
    *(Leave this terminal window open!)*

---

## 💻 How to Use the App!

**1. The Primary Dashboard (Component Analysis)** 
Open your browser and navigate to `http://localhost:5173`. 
Drag and drop your `simple_gate_driver_10kv_bom.csv` file here. The AI will analyze the parts, check real-time stock limits, and find exact alternatives.

**2. The Semantic Knowledge Graph (Optional Deep Dive)** 
If you want to view the incredibly detailed electrical mapping of your components, open a 4th terminal window and run our AI Sync script:
```bash
cd BOM-Intelligence-Agent/backend
python falkordb_sync.py simple_gate_driver_10kv_bom.csv
```
Once it finishes processing the AI inferences, open your browser to `http://localhost:3000` to interact with the database map! You can click the edges between components to see the LLM's explicit "reasoning" for the connections.
