# Daro Chat

A sleek, premium web-based AI chatbot UI powered by the NVIDIA NIM API. It allows you to select from 30+ top-tier language models (including Llama 3.3, DeepSeek, Mixtral, and Nemotron) and stream responses locally via an elegant "ChatGPT-style" interface.

## Features
- **NVIDIA NIM Integration**: Fully integrated with NVIDIA's fast inference endpoints.
- **Premium UI/UX**: Minimalist, responsive black-and-white interface matching modern chat design standards.
- **Cross-Device LAN Access**: Run the server on your computer and access the UI from any device on your local network (e.g., your phone).
- **Persistent Chat History**: Saves your previous conversations automatically using LocalStorage.
- **Markdown Support**: Renders markdown formatting, code syntax highlighting, and tables seamlessly.
- **Theme Toggling**: Switch between Light Mode and Dark Mode.

## Setup Instructions

### 1. Prerequisites
- Python 3.8+
- An NVIDIA API Key from [build.nvidia.com](https://build.nvidia.com)

### 2. Configure Environment Variables
Create a `.env` file in the root directory (where this README is located) and add your API keys:
```env
NVIDIA_API_KEY=your_nvidia_nim_api_key_here
ZHIPUAI_API_KEY=your_zhipuai_api_key_here
```
*(Note: Never commit your `.env` file to version control. It is automatically ignored by `.gitignore`)*

### 3. How to Run the App
You can run Daro Chat either as a **Web Application** (recommended) or entirely in the **Terminal**.

#### Option A: The Easy Way (All-in-One Script)
The simplest way to run the Terminal Chatbot is using the provided bash script. This automatically creates the Python virtual environment (`venv`) and installs the required packages:
```bash
bash run_chat.sh
```

*(Troubleshooting: If you ever move the `darochat` folder to a new location and get a "pip cannot execute" error, simply delete the `venv` folder by running `rm -rf venv`, and then run `bash run_chat.sh` again to rebuild it).*

#### Option B: Running Manually (Web Server or Terminal)
If you prefer to start the Web Server (or if you want to run the scripts manually), you must **activate the virtual environment** first.

**Step 1: Activate the Virtual Environment**
Run this command from the project root:
```bash
source venv/bin/activate
```

**Step 2: Start the Web UI**
```bash
python web/server.py
```
This will start a local proxy server. You can access the UI by opening `http://localhost:8080` in your web browser. It will also print your local network IP (e.g., `http://192.168.x.x:8080`) so you can open the chatbot on your phone or other devices on the same Wi-Fi!

**Step 2 (Alternative): Start the Terminal UI**
```bash
python nvidia_chat.py
```

*(Note: When you are finished, you can type `deactivate` in the terminal to exit the virtual environment).*

## Architecture
- **Backend (`web/server.py`)**: A lightweight Python `http.server` that acts as a proxy. It intercepts requests from the frontend and securely forwards them to the NVIDIA NIM API, bypassing browser CORS restrictions and protecting your API key.
- **Frontend (`web/app.js`, `web/style.css`, `web/index.html`)**: A dependency-free Vanilla JS frontend handling markdown rendering, streaming Server-Sent Events (SSE), and DOM manipulation.
