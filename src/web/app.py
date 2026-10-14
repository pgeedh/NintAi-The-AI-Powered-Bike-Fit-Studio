"""
NintAi Studio — Web Application Backend (FastAPI).
"""
import base64
import os
import shutil
import sys
import tempfile
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src import ai_report, engine, fit_profiles as fp, pose_backends as pb, report

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')
SAMPLES_DIR = os.path.join(ROOT, 'assets', 'examples')

app = FastAPI(title="NintAi Studio", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_path):
        return HTMLResponse("<h3>NintAi Studio UI loading...</h3>")
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.get("/api/config")
def get_config():
    """Return available profiles, pose backends, and sample media."""
    samples = []
    video_dir = os.path.join(SAMPLES_DIR, "videos")
    if os.path.exists(video_dir):
        for fname in sorted(os.listdir(video_dir)):
            if fname.endswith((".mp4", ".mov", ".m4v")):
                samples.append({
                    "id": fname,
                    "type": "video",
                    "title": f"Video: {fname}",
                    "path": f"videos/{fname}",
                })

    image_dir = os.path.join(SAMPLES_DIR, "images")
    if os.path.exists(image_dir):
        for fname in sorted(os.listdir(image_dir)):
            if fname.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                samples.append({
                    "id": fname,
                    "type": "image",
                    "title": f"Photo: {fname}",
                    "path": f"images/{fname}",
                })

    return {
        "profiles": fp.PROFILES,
        "default_profile": fp.DEFAULT_PROFILE,
        "metrics": fp.METRICS,
        "backends": pb.BACKENDS,
        "available_backends": pb.available(),
        "samples": samples,
    }


@app.get("/api/sample_media/{folder}/{filename}")
def get_sample_media(folder: str, filename: str):
    safe_path = os.path.abspath(os.path.join(SAMPLES_DIR, folder, filename))
    if not safe_path.startswith(SAMPLES_DIR) or not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="Sample media not found")
    media_type = "video/mp4" if filename.endswith((".mp4", ".mov")) else "image/jpeg"
    return FileResponse(safe_path, media_type=media_type)


@app.get("/api/demo")
def get_demo_analysis():
    cache_path = os.path.join(ROOT, "assets", "cache", "demo_testvideo2.json")
    if os.path.exists(cache_path):
        import json
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Demo cache not available")


