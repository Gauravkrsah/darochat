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
```
*(Note: Never commit your `.env` file to version control. It is already ignored in the `.gitignore`)*

### 3. Run the Chatbot
You can run the web application easily using the provided shell script:

```bash
bash run_chat.sh
```

This will:
1. Set up a Python virtual environment (`venv`) if it doesn't exist.
2. Install necessary dependencies (like `openai`).
3. Start the proxy server on port 8080.

### 4. Access the App
Once the server is running, the terminal will display the local and network URLs:
- **Local (On this machine)**: `http://localhost:8080`
- **Network (Other devices)**: `http://192.168.x.x:8080` (Check terminal for exact IP)

Open the URL in any modern browser to start chatting!

## Architecture
- **Backend (`web/server.py`)**: A lightweight Python `http.server` that acts as a proxy. It intercepts requests from the frontend and securely forwards them to the NVIDIA NIM API, bypassing browser CORS restrictions and protecting your API key.
- **Frontend (`web/app.js`, `web/style.css`, `web/index.html`)**: A dependency-free Vanilla JS frontend handling markdown rendering, streaming Server-Sent Events (SSE), and DOM manipulation.
