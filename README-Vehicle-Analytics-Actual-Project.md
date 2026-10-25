# Real-Time Vehicle Analytics System

A Python and React application for vehicle detection and traffic analytics from video. The project uses a YOLO model for vehicle detection, OpenCV for video-frame processing, FastAPI for backend APIs, and a React/Vite dashboard for viewing results.

> **Implementation note:** This README documents the project structure and commands used in the current local project. Video-file processing is the documented primary workflow. RTSP/live-stream support is present in the project work, but confirm it end-to-end on your machine before describing it as fully verified.

## Features

- Process a supported video file through the backend.
- Detect supported vehicle classes using a YOLO model.
- Draw/display processed detections and return detection/statistics data through the API.
- Store detection records using the project's SQLite database layer.
- View results through the React dashboard.
- Expose API health and statistics endpoints through FastAPI.

## Technology stack

- **Python** — backend and video-processing logic
- **Ultralytics YOLO** — object detection
- **OpenCV** — reading and processing video frames
- **FastAPI** — backend REST API
- **SQLite** — local database
- **React + Vite** — frontend dashboard
- **MediaMTX / FFmpeg** — used for RTSP stream testing/configuration where enabled in the local setup

The project uses YOLO/OpenCV rather than NVIDIA DeepStream. NVIDIA DeepStream is not part of the implemented stack.

## Project structure

```text
vehicle-analytics/
├── backend/
│   ├── main.py              # FastAPI routes and application entry point
│   ├── database.py          # Database operations
│   └── vision.py            # Backend vision logic (if used by current route)
├── config/                  # Application configuration
├── database/                # Database schema and initialization helpers
├── frontend/
│   ├── package.json
│   ├── index.html
│   └── src/                 # React UI and API client
├── outputs/                 # Processed output video(s)
├── sample_videos/           # Local test videos (if supplied)
├── vision/
│   ├── vehicle_detector.py  # YOLO vehicle detector
│   ├── vehicle_tracker.py   # Tracking logic
│   ├── line_counter.py      # Line-crossing logic
│   ├── video_detector.py    # Video-file processing
│   └── pipeline.py          # Vision pipeline helpers
├── yolo11n.pt               # YOLO model weights (if present locally)
├── requirements.txt
├── run_backend.bat
├── run_frontend.bat
├── setup.ps1
└── README.md
```

Some optional files (model weights, test videos, RTSP/MediaMTX binaries, local output files, and virtual environments) may be excluded from GitHub due to size or licensing. Check that any required model weights are available before running inference.

## Requirements

- Windows 10/11
- Python 3.10 or newer compatible with the versions pinned in `requirements.txt`
- Node.js LTS and npm
- Git (optional, for cloning)
- A supported input video such as `.mp4`, `.avi`, `.mov`, or `.mkv`

CPU inference is possible with compatible dependencies, but performance depends on the computer and video resolution. An NVIDIA GPU is not required for the YOLO/OpenCV workflow.

## 1. Get the project

Clone your repository, or open PowerShell in the existing project folder:

```powershell
cd "$HOME\Desktop\vehicle-analytics"
```

If cloning from GitHub, use the repository URL you actually published:

```powershell
git clone <YOUR-REPOSITORY-URL>
cd vehicle-analytics
```

## 2. Set up the Python backend

From the project root in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation, you can skip activation and call the venv's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Use the root `requirements.txt` as the source of truth for Python package versions. Do not install a second, conflicting set of packages unless the current project requires it.

## 3. Set up the frontend

Open a second PowerShell terminal:

```powershell
cd "$HOME\Desktop\vehicle-analytics\frontend"
npm install
```

## 4. Run the application

### Start the backend

From the project root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8080
```

The backend should be available at `http://127.0.0.1:8080`.

Interactive API documentation (when enabled by FastAPI) is at:

- `http://127.0.0.1:8080/docs`

You can also use the project's batch file from the project root:

```powershell
.\run_backend.bat
```

### Start the frontend

In a second terminal:

```powershell
cd "$HOME\Desktop\vehicle-analytics\frontend"
npm run dev
```

Open the local URL printed by Vite in the terminal (commonly `http://localhost:5173`).

Alternatively, from the project root, use:

```powershell
.\run_frontend.bat
```

Keep both backend and frontend terminals running while using the dashboard.

