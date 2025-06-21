import os
import subprocess
import time
import shutil

def banner(msg):
    print("\n" + "=" * 60)
    print(f"[AUTO TEST] {msg}")
    print("=" * 60 + "\n")

def check_file_exists(path):
    if not os.path.exists(path):
        print(f"[FAIL] Missing: {path}")
        return False
    print(f"[OK] Found: {path}")
    return True

def run_pipeline():
    banner("Running Full Pipeline")
    result = subprocess.run(["python", "test_inputs/test_pipeline.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("[FAIL] Pipeline failed.")
        print(result.stderr)
        return False
    print("[OK] Pipeline completed successfully.")
    return True

def validate_output():
    banner("Validating Output Artifacts")
    ok = True
    ok &= check_file_exists("temp/voice.wav")
    ok &= check_file_exists("temp/subtitles.ass")
    ok &= check_file_exists("output/final_render.mp4")
    return ok

def clean_temp_output():
    banner("Cleaning temp/output for fresh test")
    shutil.rmtree("temp", ignore_errors=True)
    shutil.rmtree("output", ignore_errors=True)
    os.makedirs("temp", exist_ok=True)
    os.makedirs("output", exist_ok=True)

def main():
    clean_temp_output()
    if not run_pipeline():
        return
    if not validate_output():
        print("[FAIL] Test failed due to missing outputs.")
    else:
        print("\n[PASS] All systems go. Full pipeline test passed.")

if __name__ == "__main__":
    main()