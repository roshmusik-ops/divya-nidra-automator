import os
import json
import random
import yt_dlp
from moviepy.editor import VideoFileClip
import moviepy.video.fx.all as vfx

def fetch_random_video(channel_url):
    print(f"Fetching videos from channel: {channel_url}")
    ydl_opts = {
        'extract_flat': True,
        'quiet': True
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)
        
    entries = info.get('entries', [])
    if not entries:
        print("No videos found in channel.")
        return None
        
    # Pick a random video
    selected = random.choice(entries)
    print(f"Selected random video: {selected['title']}")
    return selected['url'], selected['title']

def download_video(video_url):
    print(f"Downloading video: {video_url}")
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'temp_daily_download.%(ext)s',
        'quiet': False
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=True)
        filename = ydl.prepare_filename(info_dict)
        
    return filename

def cut_random_segment(input_path, title, source_url):
    if not os.path.exists(input_path):
        print("Error: Downloaded video not found.")
        return

    output_dir = 'videos_channel1'
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Loading video into moviepy: {input_path}")
    video = VideoFileClip(input_path)
    duration = int(video.duration)
    
    clip_length = 30
    
    if duration <= clip_length:
        start_time = 0
        end_time = duration
    else:
        # Pick a random 1-minute window
        start_time = random.randint(0, duration - clip_length - 5) # Leave a 5s buffer
        end_time = start_time + clip_length
        
    print(f"Slicing random segment from {start_time}s to {end_time}s")
    
    base_name = "daily_random_short"
    output_filename = f"{base_name}.mp4"
    output_filepath = os.path.join(output_dir, output_filename)
    
    clip = video.subclip(start_time, end_time)
    
    # Crop to 9:16 aspect ratio (Shorts vertical format)
    w, h = clip.size
    target_ratio = 9 / 16
    if w / h > target_ratio:
        new_w = int(h * target_ratio)
        clip = clip.fx(vfx.crop, width=new_w, height=h, x_center=w/2, y_center=h/2)
    else:
        new_h = int(w / target_ratio)
        clip = clip.fx(vfx.crop, width=w, height=new_h, x_center=w/2, y_center=h/2)

    clip.write_videofile(output_filepath, codec="libx264", audio_codec="aac")
    
    # Save SEO
    seo_file = os.path.join(output_dir, 'seo_data.json')
    seo_db = {}
    if os.path.exists(seo_file):
        with open(seo_file, 'r') as f:
            seo_db = json.load(f)
            
    # Clean title for generic use
    clean_title = title[:40] if len(title) > 40 else title
    
    seo_db[output_filename] = {
        "title": f"{clean_title} #shorts",
        "description": f"A peaceful moment from our channel. Find your calm here: {source_url} #meditation #sleep #relax",
        "tags": ["shorts", "meditation", "sleep", "relax", "peace", "divyanidra"]
    }
    
    with open(seo_file, 'w') as f:
        json.dump(seo_db, f, indent=4)
        
    video.close()
    
    # Cleanup temp file
    try:
        os.remove(input_path)
        print(f"Cleaned up temporary file: {input_path}")
    except:
        pass

if __name__ == "__main__":
    print("=== Daily Cloud Automation ===")
    channel_url = "https://www.youtube.com/@divyanidraofficial/videos"
    
    video_url, title = fetch_random_video(channel_url)
    if video_url:
        filepath = download_video(video_url)
        cut_random_segment(filepath, title, video_url)
        print("Daily Short generated and ready for upload!")