## 5. Process a video

1. Start the backend and frontend.
2. Open the React dashboard in your browser.
3. Select/upload a supported video file if the UI provides the upload control.
4. Start processing and wait for the backend response.
5. Review detections and statistics shown by the dashboard.
6. Check the `outputs/` directory for the processed video, where generated by the current pipeline.

The backend's video-processing route has used `POST /api/process-video` and writes the processed result to `outputs/processed_video.mp4`. The accepted upload field name and exact response schema should be checked in `backend/main.py` or the `/docs` page if they differ in your current checkout.

## API endpoints

The following routes have been used in this project. Open `/docs` on the running backend to confirm the exact methods and request schemas for the current code.

| Endpoint | Purpose |
|---|---|
| `GET /` | Basic backend/root response |
| `GET /api/health` | Health check |
| `GET /api/stats` | Vehicle statistics |
| `GET /api/detections` | Retrieve detection records |
| `POST /api/process-video` | Upload/process a video file |
| `DELETE /api/detections` | Clear detection records, if enabled |
| `/outputs/processed_video.mp4` | Processed video output path used by the project |

Do not expose the backend publicly without adding appropriate authentication, upload limits, and security controls.

## RTSP / live-stream configuration

RTSP was tested locally in the development setup with MediaMTX and FFmpeg. A local stream URL used during testing was:

```text
rtsp://127.0.0.1:8554/traffic
```

The stream reader was tested with OpenCV/FFmpeg and was able to open the stream and read frames. To use RTSP in your current checkout:

1. Start/configure MediaMTX using your local configuration.
2. Publish a video stream to the configured MediaMTX path using FFmpeg or another RTSP publisher.
3. Confirm that OpenCV can open the RTSP URL and retrieve frames.
4. Start the backend's RTSP processing route if it is present in the current `backend/main.py`.
5. Confirm that the processed-frame count, detections, database records, and dashboard update as expected.

**Verification status:** Earlier testing returned `running` for RTSP status, but `/api/stats` showed `processed_frames: 0`. Therefore, the full live RTSP → detection → database → dashboard flow must be verified before claiming that end-to-end live analytics is complete. MediaMTX and FFmpeg are not required for the basic video-file workflow.

## Database

The project includes a SQLite database layer in `backend/database.py` and database setup/schema files under `database/`. Follow the initialization logic in those files for the current database path and schema. Keep generated database files local unless you intentionally want to version a small, non-sensitive sample database.

## Configuration and model weights

- Check `config/` for the current project configuration.
- The detector has used `yolo11n.pt` as the model name/path. Ensure the model file is present locally or allow the configured Ultralytics setup to obtain it when appropriate.
- Do not commit virtual environments, large generated videos, secrets, TLS private keys, or executables into the repository.
- If your `.gitignore` excludes the model weights, document how to obtain the correct weights for a fresh installation.

## Troubleshooting

### Backend command fails
- Confirm the terminal is in the project root.
- Confirm `.venv` exists and dependencies installed successfully.
- Review the complete Python traceback in the terminal.

### Frontend cannot reach the API
- Make sure the backend is running on port `8080`.
- Check the API base URL in `frontend/src/services/api.js`.
- Check the browser developer console for CORS or network errors.

### YOLO model file is missing
- Confirm `yolo11n.pt` exists in the expected path, or use the model path configured in the detector.
- Ensure the installed `ultralytics` package is compatible with the project.

### Video cannot be processed
- Try a standard MP4 file first.
- Check the video path, codec support, upload size, and backend terminal output.
- Confirm that `outputs/` exists and is writable.

### RTSP status is running but no frames are counted
- Confirm the stream is actually publishing frames.
- Check the configured RTSP URL and MediaMTX logs.
- Check that the active backend route calls the detector and increments frame statistics.
- Verify database writes and dashboard polling separately.

## Current limitations

- CPU-only inference may be slower than GPU inference.
- Results depend on input-video quality, camera angle, lighting, and model accuracy.
- RTSP support requires a correctly configured stream publisher/server.
- A reported RTSP status of `running` alone does not prove that frames are being processed or that the dashboard is updating.
- Exact request fields and route behavior should be verified against the current code and FastAPI `/docs`.

## License

Add a license file if you intend to distribute this project publicly. Check the licenses of the model weights and third-party dependencies separately.
