import time
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Setup Selenium for headless Chrome on macOS
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)

# Navigate directly to KBS 1FM using its channel code
driver.get("https://onair.kbs.co.kr/index.html?sname=onair&stype=live&ch_code=24")

try:
    # Wait for JWPlayer to initialize and extract stream URL
    print("Waiting for stream to load...")
    WebDriverWait(driver, 15).until(
        lambda d: d.execute_script("return typeof jwplayer === 'function' && jwplayer('kbs-social-player').getPlaylistItem() != null")
    )

    stream_url = driver.execute_script("return jwplayer('kbs-social-player').getPlaylistItem().file;")
    print("Stream URL obtained:", stream_url)

    # Record using ffmpeg for 2 hours (7200 seconds)
    output_file = "kbs_1fm_recording.ts"
    print(f"Starting recording to {output_file} for 2 hours...")

    ffmpeg_cmd = [
        "ffmpeg",
        "-i", stream_url,
        "-c", "copy",
        "-t", "7200",
        output_file
    ]
    subprocess.run(ffmpeg_cmd)

except Exception as e:
    print("Error occurred:", e)
finally:
    driver.quit()