import os
import ffmpeg
import subprocess

def get_video_info(file_path):
    try:
        probe = ffmpeg.probe(file_path)
        format_info = probe.get('format', {})
        streams = probe.get('streams', [])

        video_stream = next((s for s in streams if s['codec_type'] == 'video'), None)
        audio_stream = next((s for s in streams if s['codec_type'] == 'audio'), None)

        return {
            "filename": os.path.basename(file_path),
            "format": format_info.get('format_name'),
            "duration": float(format_info.get('duration', 0)),
            "size_mb": round(float(format_info.get('size', 0)) / (1024 * 1024), 2),
            "bitrate": int(format_info.get('bit_rate', 0)),
            "width": video_stream.get('width') if video_stream else None,
            "height": video_stream.get('height') if video_stream else None,
            "video_codec": video_stream.get('codec_name') if video_stream else None,
            "audio_codec": audio_stream.get('codec_name') if audio_stream else None,
        }
    except Exception as e:
        return {"error": str(e)}

def compress_video(input_path, output_path, crf=28):
    cmd = [
        "ffmpeg", "-i", input_path,
        "-vcodec", "libx264", "-crf", str(crf),
        "-preset", "fast",
        "-acodec", "aac", "-b:a", "128k",
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def convert_resolution(input_path, output_path, height):
    cmd = [
        "ffmpeg", "-i", input_path,
        "-vf", f"scale=-2:{height}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
