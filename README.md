# 🚀 BOM Intelligence platform (v2)

Welcome to the **BOM Intelligence Platform**! This is a complete, full-stack application designed to help hardware engineers analyze their Bill of Materials (BOM). 

It takes a standard Excel or CSV file of hardware components, builds an intelligent map of how they all connect, and then uses Advanced AI (NVIDIA's Moonshot Kimi 2.5) to instantly tell you if any parts are obsolete, too expensive, or out of stock. If a part *is* obsolete, the AI acts as an autonomous agent to hunt down perfect drop-in replacements for you!

This guide is written for absolute beginners. If you've just downloaded this project and want to run it on your own computer, **start here!**

---

## 🌟 How It Works

*   **1. You upload an Excel/CSV file:** It instantly reads your parts list.
*   **2. It builds a "Knowledge Graph":** It maps out which parts belong to which circuit boards so it understands your entire hardware project's ecosystem.
*   **3. It deploys an AI "Agent":** Using a technology called **LangGraph**, it sends an AI agent to research every single part checking for lifecycle warnings, stock availability, and manufacturer pricing.
*   **4. You get a Dashboard:** All the results are displayed on a beautiful, interactive PowerBI-style dashboard!

---

## 🛠️ What You Need to Install First

Before you can run the code, you need to install three standard pieces of developer software on your computer.

1.  **Git:** Used to download the code. [Download Git here](https://gitforwindows.org/)
2.  **Node.js (v18+):** Needed to run the User Interface (the website). [Download Node.js here](https://nodejs.org/) (Choose the "LTS" version).
3.  **Python 3 (v3.10+):** Needed to run the AI and Backend Server. [Download Python here](https://www.python.org/downloads/).
    *   *⚠️ CRITICAL Python Step:* When installing Python on Windows, look closely at the very first installation screen and **check the box that says "Add python.exe to PATH"** before you click Install!

---

## 🚀 Step-by-Step Installation Guide

Once those three things are installed, open your computer's terminal (Command Prompt) and follow these steps exactly!

### Step 1: Download the Project
In your terminal, download the code to your computer and navigate into the folder:
```bash
git clone https://github.com/Aka8sh3/BOM-Intelligence-Agent.git
cd BOM-Intelligence-Agent
```

### Step 2: Set up the AI Backend
The "Backend" is the Python engine that talks to NVIDIA's AI.

1.  Navigate into the backend folder:
    ```bash
    cd backend
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
    *Keep this terminal window open! The server needs to stay running in the background.*

### Step 3: Set up the Website Frontend
Now we need to start the actual visual dashboard. Open a **brand new**, second terminal window for this part.

1.  Navigate into the frontend folder:
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

### Step 4: Open the App!
When you run that last command, it will print out a local URL (usually `http://localhost:5173`). 
Hold `CTRL` on your keyboard and click that link, or paste it into your browser (Chrome/Edge/Safari). 

**You are now officially running the entire BOM Intelligence Platform! Upload your first Excel file and watch the AI go to work!**
