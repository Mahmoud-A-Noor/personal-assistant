import whisper
import tempfile
from typing import Dict, Any, Union
from ..base.extractor import BaseExtractor
import ffmpeg
import os

class AudioExtractor(BaseExtractor):
    """Extractor for audio files using Whisper"""
    
    def __init__(self, model_name: str = "base"):
        """
        Initialize the audio extractor
        
        :param model_name: Whisper model size. Available options:
            - "tiny": Smallest model, fastest but least accurate
            - "tiny.en": English-only version of tiny model
            - "base": Small model, good balance of speed and accuracy
            - "base.en": English-only version of base model
            - "small": Medium model, better accuracy than base
            - "small.en": English-only version of small model
            - "medium": Large model, high accuracy but slower
            - "medium.en": English-only version of medium model
            - "large": Largest model, highest accuracy but slowest
            - "turbo": Optimized model for speed, good accuracy
            
            Model specifications:\n
            Size    | Parameters | English-only | Multilingual | VRAM | Speed\n
            --------------------------------------------------------------\n
            tiny    | 39M        | tiny.en      | tiny         | ~1GB | ~10x\n
            base    | 74M        | base.en      | base         | ~1GB | ~7x\n
            small   | 244M       | small.en     | small        | ~2GB | ~4x\n
            medium  | 769M       | medium.en    | medium       | ~5GB | ~2x\n
            large   | 1550M      | N/A          | large        | ~10GB| 1x\n
            turbo   | 809M       | N/A          | turbo        | ~6GB | ~8x\n
            
            Notes:\n
            - Relative speeds are measured on A100 GPU
            - Real-world speed may vary based on hardware
            - VRAM requirements are approximate
            - English-only models (.en suffix) are faster and more accurate for English audio
            
            Recommended usage:
            - Real-time transcription: use "tiny" or "base"
            - High accuracy: use "large" or "turbo"
            - English only: use "base.en" or "medium.en"
            - Resource constrained: use "tiny" or "tiny.en"
            - High performance: use "turbo"
        """
        self.model = whisper.load_model(model_name)
    
    def extract(self, audio_source: Union[str, bytes]) -> Dict[str, Any]:
        """
        Extract transcription from audio source
        :param audio_source: Can be file path (str) or bytes
        :return: Dictionary containing transcription and metadata
        """
        try:
            return self._extract_impl(audio_source)
        except ValueError as e:
            raise
        except Exception as e:
            raise ValueError(f"Failed to transcribe audio: {str(e)}")

    def _extract_impl(self, source: Union[str, bytes]) -> Dict[str, Any]:
        try:
            # Convert to WAV using ffmpeg
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_file:
                if isinstance(source, str):
                    # Convert file path to WAV
                    ffmpeg.input(source).output(temp_file.name, format='wav').run(overwrite_output=True)
                else:  # bytes
                    # Convert bytes to WAV
                    with tempfile.NamedTemporaryFile(delete=False) as temp_input:
                        temp_input.write(source)
                        ffmpeg.input(temp_input.name).output(temp_file.name, format='wav').run(overwrite_output=True)
                        os.unlink(temp_input.name)

                # Transcribe the WAV file
                result = self.model.transcribe(temp_file.name)

                return {
                    "transcription": result["text"],
                    "language": result["language"],
                    "model_used": str(self.model.device)
                }
        except Exception as e:
            raise ValueError(f"Failed to transcribe audio: {str(e)}")
