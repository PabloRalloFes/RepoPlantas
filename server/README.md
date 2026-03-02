# 🖥️ Server / API Backend - Setup Guide

This folder contains the configuration and scripts to run the **HTTPS API backend** that powers the desktop application (`main_app.py`).

> **Note:** Most users will interact with this server through the desktop app. Direct server access is mainly for developers and administrators.

---

## ⚡ Quick Start (3 Steps)

### 1️⃣ Install Dependencies (Once)
```bash
pip install -r requirements.txt
```

### 2️⃣ Choose How to Start

**Option A - Interactive Menu (Easiest):**
- **Windows**: Double-click `server/run_server.cmd`
- **Linux/Mac**: `chmod +x server/run_server.sh && ./server/run_server.sh`

**Option B - Command Line (Direct):**
```bash
python run_server.py --https
```

### 3️⃣ Done!
The API will be running at: **`https://localhost:5001`**

The desktop app (`main_app.py`) will connect to it automatically if running on the same machine.

---

## 🏗️ What is This Server?

This is a **Flask API backend** that:
- ✅ Manages user authentication and roles
- ✅ Handles image uploads and storage (MongoDB)
- ✅ Processes classification requests
- ✅ Provides experiment management

**The App talks to This Server:**
```
┌─────────────────┐
│   main_app.py   │  (Desktop application)
│  (GUI - Flet)   │
└────────┬────────┘
         │ HTTPS requests
         ↓
┌─────────────────────┐
│  run_server.py      │  (This file)
│  API & Backend      │
└────────┬────────────┘
         │ MongoDB
         ↓
┌─────────────────────┐
│    MongoDB          │
│  Image Storage      │
└─────────────────────┘
```

---

## 📝 Running the Server

### Interactive Menu (Recommended for first-time users)
```bash
# Windows
cd server && run_server.cmd

# Linux/Mac
./server/run_server.sh
```

A menu will appear with 5 options. Choose your preferred configuration.

---

### Command Line (More Control)

| Command | When to Use |
|---------|-------------|
| `python run_server.py --https` | **RECOMMENDED** - HTTPS with auto-reload |
| `python run_server.py` | HTTP mode (testing only, less secure) |
| `python run_server.py --https --port 8443` | Custom port (if 5001 is busy) |
| `python run_server.py --host 0.0.0.0 --https` | Allow remote connections |

**For most users:** `python run_server.py --https` is perfect.

**Note:** The server runs in development mode with auto-reload enabled, which is perfect for local usage and development.

---

## 🔐 HTTPS & Certificates

### Why HTTPS?
- ✅ Encrypts data between app and server
- ✅ Required for modern secure connections
- ✅ Self-signed certificates work fine for internal use

### Self-Signed Certificates
- Generated automatically on first run
- Valid for 365 days
- Stored in `ssl_certs/` (root directory)
- ⚠️ Browsers may warn (this is normal and safe for internal use)

**The Desktop App accepts self-signed certificates automatically** - no action needed.

---

## ⚙️ Requirements

### System Requirements
- Python 3.8+
- OpenSSL (for certificate generation)
  - **Windows**: Download from https://slproweb.com/products/Win32OpenSSL.html
  - **Linux**: `sudo apt-get install openssl`
  - **Mac**: `brew install openssl`

### Python Packages (from requirements.txt)
- Flask - Web framework
- httpx - HTTP client
- PyMongo - MongoDB connection
- Torch/TorchVision - ML models
- Flet - Desktop app framework

---

## 🔍 Verify Setup

Before deploying, validate everything is correctly configured:

```bash
python server/validate_setup.py
```

Should show ✓ for all checks. If something fails, it will tell you what to install.

---

## 🌐 Remote Access (Different Machine)

If you need to connect the app from a **different computer** on the same network:

### Step 1: Get Your Server's IP
```bash
# Windows
ipconfig

# Linux/Mac
ifconfig
```

Look for something like: `192.168.1.100` or `10.0.0.50`

### Step 2: Configure App to Use That IP

In `logicav3.py` on the client machine, change:
```python
# Line 8 - change from:
URL_API = "https://localhost:5001"

# To your server IP:
URL_API = "https://192.168.1.100:5001"  # Replace with your actual IP
```

### Step 3: Add Certificate Exception

In petitions, add `verify=False`:
```python
res = httpx.post(url, json=data, verify=False)
```

### Network Requirements
- Both machines on the **same network** (campus LAN or university VPN)
- Firewall allows port 5001
- If unsure, contact your IT department

---

## 📁 Server Folder Contents

```
server/
├── run_server.cmd              # Interactive menu (Windows)
├── run_server.sh               # Interactive menu (Linux/Mac)
├── generate_certificates.py    # SSL certificate generator
├── validate_setup.py           # Dependency checker
└── README.md                   # This file
```

---

## 🆘 Troubleshooting

### "OpenSSL not found"
```bash
# Windows with Chocolatey
choco install openssl

# Or download: https://slproweb.com/products/Win32OpenSSL.html
```

### "Port 5001 already in use"
```bash
# Use a different port
python run_server.py --https --port 8443
```

### "Can't connect from another machine"
- ✅ Both machines on **same network**?
- ✅ Firewall allows port 5001?
- ✅ Using correct IP (not `localhost`)?

### "Certificate errors"
- **In app**: Add `verify=False` to httpx requests
- **System errors**: Check OpenSSL is properly installed

---

## ❓ FAQ

**Q: Can I use HTTP instead of HTTPS?**
A: Yes, with `python run_server.py` (without --https flag) for testing. HTTPS is more secure.

**Q: Why does the desktop app need this server?**
A: The server manages the database, user authentication, and image processing. The app is just the UI.

**Q: Does this work on Windows?**
A: Yes, works perfectly on Windows, Linux, and Mac.

**Q: Where are the certificates stored?**
A: In `ssl_certs/` directory in the project root (auto-generated).

**Q: Can I run this in production?**
A: This development server is suitable for local/internal use. For public production, consider using a proper WSGI server behind nginx.

---

## 📚 Related Documentation

- **Main Project**: [README.md](../README.md) or [README_ES.md](../README_ES.md)
- **Desktop App Guide**: See `README_APP.md` in the root
- **API Code**: [main.py](../main.py)
- **App Code**: [main_app.py](../main_app.py)

---

## 🎯 Next Steps

1. Run `python server/validate_setup.py`
2. Start server: `python run_server.py --https`
3. Run desktop app: `python main_app.py`
4. Login and test functionality

---

*Last Updated: February 2026 | TFG Plant Classification*

