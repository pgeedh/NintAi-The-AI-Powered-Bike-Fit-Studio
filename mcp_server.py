#!/usr/bin/env python3
"""
Open-BikeFit Claude Model Context Protocol (MCP) Server.
Enables Claude Desktop and MCP clients to directly run dynamic cycling kinematics,
analyze video motion capture, query reference targets, and compile studio PDF fit reports.
"""

import sys
import os
import json
import logging

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.kinematics import FIT_TARGETS
from src.ai_fitter import generate_rule_based_breakdown
from src.pdf_generator import build_clinical_pdf
from src.analyzer import process_cycling_video

logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="[Open-BikeFit MCP] %(message)s")

SERVER_INFO = {
    "name": "open-bikefit-mcp",
    "version": "2.5.0"
}

TOOLS = [
    {
        "name": "openbikefit_list_sample_datasets",
        "description": "Lists all pre-packaged studio cycling sample datasets available in the repository with duration and frame stats.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "openbikefit_get_fit_targets",
        "description": "Returns standard biomechanical joint angle envelopes and targets for a specified cycling discipline (ROAD, GRAVEL_ENDURANCE, TRIATHLON_TT, MTB).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "discipline": {
                    "type": "string",
                    "enum": ["ROAD", "GRAVEL_ENDURANCE", "TRIATHLON_TT", "MTB"],
                    "description": "Cycling discipline to fetch target envelopes for.",
                    "default": "ROAD"
                }
            },
            "required": ["discipline"]
        }
    },
    {
        "name": "openbikefit_analyze_video",
        "description": "Runs real-time 33-landmark MediaPipe BlazePose Heavy tracking, 1€ adaptive temporal filtering, bone length invariance enforcement, and 4-phase pedal stroke decomposition on a video file. Returns observed joint angles (Holmes knee extension, Pruitt flexion, closed hip, torso incline, arm reach, ankling) and snapshot filepaths.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "video_path": {
                    "type": "string",
                    "description": "Relative or absolute path to cycling trainer video (e.g. 'inputs/videos/sample_road_endurance.mp4')."
                },
                "discipline": {
                    "type": "string",
                    "enum": ["ROAD", "GRAVEL_ENDURANCE", "TRIATHLON_TT", "MTB"],
                    "description": "Target discipline for comparison.",
                    "default": "ROAD"
                }
            },
            "required": ["video_path"]
        }
    },
    {
        "name": "openbikefit_generate_report",
        "description": "Generates a structured, deterministic biomechanical bike fit report with exact millimeter wrench adjustments (saddle height +/-mm, saddle fore/aft +/-mm, stack spacers +/-mm, stem reach) cross-referenced against rider symptoms.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kinematic_stats": {
                    "type": "object",
                    "description": "Measured angles dictionary containing knee_ext_max, knee_flex_min, hip_closed_min, back_avg, arm_avg, ankling_avg."
                },
                "discipline": {
                    "type": "string",
                    "enum": ["ROAD", "GRAVEL_ENDURANCE", "TRIATHLON_TT", "MTB"],
                    "default": "ROAD"
                },
                "rider_name": {
                    "type": "string",
                    "default": "Cyclist"
                },
                "rider_goal": {
                    "type": "string",
                    "default": "Balanced Performance"
                },
                "pain_points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Reported rider discomfort symptoms (e.g. 'Front of Knee (Patella / Anterior)', 'Lower Back Fatigue')."
                }
            },
            "required": ["kinematic_stats"]
        }
    },
    {
        "name": "openbikefit_compile_pdf",
        "description": "Compiles a high-resolution studio PDF dossier embedding 4-phase pedal stroke stills (TDC, 3 o'clock Power, BDC, Overall), metrics comparison table, and millimeter wrench instructions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kinematic_stats": {
                    "type": "object",
                    "description": "Measured angles dictionary with snapshot paths."
                },
                "report_text": {
                    "type": "string",
                    "description": "Markdown formatted fit summary / consultation text."
                },
                "output_pdf_path": {
                    "type": "string",
                    "default": "outputs/reports/openbikefit_studio_report.pdf"
                },
                "rider_name": {
                    "type": "string",
                    "default": "Cyclist"
                },
                "discipline": {
                    "type": "string",
                    "default": "ROAD"
                }
            },
            "required": ["kinematic_stats", "report_text"]
        }
    }
]

