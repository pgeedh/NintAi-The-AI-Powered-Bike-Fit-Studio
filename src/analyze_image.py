"""
CLI tool for NintAi single-image fit analysis.
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
    parser = argparse.ArgumentParser(description="NintAi AI-Powered Static Photo Bike Fit Analysis")
    parser.add_argument("--input", "-i", type=str, required=True, help="Input photo path")
    parser.add_argument("--output_image", "-o", type=str, help="Output annotated image path")
    parser.add_argument("--output_pdf", "-op", type=str, default="output/nintai_photo_report.pdf",
                        help="Output PDF path")
    parser.add_argument("--profile", "-p", type=str, default="road_endurance",
                        choices=list(fp.PROFILES.keys()), help="Riding style profile")
    parser.add_argument("--backend", "-b", type=str, default="auto",
                        choices=["auto", "rtmpose", "mediapipe"], help="Pose estimation engine")
    parser.add_argument("--crank_pos", type=str, default="auto",
                        choices=["auto", "bottom", "top", "other"], help="Pedal position in photo")
    parser.add_argument("--api_key", type=str, help="Google Gemini API key (or set GOOGLE_API_KEY)")
    parser.add_argument("--rider_name", type=str, default="", help="Rider name for the report")
    args = parser.parse_args()

    print(f"\n🚴 NintAi Static Photo Fit Analysis")
    print(f"   Photo:   {args.input}")
    print(f"   Profile: {fp.PROFILES[args.profile]['name']}")
    print(f"   Backend: {args.backend}")

    try:
        result = engine.analyze_image(
            args.input,
            profile_key=args.profile,
            crank_position=args.crank_pos,
            backend=args.backend,
        )
    except engine.AnalysisError as e:
        print(f"\n❌ Analysis error: {e}")
        sys.exit(1)

    print("\n📊 Kinematics Results:")
    print(f"   Overall Fit Score: {result['score']}/100")
    print("   --------------------------------------------------------")
    for k, m in fp.METRICS.items():
        v = result['metrics'].get(k, 0)
        lo, hi = fp.PROFILES[args.profile]['ranges'][k]
        st = result['statuses'].get(k, 'na').upper()
        if v > 0:
            print(f"   {m['label']:<34} {v:5.1f}°  (Target: {lo}–{hi}°) [{st}]")

    if result['warnings']:
        print("\n⚠️ Capture Notes:")
        for w in result['warnings']:
            print(f"   - {w}")

    print("\n🛠️ Recommended Adjustments:")
    for i, r in enumerate(result['recommendations'], 1):
        print(f"   {i}. {r['title']}")
        print(f"      {r['detail']}")

    out_dir = os.path.dirname(os.path.abspath(args.output_pdf))
    os.makedirs(out_dir, exist_ok=True)
    snap_paths = engine.save_snapshots(result, os.path.join(out_dir, "snapshots"))

    if args.output_image and 'photo' in snap_paths:
        import shutil
        shutil.copyfile(snap_paths['photo'], args.output_image)
        print(f"\n📸 Annotated image saved to: {args.output_image}")

    print("\n🤖 Generating AI Coach Verdict...")
    coach_text, src = ai_report.generate_ai_analysis(
        result['metrics'],
        result['recommendations'],
        api_key=args.api_key,
        profile_name=fp.PROFILES[args.profile]['name'],
    )

    report.generate_fit_report(
        result,
        snap_paths,
        output_path=args.output_pdf,
        coach_text=coach_text,
        rider_name=args.rider_name,
    )
    print(f"✅ Fit Report successfully saved to: {args.output_pdf}\n")


if __name__ == "__main__":
    main()
