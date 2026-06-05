import os
import json
import argparse
from moviepy.editor import VideoFileClip
import google.generativeai as genai
import yt_dlp

def generate_seo(api_key, topic, part_number):
    print(f"Generating AI SEO for Part {part_number}...")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    I am uploading a YouTube Short about this topic: "{topic}".
    This is Part {part_number} of a longer video.
    Generate a highly engaging, clickbait-style title (under 50 characters, ending with #shorts).
    Generate a 2-sentence description.
    Generate exactly 5 relevant comma-separated tags (no hashtags in the tags list, just words).
    
    Format the output EXACTLY as valid JSON with these keys:
    {{"title": "...", "description": "...", "tags": ["tag1", "tag2"]}}
    """
    
    if not api_key:
        print("No Gemini API key provided. Using fallback SEO...")
        return {
            "title": f"{topic} Part {part_number} #shorts",
            "description": f"Part {part_number} of our series on {topic}. Subscribe for more!",
            "tags": ["shorts", "trending", "viral"]
        }
        
    try:
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        seo_data = json.loads(text)
        return seo_data
    except Exception as e:
        print(f"Failed to parse Gemini response: {e}")
        return {
            "title": f"{topic} Part {part_number} #shorts",
            "description": f"Part {part_number} of our series on {topic}. Subscribe for more!",
            "tags": ["shorts", "trending", "viral"]
        }

def cut_video(input_path, topic, api_key):
    # Remove quotes if user dragged and dropped the file into the terminal
    input_path = input_path.strip('"\'')
    
    if not os.path.exists(input_path):
        print(f"Error: File {input_path} not found.")
        return

    output_dir = 'videos_channel1'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Loading video: {input_path}...")
    video = VideoFileClip(input_path)
    duration = video.duration
    
    clip_length = 59  # 59 seconds for shorts
    
    seo_file = os.path.join(output_dir, 'seo_data.json')
    if os.path.exists(seo_file):
        with open(seo_file, 'r') as f:
            seo_db = json.load(f)
    else:
        seo_db = {}

    part = 1
    # Check what the highest part is already so we don't overwrite
    base_name = os.path.splitext(os.path.basename(input_path))[0].replace(" ", "_")
    
    for start_time in range(0, int(duration), clip_length):
        end_time = min(start_time + clip_length, duration)
        
        # Skip clips shorter than 10 seconds at the end
        if end_time - start_time < 10:
            break
            
        output_filename = f"{base_name}_part_{part}.mp4"
        output_filepath = os.path.join(output_dir, output_filename)
        
        print(f"\n--- Cutting Part {part} ({start_time}s to {end_time}s) ---")
        clip = video.subclip(start_time, end_time)
        clip.write_videofile(output_filepath, codec="libx264", audio_codec="aac")
        
        # Generate SEO
        seo_data = generate_seo(api_key, topic, part)
        seo_db[output_filename] = seo_data
        
        # Save SEO to DB
        with open(seo_file, 'w') as f:
            json.dump(seo_db, f, indent=4)
            
        part += 1

    print("\n✅ All clips cut and SEO generated successfully!")
    video.close()
    
    # Clean up the downloaded long video to save space
    try:
        os.remove(input_path)
        print(f"Cleaned up temporary file: {input_path}")
    except Exception as e:
        print(f"Could not remove temp file: {e}")

def download_youtube_video(url):
    print(f"Downloading video from: {url}")
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'temp_downloaded_video.%(ext)s',
        'quiet': False
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        video_title = info_dict.get('title', 'Unknown Topic')
        expected_filename = ydl.prepare_filename(info_dict)
        
    print(f"Successfully downloaded: {expected_filename}")
    return expected_filename, video_title

if __name__ == "__main__":
    print("=== Automated YouTube Shorts Cutter & SEO ===")
    
    # HARDCODED FOR AUTOMATION
    youtube_url = "https://www.youtube.com/watch?v=uCg9D5IOFx8"
    print(f"Auto-fetching video: {youtube_url}")
    
    # Download the video using yt-dlp
    video_path, topic = download_youtube_video(youtube_url)
    
    # Prompt for Gemini API Key if not already saved
    api_key_file = 'gemini_key.txt'
    if os.path.exists(api_key_file):
        with open(api_key_file, 'r') as f:
            api_key = f.read().strip()
    else:
        # Fallback empty string if no key is found, so automation doesn't block!
        api_key = ""
            
    cut_video(video_path, topic, api_key)
