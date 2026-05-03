"""
Cricket Analyzer – uses Gemini Vision to extract structured shot data
from cricket images or video frames.
Uses the new google-genai SDK (google-genai >= 1.0.0)
"""

import json
import re
import tempfile
import os
from PIL import Image
import io

try:
    from google import genai
    from google.genai import types
    NEW_SDK = True
except ImportError:
    import google.generativeai as genai
    NEW_SDK = False


ANALYSIS_PROMPT = """You are an expert cricket analyst with deep knowledge of cricket shots, ball deliveries, and match statistics.

Analyze this cricket image/frame carefully and extract detailed information. Return ONLY a valid JSON object with these exact keys:

{{
  "shot_type": "Name of shot played (e.g., Cover Drive, Pull Shot, Sweep, Cut Shot, Flick, Straight Drive, Hook, Defensive Block, Loft, Glance, etc.)",
  "ball_type": "Type of delivery (e.g., Full Toss, Good Length, Short Pitch, Yorker, Bouncer, Swing, Off-spin, Leg-spin, Googly, In-swinger, Out-swinger, Seam Delivery, etc.)",
  "pitch_length": "Where ball pitched (e.g., Full, Good Length, Short of Good Length, Short Pitch, Yorker Length, Half Volley)",
  "ball_speed": "Estimated ball speed or 'Cannot determine from image'",
  "runs_scored": "Estimated runs (0, 1, 2, 3, 4, 6, or 'Cannot determine')",
  "shot_direction": "Direction of shot (e.g., Cover, Mid-On, Mid-Off, Square Leg, Fine Leg, Point, Third Man, Long-On, Long-Off, Midwicket)",
  "outcome": "What happened (e.g., Boundary 4, Six, Dot Ball, Wicket, Single, Two Runs, Caught, LBW, Bowled, etc.)",
  "batting_stance": "Batsman's stance (e.g., Right-handed, Left-handed, Open stance, Closed stance)",
  "commentary": "A vivid 2-3 sentence ball-by-ball commentary describing exactly what happened in the image",
  "player_insights": "Brief insight about the batsman's technique or footwork visible in the image",
  "tactical_observation": "Tactical observation about field placement, shot selection, or bowling strategy"
}}

Additional context provided:
- Over: {over}
- Ball: {ball}
- Batting Team: {batting_team}
- Bowling Team: {bowling_team}
- Batsman: {batsman}
- Bowler: {bowler}
- Notes: {notes}

If any field cannot be determined from the image, use a reasonable cricket-informed guess or write "Cannot determine".
Return ONLY the JSON object, no markdown, no explanation.
"""


class CricketAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        if NEW_SDK:
            self.client = genai.Client(api_key=api_key)
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-2.5-flash")

    def _extract_frame_from_video(self, video_file) -> Image.Image:
        """Extract a frame from video using OpenCV."""
        try:
            import cv2

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(video_file.read())
                tmp_path = tmp.name

            cap = cv2.VideoCapture(tmp_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            target_frame = max(1, total_frames // 10)
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            ret, frame = cap.read()
            cap.release()
            os.unlink(tmp_path)

            if ret:
                import numpy as np
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                return Image.fromarray(frame_rgb)
        except Exception:
            pass
        return None

    def _call_gemini(self, prompt: str, img_bytes: bytes) -> str:
        """Call Gemini API with image and return text response."""
        if NEW_SDK:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                    prompt,
                ],
            )
            return response.text
        else:
            response = self.model.generate_content(
                [
                    prompt,
                    {"mime_type": "image/jpeg", "data": img_bytes},
                ]
            )
            return response.text

    def analyze(self, uploaded_file, upload_mode: str, context: dict) -> dict:
        """Analyze an image or video for cricket shot details."""
        raw_text = ""
        try:
            if upload_mode == "Image":
                image = Image.open(uploaded_file)
            else:
                image = self._extract_frame_from_video(uploaded_file)
                if image is None:
                    return {
                        "success": False,
                        "error": (
                            "Could not extract video frame. "
                            "Please install opencv-python or upload an image instead."
                        ),
                    }

            # Convert to JPEG bytes
            img_bytes_io = io.BytesIO()
            if image.mode in ("RGBA", "P", "LA"):
                image = image.convert("RGB")
            image.save(img_bytes_io, format="JPEG")
            img_bytes = img_bytes_io.getvalue()

            prompt = ANALYSIS_PROMPT.format(
                over=context.get("over", "N/A"),
                ball=context.get("ball", "N/A"),
                batting_team=context.get("batting_team", "N/A") or "N/A",
                bowling_team=context.get("bowling_team", "N/A") or "N/A",
                batsman=context.get("batsman", "N/A") or "N/A",
                bowler=context.get("bowler", "N/A") or "N/A",
                notes=context.get("notes", "None") or "None",
            )

            raw_text = self._call_gemini(prompt, img_bytes).strip()

            # Strip markdown code fences if present
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
            raw_text = re.sub(r"\s*```$", "", raw_text)

            data = json.loads(raw_text)
            return {"success": True, "data": data}

        except json.JSONDecodeError:
            try:
                match = re.search(r"\{.*\}", raw_text, re.DOTALL)
                if match:
                    data = json.loads(match.group())
                    return {"success": True, "data": data}
            except Exception:
                pass
            return {
                "success": False,
                "error": f"JSON parse error. Raw response: {raw_text[:400]}",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