RESOURCES = [
    {
        "uri": "openbikefit://targets/all",
        "name": "Complete Discipline Biomechanical Target Envelopes",
        "description": "Reference joint angle ranges for Road, Gravel, Triathlon/TT, and MTB.",
        "mimeType": "application/json"
    },
    {
        "uri": "openbikefit://protocols/holmes",
        "name": "Holmes Knee Extension Biomechanical Protocol",
        "description": "Scientific justification and dynamic angle bounds for Holmes BDC saddle height methodology.",
        "mimeType": "text/plain"
    }
]


def handle_tool_call(name: str, arguments: dict) -> dict:
    if name == "openbikefit_list_sample_datasets":
        samples_dir = os.path.join(PROJECT_ROOT, "inputs", "videos")
        samples = []
        if os.path.exists(samples_dir):
            for f in os.listdir(samples_dir):
                if f.endswith((".mp4", ".mov", ".avi")):
                    p = os.path.join(samples_dir, f)
                    samples.append({
                        "filename": f,
                        "path": os.path.relpath(p, PROJECT_ROOT),
                        "size_mb": round(os.path.getsize(p) / (1024 * 1024), 2)
                    })
        return {"samples": samples}

    elif name == "openbikefit_get_fit_targets":
        disc = arguments.get("discipline", "ROAD").upper()
        targets = FIT_TARGETS.get(disc, FIT_TARGETS["ROAD"])
        return {
            "discipline": disc,
            "targets": {
                "knee_extension_bdc_6h": {"min": targets["knee_ext_max"][0], "max": targets["knee_ext_max"][1], "unit": "degrees"},
                "knee_flexion_tdc_12h": {"min": targets["knee_flex_min"][0], "max": targets["knee_flex_min"][1], "unit": "degrees"},
                "closed_hip_tdc": {"min": targets["hip_closed_min"][0], "max": targets["hip_closed_min"][1], "unit": "degrees"},
                "torso_incline_horizontal": {"min": targets["back_avg"][0], "max": targets["back_avg"][1], "unit": "degrees"},
                "shoulder_reach_angle": {"min": targets["arm_avg"][0], "max": targets["arm_avg"][1], "unit": "degrees"},
                "ankle_plantarflexion_bdc": {"min": targets["ankling_bdc"][0], "max": targets["ankling_bdc"][1], "unit": "degrees"}
            }
        }

    elif name == "openbikefit_analyze_video":
        rel_path = arguments.get("video_path")
        abs_path = os.path.abspath(os.path.join(PROJECT_ROOT, rel_path)) if not os.path.isabs(rel_path) else rel_path
        
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Video file not found at: {abs_path}")

        disc = arguments.get("discipline", "ROAD").upper()
        out_vid = os.path.join(PROJECT_ROOT, "outputs", "videos", "annotated_mcp_run.mp4")
        out_pdf = os.path.join(PROJECT_ROOT, "outputs", "reports", "temp_mcp_report.pdf")
        os.makedirs(os.path.dirname(out_vid), exist_ok=True)
        os.makedirs(os.path.dirname(out_pdf), exist_ok=True)

        stats = process_cycling_video(
            input_path=abs_path,
            output_video_path=out_vid,
            output_pdf_path=out_pdf,
            discipline=disc,
            provider="OFFLINE"
        )
        return stats

    elif name == "openbikefit_generate_report":
        stats = arguments.get("kinematic_stats", {})
        disc = arguments.get("discipline", "ROAD").upper()
        targets = FIT_TARGETS.get(disc, FIT_TARGETS["ROAD"])
        rider_profile = {
            "name": arguments.get("rider_name", "Cyclist"),
            "discipline": disc,
            "goal": arguments.get("rider_goal", "Balanced Performance"),
            "pain_points": arguments.get("pain_points", [])
        }
        report_text = generate_rule_based_breakdown(stats, targets, rider_profile)
        return {"report_markdown": report_text}

    elif name == "openbikefit_compile_pdf":
        stats = arguments.get("kinematic_stats", {})
        report_text = arguments.get("report_text", "")
        rel_out = arguments.get("output_pdf_path", "outputs/reports/openbikefit_studio_report.pdf")
        abs_out = os.path.abspath(os.path.join(PROJECT_ROOT, rel_out)) if not os.path.isabs(rel_out) else rel_out
        os.makedirs(os.path.dirname(abs_out), exist_ok=True)

        disc = arguments.get("discipline", "ROAD").upper()
        targets = FIT_TARGETS.get(disc, FIT_TARGETS["ROAD"])
        rider_profile = {
            "name": arguments.get("rider_name", "Cyclist"),
            "discipline": disc,
            "goal": "Biomechanical Baseline"
        }

        build_clinical_pdf(
            snap_tdc=stats.get("snap_tdc", "outputs/snapshots/phase_tdc.jpg"),
            snap_bdc=stats.get("snap_bdc", "outputs/snapshots/phase_bdc.jpg"),
            snap_power=stats.get("snap_power", "outputs/snapshots/phase_power.jpg"),
            snap_overall=stats.get("snap_overall", "outputs/snapshots/phase_overall.jpg"),
            stats=stats,
            targets=targets,
            consultation_text=report_text,
            output_path=abs_out,
            rider_profile=rider_profile
        )
        return {"status": "success", "pdf_path": os.path.relpath(abs_out, PROJECT_ROOT), "size_bytes": os.path.getsize(abs_out)}

    else:
        raise ValueError(f"Unknown tool: {name}")


