# LibriSmart – Smart Library Management and Campus Space Reservation Platform

LibriSmart is a complete, production-oriented Smart Library and Campus Space Reservation Platform built for colleges, universities, and educational institutions.

---

## 🏛️ Project Architecture

The project is structured into two main components:
1. **`android/`**: Modern Native Android application built with **Jetpack Compose**, **Material 3**, **MVVM**, **Kotlin Coroutines & StateFlow**, **Room Database**, **CameraX QR scanning**, and designed for strict **Google Play Store Policy compliance**.
2. **`backend/`**: High-performance asynchronous REST API built with **FastAPI**, **SQLAlchemy 2.0**, and **PostgreSQL** (with zero-configuration SQLite support for immediate local testing).

---

## 🚀 Getting Started

### 1. Android Application (`android/`)
1. Launch **Android Studio** (Ladybug / Meerkat or newer recommended).
2. Click **Open** and select the `c:\Users\Pallavi\Downloads\Librismart\android` folder.
3. Android Studio will automatically recognize Gradle Version Catalogs (`libs.versions.toml`) and download necessary dependencies.
4. Select an emulator (API 34 or 35 recommended) and click **Run 'app'** (`Shift + F10`).

### 2. Backend Server (`backend/`)
1. Open PowerShell or Terminal and navigate to the backend directory:
   ```powershell
   cd backend
   ```
2. Activate the Python virtual environment:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
3. Install required packages:
   ```powershell
   pip install -r requirements.txt
   ```
4. Verify Phase 1 database tables and connectivity:
   ```powershell
   python verify_phase1.py
   ```
5. Run the FastAPI development server:
   ```powershell
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
6. Access interactive API documentation at:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`
   - Health check: `http://localhost:8000/health`

---

## 📁 Repository Structure

```
Librismart/
├── README.md                           # Master setup and execution guide
├── android/                            # Complete Android Studio project
│   ├── app/
│   │   ├── build.gradle.kts            # App-level build config (targetSdk 35)
│   │   ├── proguard-rules.pro          # Release shrinking & keep-rules
│   │   └── src/main/
│   │       ├── AndroidManifest.xml     # Clean, Play-compliant permissions
│   │       ├── java/com/librismart/app/
│   │       │   ├── LibriSmartApp.kt    # Application class
│   │       │   ├── MainActivity.kt     # Jetpack Compose entry point
│   │       │   └── core/theme/         # Academic Material 3 design system
│   │       └── res/                    # Colors, strings, themes, network-security
│   ├── build.gradle.kts                # Root build script
│   ├── settings.gradle.kts             # Module declarations & repositories
│   └── gradle/
│       └── libs.versions.toml          # Centralized Version Catalog
│
└── backend/                            # FastAPI REST API & Database
    ├── .env.example                    # Environment template
    ├── requirements.txt                # Python dependencies
    ├── verify_phase1.py                # Database verification test suite
    └── app/
        ├── main.py                     # FastAPI application & lifespan
        ├── core/
        │   ├── config.py               # Pydantic Settings
        │   └── database.py             # SQLAlchemy async engine & session
        └── models/                     # Full 3NF relational models
            ├── user.py                 # Users, Student & Librarian Profiles
            ├── book.py                 # Books, Categories, Physical Barcode Copies
            ├── loan.py                 # Loans, Overdue Fines, Payments, Waitlist
            ├── seat.py                 # Floors, Zones, Seats, Reservations
            └── system.py               # Notifications, Wishlists, Reports, Settings
```

---

## 🔒 Google Play Compliance Highlights
- **Target API Level**: `targetSdk = 35` (Android 15 ready).
- **Minimal Permissions**: Only `INTERNET` and `ACCESS_NETWORK_STATE` in base config. `CAMERA` is isolated to QR scanning with user-facing runtime dialogs.
- **Data Privacy**: No tracking SDKs, no unauthorized data access, prepared for in-app account deletion.
