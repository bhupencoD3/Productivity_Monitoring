# main.py
import cv2
import os
import datetime
import asyncio
import sys
from threading import Thread
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
from app.config import DB_CONFIG
from app.face_recognition.detection import ProductivityEyeTracker
from app.face_recognition.recognition import ProductivityRecognizer
from app.dao.employee_dao import EmployeeDAO


app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

tracker_instance = None
recognizer_instance = None
cap = None
monitoring_thread = None
is_monitoring = False
debug_mode = False
frame_log_interval = 60
SHUTDOWN_SECRET = "bhupen"
SESSION_START_TIME = None
PRODUCTIVITY_DATA = {}

employee_dao = EmployeeDAO()


class KnownFace(BaseModel):
    name: str
    path: str


class ShutdownRequest(BaseModel):
    secret: str


def log_productivity_to_db(employee_id, entries):
    for entry in entries:
        success = employee_dao.log_productivity(
            employee_id, entry["start"], entry["end"], entry["duration"]
        )
        if not success:
            print(f"Failed to log productivity for employee {employee_id}")


def log_frame(frame, employee_id, timestamp):
    frame_dir = "frame_logs"
    os.makedirs(frame_dir, exist_ok=True)
    frame_filename = os.path.join(
        frame_dir, f"emp_{employee_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
    )
    success = employee_dao.log_frame(employee_id, frame_filename, timestamp)
    if success:
        cv2.imwrite(frame_filename, frame)
        return frame_filename
    else:
        print(f"Failed to log frame for employee {employee_id}")
        return None


# app/main.py (Snippet)
def process_productivity_data(employee_id, name, frame_filename=None):
    global tracker_instance, SESSION_START_TIME, PRODUCTIVITY_DATA
    stats = tracker_instance.get_productivity_stats()
    current_time = datetime.datetime.now()

    if employee_id not in PRODUCTIVITY_DATA:
        PRODUCTIVITY_DATA[employee_id] = {
            "name": name,
            "session_start": SESSION_START_TIME,
            "total_session_time": 0.0,
            "total_closed_time": 0.0,
            "closure_events": [],
            "frame_references": [],
            "presence_status": "absent",  # Default
        }

    session_duration = (current_time - SESSION_START_TIME).total_seconds()
    PRODUCTIVITY_DATA[employee_id]["total_session_time"] = session_duration
    PRODUCTIVITY_DATA[employee_id]["total_closed_time"] = stats["total_closed"]
    PRODUCTIVITY_DATA[employee_id]["presence_status"] = (
        "present" if stats["current_state"] else "absent"
    )  # Update presence

    if stats["pending_logs"]:
        for log in stats["pending_logs"]:
            PRODUCTIVITY_DATA[employee_id]["closure_events"].append(
                {
                    "start": log["start"].isoformat(),
                    "end": log["end"].isoformat(),
                    "duration": log["duration"],
                }
            )
        if frame_filename:
            PRODUCTIVITY_DATA[employee_id]["frame_references"].append(
                {"timestamp": current_time.isoformat(), "frame_path": frame_filename}
            )

    total_closed = PRODUCTIVITY_DATA[employee_id]["total_closed_time"]
    productivity_score = max(0, 100 - (total_closed / session_duration) * 100)
    PRODUCTIVITY_DATA[employee_id]["productivity_score"] = productivity_score


def monitoring_loop(employee_id, name):
    global \
        tracker_instance, \
        cap, \
        is_monitoring, \
        debug_mode, \
        frame_log_interval, \
        SESSION_START_TIME
    frame_count = 0
    PROCESS_EVERY_NTH_FRAME = 4
    SESSION_START_TIME = datetime.datetime.now()
    timeout_minutes = 10

    while (
        is_monitoring
        and cap
        and cap.isOpened()
        and (datetime.datetime.now() - SESSION_START_TIME).seconds
        < timeout_minutes * 60
    ):
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame in monitoring loop")
            is_monitoring = False
            break

        frame_count += 1
        current_time = datetime.datetime.now()

        if frame_count % PROCESS_EVERY_NTH_FRAME == 0:
            scale_factor = 0.5
            small_frame = cv2.resize(frame, (0, 0), fx=scale_factor, fy=scale_factor)
            eye_state = tracker_instance.process_frame(small_frame)
            stats = tracker_instance.get_productivity_stats()

            if eye_state is None:
                if "no_face_start" not in locals():
                    no_face_start = current_time
                elif (current_time - no_face_start).seconds >= 5:
                    print("No face detected for 5 seconds. Stopping monitoring...")
                    is_monitoring = False
                    break
            else:
                if "no_face_start" in locals():
                    del no_face_start

            if stats["pending_logs"]:
                frame_filename = log_frame(frame, employee_id, current_time)
                if frame_filename:
                    Thread(
                        target=log_productivity_to_db,
                        args=(employee_id, stats["pending_logs"]),
                    ).start()
                    process_productivity_data(employee_id, name, frame_filename)
                    tracker_instance.clear_log_buffer()
                else:
                    process_productivity_data(employee_id, name)

    print("Monitoring stopped")
    is_monitoring = False


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/initialize")
async def initialize():
    global recognizer_instance, cap
    if cap is not None and cap.isOpened():
        cap.release()
    if recognizer_instance is not None:
        recognizer_instance = None

    recognizer_instance = ProductivityRecognizer()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise HTTPException(status_code=500, detail="Could not open webcam.")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    return {"message": "Recognizer initialized successfully"}


