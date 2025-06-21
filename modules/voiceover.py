--- modules/voiceover.py
+++ modules/voiceover.py
@@ -1,6 +1,8 @@
 import os
 from pathlib import Path
+import subprocess
+import logging
 import json
 import requests
 from dotenv import load_dotenv
@@ -12,6 +14,7 @@ import struct
 load_dotenv()
 
 # Constants
+PROJECT_ROOT = Path(__file__).resolve().parent.parent
 TEMP_DIR = PROJECT_ROOT / "temp"
 TEMP_DIR.mkdir(parents=True, exist_ok=True)
 
@@ -22,6 +25,7 @@ logger = get_logger(__name__)
 def call_elevenlabs_api(text, output_path):
     api_key = os.getenv("ELEVENLABS_API_KEY")
     voice_id = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
+    
     if not api_key:
         logger.error(f"{ErrorCode.ELEVENLABS_FAIL.value}: API key missing")
         return False
@@ -48,6 +52,28 @@ def call_elevenlabs_api(text, output_path):
         return False
 
+def convert_mp3_to_wav(mp3_path: Path, wav_path: Path):
+    """
+    Convert an MP3 file to a 44.1kHz mono WAV using ffmpeg.
+    """
+    try:
+        subprocess.run([
+            "ffmpeg", "-y",
+            "-i", str(mp3_path),
+            "-ar", "44100",
+            "-ac", "1",
+            str(wav_path)
+        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
+        logger.info(f"Converted MP3 to WAV: {wav_path}")
+        mp3_path.unlink(missing_ok=True)
+        return True
+    except Exception as e:
+        logger.error(f"{ErrorCode.VIDEO_RENDER_FAIL.value}: FFmpeg conversion failed: {e}")
+        return False
+
 def generate_voiceover(script_text, output_path, *, test_mode: bool | None = None):
     if test_mode is None:
         test_mode = get_test_mode()
@@ -31,16 +57,23 @@ def generate_voiceover(script_text, output_path, *, test_mode: bool | None = None):
     output_path = Path(output_path)
     output_path.parent.mkdir(parents=True, exist_ok=True)
 
-    if test_mode:
-        logger.info("Test mode active: using dummy audio and skipping ElevenLabs")
-        generate_dummy_audio(output_path)
-    else:
-        logger.info("Calling ElevenLabs API...")
-        success = call_elevenlabs_api(script_text, output_path)
-        if not success:
-            logger.error(f"{ErrorCode.ELEVENLABS_FAIL.value}: generation failed")
-            raise RuntimeError(ErrorCode.ELEVENLABS_FAIL.value)
+    if test_mode:
+        logger.info("Test mode active: using dummy audio and skipping ElevenLabs")
+        generate_dummy_audio(output_path)
+        return
+
+    # Real mode: first fetch raw MP3
+    logger.info("Calling ElevenLabs API for MP3...")
+    mp3_path = output_path.with_suffix(".mp3")
+    if not call_elevenlabs_api(script_text, mp3_path):
+        logger.error(f"{ErrorCode.ELEVENLABS_FAIL.value}: MP3 generation failed")
+        raise RuntimeError(ErrorCode.ELEVENLABS_FAIL.value)
+
+    # Convert MP3 to WAV
+    logger.info("Converting MP3 to WAV...")
+    if not convert_mp3_to_wav(mp3_path, output_path):
+        logger.error(f"{ErrorCode.ELEVENLABS_FAIL.value}: WAV conversion failed")
+        raise RuntimeError(ErrorCode.ELEVENLABS_FAIL.value)
+
+    logger.info(f"Voiceover ready at {output_path}")
