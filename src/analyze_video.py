"""
CLI tool for NintAi dynamic video analysis.
"""
import argparse
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src import engine
from src import fit_profiles as fp
from src import report
from src import ai_report


def main():
    parser = argparse.ArgumentParser(description="NintAi AI-Powered Dynamic Bike Fit Analysis")
    parser.add_argument("--input", "-i", type=str, required=True, help="Input video path")
    parser.add_argument("--output_video", "-ov", type=str, help="Output annotated video path (.mp4)")
    parser.add_argument("--output_pdf", "-op", type=str, default="output/nintai_fit_report.pdf",
                        help="Output PDF path")
    parser.add_argument("--profile", "-p", type=str, default="road_endurance",
                        choices=list(fp.PROFILES.keys()), help="Riding style profile")
    parser.add_argument("--backend", "-b", type=str, default="auto",
                        choices=["auto", "rtmpose", "mediapipe"], help="Pose estimation engine")
    parser.add_argument("--api_key", type=str, help="Google Gemini API key (or set GOOGLE_API_KEY)")
    parser.add_argument("--rider_name", type=str, default="", help="Rider name for the report")
    parser.add_argument("--crank_mm", type=float, default=172.5, help="Crank arm length in mm")
    parser.add_argument("--rider_height", type=float, help="Rider height in cm for scale")
    args = parser.parse_args()

    print(f"\n🚴 NintAi Dynamic Bike Fit Analysis")
    print(f"   Video:   {args.input}")
    print(f"   Profile: {fp.PROFILES[args.profile]['name']}")
    print(f"   Backend: {args.backend}")

    def progress(frac, msg):
        pct = int(frac * 100)
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        print(f"\r   [{bar}] {pct:3d}% — {msg}", end="", flush=True)

    print()
    try:
        result = engine.analyze_video(
            args.input,
            profile_key=args.profile,
            backend=args.backend,
            progress_cb=progress,
            output_video=args.output_video,
            crank_mm=args.crank_mm,
            rider_height_cm=args.rider_height,
        )
    except engine.AnalysisError as e:
        print(f"\n❌ Analysis error: {e}")
        sys.exit(1)

    print("\n\n📊 Dynamic Kinematics Results:")
    print(f"   Overall Fit Score: {result['score']}/100")
    print("   --------------------------------------------------------")
    for k, m in fp.METRICS.items():
        v = result['metrics'].get(k, 0)
        lo, hi = fp.PROFILES[args.profile]['ranges'][k]
        st = result['statuses'].get(k, 'na').upper()
        print(f"   {m['label']:<34} {v:5.1f}°  (Target: {lo}–{hi}°) [{st}]")

    if result['biomech'].get('cadence_rpm'):
        print(f"   Cadence:                       {result['biomech']['cadence_rpm']:5.1f} rpm")
    if result['biomech'].get('kops_mm') is not None:
        print(f"   KOPS (3 o'clock offset):       {result['biomech']['kops_mm']:+5.1f} mm")
    if result['biomech'].get('hip_rock_mm') is not None:
        print(f"   Hip Rock (vertical sway):      {result['biomech']['hip_rock_mm']:5.1f} mm")
    if result['biomech'].get('saddle_adj_mm') is not None:
        adj = result['biomech']['saddle_adj_mm']
        action = f"Raise saddle ~{abs(adj):.0f} mm" if adj > 0 else f"Lower saddle ~{abs(adj):.0f} mm"
        print(f"   Recommended Saddle Adjustment: {action}")

    if result['warnings']:
        print("\n⚠️ Capture Notes:")
        for w in result['warnings']:
            print(f"   - {w}")

    print("\n🛠️ Recommended Adjustments (in order):")
    for i, r in enumerate(result['recommendations'], 1):
        print(f"   {i}. {r['title']}")
        print(f"      {r['detail']}")

    # Snapshots & PDF Report
    out_dir = os.path.dirname(os.path.abspath(args.output_pdf))
    os.makedirs(out_dir, exist_ok=True)
    snap_paths = engine.save_snapshots(result, os.path.join(out_dir, "snapshots"))

    print("\n🤖 Generating AI Coach Verdict...")
    coach_text, src = ai_report.generate_ai_analysis(
        result['metrics'],
        result['recommendations'],
        api_key=args.api_key,
        profile_name=fp.PROFILES[args.profile]['name'],
    )
    print(f"   Coach source: {src.upper()}")

    report.generate_fit_report(
        result,
        snap_paths,
        output_path=args.output_pdf,
        coach_text=coach_text,
        rider_name=args.rider_name,
    )
    print(f"\n✅ Fit Report successfully saved to: {args.output_pdf}\n")


if __name__ == "__main__":
    main()
