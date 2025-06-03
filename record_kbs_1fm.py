import requests
import subprocess
import datetime
import os
import re
import time

def get_signed_url(channel_code=24):
    """Fetches the live streaming URL for the given channel code (e.g., 24 for 1FM)."""
    api_url = f"https://cfpwwwapi.kbs.co.kr/api/v1/landing/live/channel_code/{channel_code}"
    response = requests.get(api_url)
    response.raise_for_status()

    data = response.json()
    try:
        url = data["channel_item"][0]["service_url"]
        print(f"[INFO] Signed stream URL:\n{url}")
        return url
    except (KeyError, IndexError):
        raise ValueError("Could not find a valid streaming URL in API response.")

def extract_expiry_from_url(url):
    """Extracts the Expires=UNIXTIMESTAMP from the signed URL."""
    match = re.search(r"Expires=(\d+)", url)
    if match:
        return int(match.group(1))
    raise ValueError("Expires= timestamp not found in URL.")

def record_stream(stream_url, duration_seconds, output_path, chunk_num):
    """Records the stream using ffmpeg for a given duration."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_path, f"kbs_1fm_chunk{chunk_num}_{timestamp}.mp3")

    print(f"[INFO] Starting recording chunk {chunk_num}: {duration_seconds} sec → {output_file}")

    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output
        "-i", stream_url,
        "-t", str(duration_seconds),
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        output_file
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"[SUCCESS] Chunk {chunk_num} saved: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] ffmpeg failed for chunk {chunk_num}: {e}")

def smart_record(total_duration=7200, buffer_seconds=600, output_dir="./recordings"):
    os.makedirs(output_dir, exist_ok=True)

    seconds_remaining = total_duration
    chunk_num = 1

    while seconds_remaining > 0:
        signed_url = get_signed_url()
        expires_at = extract_expiry_from_url(signed_url)
        now = int(time.time())

        safe_duration = expires_at - now - buffer_seconds
        if safe_duration <= 0:
            print("[WARN] Signed URL expires too soon. Skipping this URL.")
            time.sleep(5)
            continue

        duration_this_chunk = min(safe_duration, seconds_remaining)
        print(f"[INFO] Will record for {duration_this_chunk} seconds (expires in {expires_at - now}s)")

        record_stream(signed_url, duration_this_chunk, output_dir, chunk_num)

        seconds_remaining -= duration_this_chunk
        chunk_num += 1

    print("[DONE] All chunks recorded.")

    # === Auto-Merge Chunks ===
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    merged_output = os.path.join(output_dir, f"kbs_1fm_full_{timestamp}.mp3")
    list_file = os.path.join(output_dir, "chunks.txt")

    # Find all chunk files
    chunk_files = sorted(f for f in os.listdir(output_dir) if f.startswith("kbs_1fm_chunk") and f.endswith(".mp3"))

    # Write them to chunks.txt
    with open(list_file, "w") as f:
        for chunk in chunk_files:
            f.write(f"file '{os.path.abspath(os.path.join(output_dir, chunk))}'\n")

    print("[INFO] Merging chunks into one file...")
    cmd = [
        "ffmpeg", "-f", "concat", "-safe", "0", "-i", list_file,
        "-c", "copy", merged_output
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"[SUCCESS] Merged file saved: {merged_output}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to merge chunks: {e}")

    for chunk in chunk_files:
        os.remove(os.path.join(output_dir, chunk))
    os.remove(list_file)
    print("[INFO] Cleaned up chunk files.")

if __name__ == "__main__":
    TOTAL_RECORDING_DURATION = 2 * 60 * 60  # 2 hours
    smart_record(total_duration=TOTAL_RECORDING_DURATION)