@app.post("/api/analyze")
async def analyze_media(
    file: Optional[UploadFile] = File(None),
    sample_id: Optional[str] = Form(None),
    profile: str = Form("road_endurance"),
    backend: str = Form("auto"),
    crank_mm: float = Form(172.5),
    rider_height: Optional[float] = Form(None),
    api_key: Optional[str] = Form(None),
    rider_name: Optional[str] = Form(""),
    rider_notes: Optional[str] = Form(""),
):
    """
    Main analysis endpoint: accepts file upload OR pre-loaded sample ID.
    Returns kinematics metrics, score, recommendations, snapshots, and video previews.
    """
    temp_path = None
    media_type = "video"

    try:
        if file and file.filename:
            suffix = os.path.splitext(file.filename)[1].lower()
            if suffix in [".jpg", ".jpeg", ".png", ".webp"]:
                media_type = "image"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix or ".mp4") as tmp:
                shutil.copyfileobj(file.file, tmp)
                temp_path = tmp.name
        elif sample_id:
            # Check videos then images
            v_path = os.path.join(SAMPLES_DIR, "videos", sample_id)
            i_path = os.path.join(SAMPLES_DIR, "images", sample_id)
            if os.path.exists(v_path):
                temp_path = v_path
                media_type = "video"
            elif os.path.exists(i_path):
                temp_path = i_path
                media_type = "image"
            else:
                raise HTTPException(status_code=404, detail=f"Sample '{sample_id}' not found")
        else:
            raise HTTPException(status_code=400, detail="Provide an uploaded media file or sample_id")

        if media_type == "video":
            res = engine.analyze_video(
                temp_path,
                profile_key=profile,
                backend=backend,
                crank_mm=crank_mm,
                rider_height_cm=rider_height,
                keep_preview=True,
            )
        else:
            res = engine.analyze_image(
                temp_path,
                profile_key=profile,
                backend=backend,
            )

        # Base64 encode snapshots for clean client rendering
        b64_snaps = {}
        for k, snap in res.get("snapshots", {}).items():
            if snap.get("jpg"):
                b64_snaps[k] = {
                    "title": snap.get("title", k),
                    "data_url": f"data:image/jpeg;base64,{base64.b64encode(snap['jpg']).decode('ascii')}",
                    "angles": snap.get("angles", {}),
                }

        # Base64 encode video previews (scrubber sequence)
        b64_previews = []
        for p in res.get("previews", []):
            if p.get("jpg"):
                b64_previews.append({
                    "t": round(p["t"], 3),
                    "data_url": f"data:image/jpeg;base64,{base64.b64encode(p['jpg']).decode('ascii')}",
                })

        # Timeseries data for charts
        chart_data = None
        if res.get("timeseries") is not None and not res["timeseries"].empty:
            ts = res["timeseries"]
            step = max(1, len(ts) // 100)
            sample_ts = ts.iloc[::step]
            chart_data = {
                "t": [round(float(v), 2) for v in sample_ts["t"]],
                "knee": [round(float(v), 1) if float(v) > 0 else None for v in sample_ts["knee"]],
                "hip": [round(float(v), 1) if float(v) > 0 else None for v in sample_ts["hip"]],
                "torso": [round(float(v), 1) if float(v) > 0 else None for v in sample_ts.get("torso", [])],
            }

        # AI Coach analysis
        coach_text, coach_src = ai_report.generate_ai_analysis(
            res["metrics"],
            res["recommendations"],
            api_key=api_key,
            profile_name=fp.PROFILES[profile]["name"],
            rider_notes=rider_notes or "",
        )

        return {
            "status": "success",
            "mode": res["mode"],
            "backend": res["backend"],
            "backend_name": res["backend_name"],
            "profile": profile,
            "profile_name": fp.PROFILES[profile]["name"],
            "score": res["score"],
            "metrics": res["metrics"],
            "statuses": res["statuses"],
            "recommendations": res["recommendations"],
            "warnings": res["warnings"],
            "biomech": res.get("biomech", {}),
            "extra": res.get("extra", {}),
            "snapshots": b64_snaps,
            "previews": b64_previews,
            "chart_data": chart_data,
            "coach": {
                "text": coach_text,
                "source": coach_src,
            },
        }

    except engine.AnalysisError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        # Clean up temporary upload if we created one
        if temp_path and temp_path.startswith(tempfile.gettempdir()) and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


class PDFRequest(BaseModel):
    result: Optional[dict] = None
    metrics: Optional[dict] = None
    profile: Optional[str] = None
    profile_name: Optional[str] = None
    score: Optional[float] = None
    statuses: Optional[dict] = None
    recommendations: Optional[list] = None
    warnings: Optional[list] = None
    biomech: Optional[dict] = None
    backend_name: Optional[str] = None
    rider_name: Optional[str] = "Cyclist"
    coach_text: Optional[str] = None


@app.post("/api/generate_pdf")
@app.post("/api/report/pdf")
def generate_pdf_endpoint(req: PDFRequest):
    """Generate high-resolution fpdf2 PDF report from analysis results."""
    try:
        res_dict = req.result if req.result else {
            "metrics": req.metrics or {},
            "profile": req.profile or "road_endurance",
            "profile_name": req.profile_name or "Road Endurance",
            "score": req.score or 80.0,
            "statuses": req.statuses or {},
            "recommendations": req.recommendations or [],
            "warnings": req.warnings or [],
            "biomech": req.biomech or {},
            "backend_name": req.backend_name or "RTMPose",
        }
        temp_dir = tempfile.mkdtemp(prefix="nintai_pdf_")
        snap_paths = {}

        for k, snap in res_dict.get("snapshots", {}).items():
            data_url = snap.get("data_url", "")
            if data_url.startswith("data:image/"):
                header, encoded = data_url.split(",", 1)
                img_data = base64.b64decode(encoded)
                p = os.path.join(temp_dir, f"{k}.jpg")
                with open(p, "wb") as f:
                    f.write(img_data)
                snap_paths[k] = p

        pdf_bytes = report.generate_fit_report(
            res_dict,
            snap_paths,
            coach_text=req.coach_text,
            rider_name=req.rider_name or "",
        )

        shutil.rmtree(temp_dir, ignore_errors=True)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=nintai_bike_fit_report.pdf"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
