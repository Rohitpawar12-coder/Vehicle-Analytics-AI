# Vehicle Analytics Pipeline — CPU Prototype

A local Windows-friendly prototype for vehicle detection, approximate vehicle-color classification, saving detections, and viewing results in a React dashboard.

## Requirements
- Windows 10/11
- Python 3.10–3.12 recommended for the smoothest ML package support
- Node.js 20+
- Internet for the first YOLO model download

## Run on Windows
Open PowerShell in this folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

Open a second terminal in this folder:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

Upload an MP4/MOV/AVI/MKV/WEBM file from the dashboard. The first upload downloads `yolo11n.pt`; processing speed depends on your CPU and video resolution.

API docs: http://127.0.0.1:8000/docs

## Important scope note
This is a runnable CPU prototype, not a claim of full NVIDIA DeepStream compliance. The assignment's actual DeepStream/NVIDIA GPU requirement, production-grade persistent multi-object tracking, and true trained secondary color classifier need a compatible NVIDIA environment and further integration. This prototype uses YOLO on CPU, SQLite persistence, a heuristic color estimate, and a visual line overlay. It does not count unique line crossings yet.
