from typing import Dict, Any, Union, List
from ..base.extractor import BaseExtractor
from moviepy.video.io.VideoFileClip import VideoFileClip
import numpy as np
import whisper
import tempfile
import os

class VideoExtractor(BaseExtractor):
    """Extractor for video files"""
    SUPPORTED_FORMATS = {
        '.mp4': 'MP4',
        '.avi': 'AVI',
        '.mov': 'MOV',
        '.wmv': 'WMV',
        '.mkv': 'MKV'
    }
    
    def __init__(self, model_type: str = "base"):
        """
        Initialize the video extractor
        :param model_type: Type of Whisper model for audio transcription
        """
        self.model = whisper.load_model(model_type)
    
    def extract(self, video_source: Union[str, bytes]) -> Dict[str, Any]:
        """
        Extract information from video file
        :param video_source: Can be file path (str) or bytes
        :return: Dictionary containing extracted information
        """
        try:
            # Handle bytes input
            if isinstance(video_source, bytes):
                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
                    temp_file.write(video_source)
                    temp_file.flush()
                    video_path = temp_file.name
            else:
                video_path = video_source
            
            # Load video
            video = VideoFileClip(video_path)
            
            # Extract basic video properties
            properties = {
                "duration": video.duration,
                "fps": video.fps,
                "resolution": (video.w, video.h),
                "size": video.size,
                "audio_exist": bool(video.audio)
            }
            
            # Extract audio and transcribe
            if video.audio:
                audio_file = os.path.splitext(video_path)[0] + "_audio.wav"
                video.audio.write_audiofile(audio_file)
                transcription = self._transcribe_audio(audio_file)
                os.remove(audio_file)
            else:
                transcription = {"text": "No audio track found"}
            
            # Extract key frames
            # key_frames = self._extract_key_frames(video)
            
            # Extract color information
            # color_info = self._extract_color_info(video)
            
            return {
                "content": transcription,
                "metadata": {
                    **properties,
                    #"key_frames": key_frames,
                    #"color_info": color_info
                }
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            if isinstance(video_source, bytes):
                os.remove(video_path)
    
    def _transcribe_audio(self, audio_file: str) -> Dict[str, Any]:
        """Transcribe audio using Whisper"""
        result = self.model.transcribe(audio_file)
        return {
            "text": result["text"],
            "language": result["language"],
            # "segments": result["segments"]
        }
    
    def _extract_key_frames(self, video: VideoFileClip) -> List[Dict[str, Any]]:
        """Extract key frames from video"""
        key_frames = []
        # Extract frames at 5% intervals
        for i in range(0, 100, 5):
            time = (video.duration * i) / 100
            frame = video.get_frame(time)
            key_frames.append({
                "time": time,
                "resolution": frame.shape[:2],
                "color_mean": np.mean(frame, axis=(0, 1)).tolist()
            })
        return key_frames
    
    def _extract_color_info(self, video: VideoFileClip) -> Dict[str, Any]:
        """Extract color information from video"""
        # Get a sample frame
        frame = video.get_frame(video.duration / 2)
        
        # Calculate color statistics
        color_stats = {
            "mean": np.mean(frame, axis=(0, 1)).tolist(),
            "std": np.std(frame, axis=(0, 1)).tolist(),
            "min": np.min(frame, axis=(0, 1)).tolist(),
            "max": np.max(frame, axis=(0, 1)).tolist()
        }
        
        return color_stats
