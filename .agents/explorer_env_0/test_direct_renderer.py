import os
import sys
import subprocess
import shutil
import json
import time

def test_direct_render():
    ffmpeg_path = shutil.which("ffmpeg")
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome_path):
        chrome_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    
    out_dir = r"g:\Finding-new-code\harness9\.agents\explorer_env_0\render_test"
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Create a sample HTML+GSAP composition
    html_content = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { margin: 0; padding: 0; width: 1280px; height: 720px; background: #0f172a; color: #f8fafc; font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; overflow: hidden; }
  h1 { font-size: 56px; color: #38bdf8; margin: 0; }
  p { font-size: 28px; color: #94a3b8; margin-top: 16px; }
  .box { width: 100px; height: 100px; background: #f43f5e; border-radius: 12px; margin-top: 30px; }
</style>
</head>
<body>
  <h1 id="title">Harness 9 HyperFrames POC</h1>
  <p id="sub">Automated Video Composition Engine</p>
  <div id="box" class="box"></div>
  <script>
    // Frame step helper
    function seekFrame(frame, totalFrames) {
      const progress = frame / totalFrames;
      document.getElementById("box").style.transform = "rotate(" + (progress * 360) + "deg) scale(" + (1 + 0.5 * Math.sin(progress * Math.PI)) + ")";
      document.getElementById("title").style.opacity = Math.min(1, progress * 4);
    }
  </script>
</body>
</html>"""
    
    html_path = os.path.join(out_dir, "comp.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    # 2. Render frames using Chrome headless or Node
    print("Testing frame capture via Chrome headless...")
    fps = 30
    duration_sec = 2
    total_frames = fps * duration_sec
    
    # Render 10 sample frames or all frames to verify frame generation
    frames_dir = os.path.join(out_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    
    # Generate 15 sample frames for rapid test
    for f_idx in range(15):
        frame_file = os.path.join(frames_dir, f"frame_{f_idx:04d}.png")
        # Chrome screenshot test
        file_url = "file:///" + html_path.replace("\\", "/")
        cmd = [
            chrome_path,
            "--headless=new",
            "--disable-gpu",
            "--window-size=1280,720",
            f"--screenshot={frame_file}",
            file_url
        ]
        # Run single test
        if f_idx == 0:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            print("Frame 0 capture result:", res.returncode, "Exists:", os.path.exists(frame_file))
            break
            
    # 3. Test FFmpeg synthesis of MP4 from generated color/audio test stream
    test_mp4 = os.path.join(out_dir, "test_output.mp4")
    # Generate 2 second synthetic video + audio test via FFmpeg directly
    ffmpeg_cmd = [
        ffmpeg_path,
        "-y",
        "-f", "lavfi",
        "-i", "testsrc=size=1280x720:rate=30",
        "-f", "lavfi",
        "-i", "sine=frequency=440:sample_rate=44100",
        "-t", "2",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        test_mp4
    ]
    res_ffmpeg = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=15)
    print("FFmpeg synth returncode:", res_ffmpeg.returncode)
    
    # 4. Probe generated MP4 with ffprobe
    ffprobe_path = shutil.which("ffprobe")
    probe_cmd = [
        ffprobe_path,
        "-v", "error",
        "-show_entries", "format=duration,size,bit_rate:stream=codec_name,codec_type,width,height",
        "-of", "json",
        test_mp4
    ]
    res_probe = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
    print("FFprobe output:", res_probe.stdout)
    
    results = {
        "ffmpeg_direct_success": res_ffmpeg.returncode == 0 and os.path.exists(test_mp4),
        "mp4_path": test_mp4,
        "mp4_size": os.path.getsize(test_mp4) if os.path.exists(test_mp4) else 0,
        "probe_data": json.loads(res_probe.stdout) if res_probe.returncode == 0 else None
    }
    with open(r"g:\Finding-new-code\harness9\.agents\explorer_env_0\direct_render_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    test_direct_render()
