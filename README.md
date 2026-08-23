# ⚡ VYRON — AI Biometric Attendance System

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-cyan.svg)](https://flask.palletsprojects.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8%2B-magenta.svg)](https://opencv.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-SQLite%2FMySQL-purple.svg)](https://www.sqlalchemy.org/)

**VYRON** is an advanced, cyberpunk-themed **AI Biometric Attendance System** built with Python Flask, OpenCV, Deep Metric 128-dimensional Face Encodings, and SQLAlchemy. The platform combines a high-tech biometric command center HUD with real-time face recognition to automate attendance tracking, prevent proxy check-ins, and deliver instant attendance intelligence.

---

## 🌌 Visual & Technological Highlights

* **Cyberpunk Command Center:** Built with neon red (`#FF0055`), neon pink (`#FF2BD6`), and neon purple (`#A855F7`) palettes on obsidian surface (`#09050C`), with glassmorphism and animated HUD overlays.
* **Multi-Device & Cross-Platform Support:** Fully responsive on iOS/Android smartphones, iPads/tablets, laptops, desktops, and wall-mounted kiosks.
* **Camera Sensor Switching & Torch:** Flip between front/rear cameras or select external USB webcams; toggle flashlight in low-light environments.
* **Instant Wi-Fi QR Code Pairing & Kiosk Mode:** Generate pairing QR codes for any phone/tablet on the local network; one-tap Fullscreen Kiosk Mode for dedicated terminals.
* **Progressive Web App (PWA):** Installable as a standalone app with offline shell caching via Service Worker.
* **Holographic Light Mode:** Dual theme engine with Cyber Dark and Holographic Light mode persisted in `localStorage`.
* **Live Biometric HUD Scanner:** Optical camera viewfinder with animated scanline, target reticle, and adaptive bounding box scaling.
* **128-d Neural Face Vectorization:** Deep residual network extraction and Euclidean distance matching with real-time confidence scores.
* **Anti-Proxy Protection:** In-memory 30s cooldown timer + Database-level unique constraint on `(student_id, date)` preventing duplicate same-day attendance.
* **Identity Registry & Dossiers:** Manage student profiles, track class logs, calculate dynamic attendance percentages, and monitor exam eligibility ($\ge 75\%$).
* **Attendance Intelligence & CSV Export:** Search by Name/USN, filter by Date/Department, and export one-click RFC CSV reports.

---

## 🧠 AI/ML Recognition Pipeline

```
     Optical Video Feed
            ↓
  [Downscale Frame 0.25x] (30+ FPS Speed)
            ↓
  [Convert BGR → RGB]
            ↓
  [Face Detection] (Haar Cascade / HOG / CNN)
            ↓
  [128-d Feature Vector Extraction]
            ↓
  [Euclidean Distance Matching] (Against In-Memory Cached Identity Vectors)
            ↓
  [Verification Threshold (≤ 0.50)]
     ├── YES → Identity Verified (Confidence % = (1 - Distance / Max) * 100)
     │            ↓
     │     [Check Cooldown & Daily DB Constraint]
     │            ↓
     │     Mark Verified Attendance ("Present")
     └── NO  → "UNKNOWN PERSON" (Pink/Red HUD Alert, Access Unregistered)
```

---

## 🚀 Quickstart & Setup

### 1. Activate Environment & Install Dependencies
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Launch VYRON Command Center
```bash
python app.py
```
Open your browser at:
```text
http://127.0.0.1:5000
```

### 🔐 Default Command Clearance Credentials
- **Admin Identifier:** `admin`
- **Access Key:** `admin123`

---

## 🧪 Automated Testing
Verify all database constraints, authentication guards, and attendance calculations:
```bash
python -m pytest tests/ -v
```

---

## 🌐 Deploy to Render

This repository includes a [`render.yaml`](file:///d:/Face_recognition_attendance_system/render.yaml) blueprint specification for 1-click deployment on Render:

1. Push your repository to GitHub.
2. Log into [Render Dashboard](https://dashboard.render.com/).
3. Click **New +** → **Blueprint**.
4. Connect this GitHub repository (`Face-Recognition-Attendance-System`).
5. Render will automatically detect [`render.yaml`](file:///d:/Face_recognition_attendance_system/render.yaml), install dependencies with `pip`, launch the WSGI server with `gunicorn app:app`, and generate secure environment keys.