@app.get("/recognize")
async def recognize_user(background_tasks: BackgroundTasks):
    global recognizer_instance, cap, tracker_instance, monitoring_thread, is_monitoring
    if recognizer_instance is None or cap is None or not cap.isOpened():
        raise HTTPException(
            status_code=400, detail="Recognizer not initialized or webcam not available"
        )

    start_time = datetime.datetime.now()
    timeout = 20
    frame_count = 0
    frame_skip = 2

    while (datetime.datetime.now() - start_time).seconds < timeout:
        ret, frame = cap.read()
        if not ret:
            raise HTTPException(
                status_code=500, detail="Failed to capture frame from webcam"
            )
        frame_count += 1
        if frame_count % frame_skip == 0:
            if recognizer_instance.recognize_user(frame):
                user_name = recognizer_instance.get_identity()
                employee_id = recognizer_instance.get_employee_id()
                if employee_id is None:
                    raise HTTPException(status_code=500, detail="Employee ID not found")
                tracker_instance = ProductivityEyeTracker()
                is_monitoring = True
                monitoring_thread = Thread(
                    target=monitoring_loop, args=(employee_id, user_name)
                )
                monitoring_thread.start()
                return {
                    "employee_id": employee_id,
                    "name": user_name,
                    "message": "Employee recognized and monitoring started",
                }
    raise HTTPException(status_code=404, detail="No employee recognized within timeout")


@app.get("/stats")
async def get_stats():
    global tracker_instance, PRODUCTIVITY_DATA
    if tracker_instance is None:
        raise HTTPException(status_code=400, detail="Monitoring not started")
    stats = tracker_instance.get_productivity_stats()
    print("Stats from server:", stats)
    employee_id = recognizer_instance.get_employee_id() if recognizer_instance else None
    if employee_id and employee_id in PRODUCTIVITY_DATA:
        productivity_data = PRODUCTIVITY_DATA[employee_id]
        return {
            "current_state": stats["current_state"],
            "total_closed_time": stats["total_closed"],
            "state_since": stats["state_since"].isoformat()
            if stats["state_since"]
            else None,
            "pending_logs": [
                {
                    "start": log["start"].isoformat(),
                    "end": log["end"].isoformat(),
                    "duration": log["duration"],
                }
                for log in stats["pending_logs"]
            ],
            "productivity_data": {
                "name": productivity_data["name"],
                "session_start": productivity_data["session_start"].isoformat(),
                "total_session_time": productivity_data["total_session_time"],
                "total_closed_time": productivity_data["total_closed_time"],
                "closure_events": productivity_data["closure_events"],
                "frame_references": productivity_data["frame_references"],
                "productivity_score": productivity_data["productivity_score"],
            },
        }
    return {
        "current_state": stats["current_state"],
        "total_closed_time": stats["total_closed"],
        "state_since": stats["state_since"].isoformat()
        if stats["state_since"]
        else None,
        "pending_logs": [
            {
                "start": log["start"].isoformat(),
                "end": log["end"].isoformat(),
                "duration": log["duration"],
            }
            for log in stats["pending_logs"]
        ],
    }


@app.post("/stop")
async def stop_monitoring():
    global is_monitoring, cap, monitoring_thread, tracker_instance
    if not is_monitoring:
        raise HTTPException(status_code=400, detail="Monitoring not active")
    is_monitoring = False
    if monitoring_thread:
        monitoring_thread.join()
    if cap and cap.isOpened():
        cap.release()
    if tracker_instance:
        total_closed = tracker_instance.get_productivity_stats()["total_closed"]
        print(
            f"Monitoring ended: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print(f"Total Closed Duration: {total_closed:.1f} seconds")
        employee_id = (
            recognizer_instance.get_employee_id() if recognizer_instance else None
        )
        if employee_id and employee_id in PRODUCTIVITY_DATA:
            productivity_score = PRODUCTIVITY_DATA[employee_id]["productivity_score"]
            print(f"Productivity Score: {productivity_score:.1f}%")
    tracker_instance = None
    return {"message": "Monitoring stopped"}


@app.post("/toggle_debug")
async def toggle_debug():
    global debug_mode
    debug_mode = not debug_mode
    return {"debug_mode": debug_mode}


@app.post("/shutdown")
async def shutdown(request: ShutdownRequest):
    if not request.secret or request.secret.strip() == "":
        raise HTTPException(status_code=422, detail="Secret key cannot be empty")
    if request.secret != SHUTDOWN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid shutdown secret")

    print("Shutting down server...")
    global is_monitoring, cap, monitoring_thread
    is_monitoring = False
    if monitoring_thread:
        monitoring_thread.join()
    if cap and cap.isOpened():
        cap.release()
    asyncio.get_event_loop().call_later(1, sys.exit, 0)
    return {"message": "Server is shutting down"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

