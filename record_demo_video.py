import asyncio
import glob
import os
import subprocess
import imageio_ffmpeg
from playwright.async_api import async_playwright

ARTIFACTS_DIR = "/config/.gemini/antigravity/brain/a4ab4c96-8b5d-47f7-9dc6-01dc33c185aa"

async def record_demo():
    os.makedirs("video_temp", exist_ok=True)
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    
    async with async_playwright() as p:
        print("Launching Chromium browser...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir="video_temp",
            record_video_size={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        
        app_url = "https://recipe-assistant-frontend-358830685831.us-east4.run.app"
        print(f"Navigating to Recipe Assistant app ({app_url})...")
        await page.goto(app_url, timeout=20000)
        await page.wait_for_timeout(2000)
        
        # --- Prompt 1: Core capability ---
        prompt1 = "What can I cook with chicken, garlic, and spinach considering my allergies?"
        print(f"Typing Prompt 1: '{prompt1}'...")
        
        input_elem = page.locator("#input")
        await input_elem.focus()
        await input_elem.type(prompt1, delay=30)
        await page.wait_for_timeout(500)
        
        print("Submitting Prompt 1...")
        await page.click(".send-btn")
        
        print("Waiting for Agent response to Prompt 1...")
        await page.wait_for_selector(".msg-row.agent .bubble", timeout=30000)
        await page.wait_for_timeout(4000)
        
        # --- Prompt 2: Richer prompt with Tool Call & Image Generation ---
        prompt2 = "Generate a delicious image of Garlic Herb Butter Chicken and show my favorite saved recipes."
        print(f"Typing Prompt 2: '{prompt2}'...")
        
        await input_elem.focus()
        await input_elem.type(prompt2, delay=30)
        await page.wait_for_timeout(500)
        
        print("Submitting Prompt 2...")
        await page.click(".send-btn")
        
        print("Waiting for Agent response to Prompt 2...")
        await page.wait_for_timeout(10000)
        
        # Scroll down to ensure full response is visible
        await page.evaluate("document.getElementById('log').scrollTop = document.getElementById('log').scrollHeight")
        await page.wait_for_timeout(4000)
        
        print("Closing page & context to save video...")
        video_obj = page.video
        await context.close()
        video_path = await video_obj.path()
        print(f"Raw Playwright video saved to: {video_path}")
        await browser.close()
        
        # Merge raw video with lo-fi background audio
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        output_mp4 = os.path.join(ARTIFACTS_DIR, "demo_video.mp4")
        
        print(f"Merging video and lo-fi audio track into {output_mp4}...")
        cmd = [
            ffmpeg_exe,
            "-y",
            "-i", video_path,
            "-i", "lofi_music.wav",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_mp4
        ]
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"🎉 Demo video successfully created at: {output_mp4}")
        else:
            print(f"FFmpeg error: {res.stderr}")
            import shutil
            fallback_path = os.path.join(ARTIFACTS_DIR, "demo_video.webm")
            shutil.copy(video_path, fallback_path)
            print(f"Copied raw video to: {fallback_path}")

if __name__ == "__main__":
    asyncio.run(record_demo())