def handle_resource_read(uri: str) -> dict:
    if uri == "openbikefit://targets/all":
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(FIT_TARGETS, indent=2)
                }
            ]
        }
    elif uri == "openbikefit://protocols/holmes":
        text = """
Holmes Biomechanical Knee Angle Protocol:
- Optimal Knee Extension Window at BDC (Bottom Dead Center 6h): 140° to 150°.
- Measured as the interior angle between the greater trochanter -> lateral femoral condyle -> lateral malleolus.
- Rationale:
  * Angles < 140° cause excessive patellofemoral compression force, leading to anterior patellar tendinopathy.
  * Angles > 150° force hamstring hyperextension, pelvic instability, and saddle sores from side-to-side rocking.
- Correction factor: Each 1° of angular deficit corresponds to approximately 2.8 mm of vertical saddle height adjustment.
"""
        return {
            "contents": [
                {"uri": uri, "mimeType": "text/plain", "text": text.strip()}
            ]
        }
    else:
        raise ValueError(f"Resource not found: {uri}")


def main():
    """Stdio JSON-RPC 2.0 Loop for Claude Desktop / MCP Clients."""
    logging.info("Open-BikeFit MCP Server started in stdio mode.")
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            line = line.strip()
            if not line:
                continue

            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if method == "initialize":
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {},
                            "resources": {}
                        },
                        "serverInfo": SERVER_INFO
                    }
                }
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()

            elif method == "notifications/initialized":
                # Client acknowledgment
                continue

            elif method == "tools/list":
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": TOOLS
                    }
                }
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()

            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                try:
                    tool_output = handle_tool_call(tool_name, tool_args)
                    res = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(tool_output, indent=2) if isinstance(tool_output, dict) else str(tool_output)
                                }
                            ]
                        }
                    }
                except Exception as e:
                    res = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "isError": True,
                        "result": {
                            "content": [{"type": "text", "text": f"Error executing tool {tool_name}: {str(e)}"}]
                        }
                    }
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()

            elif method == "resources/list":
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "resources": RESOURCES
                    }
                }
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()

            elif method == "resources/read":
                uri = params.get("uri")
                try:
                    r_res = handle_resource_read(uri)
                    res = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": r_res
                    }
                except Exception as e:
                    res = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32602, "message": str(e)}
                    }
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()

            elif method == "ping":
                res = {"jsonrpc": "2.0", "id": req_id, "result": {}}
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()

            else:
                if req_id is not None:
                    res = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32601, "message": f"Method not found: {method}"}
                    }
                    sys.stdout.write(json.dumps(res) + "\n")
                    sys.stdout.flush()

        except Exception as e:
            logging.error(f"Error handling message: {e}")


if __name__ == "__main__":
    main()
