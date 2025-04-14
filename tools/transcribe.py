import whisper
import tempfile
from typing import List, Union
from pydantic_ai import Tool

class AudioTranscribeTool:
    def __init__(self, model_size="base"):
        """
            Initialize the transcriber with a Whisper model
            :param model_size: Size of Whisper model (tiny, base, small, medium, large)
            default value is "base"
        """
        self.model = whisper.load_model(model_size)

    def transcribe(self, audio_source: Union[str, bytes]) -> str:
        """
        Universal transcription method that handles different input types
        :param audio_source: Can be file path (str) or bytes
        """
        if isinstance(audio_source, bytes):
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as temp_file:
                temp_file.write(audio_source)
                temp_file.flush()
                return self.model.transcribe(temp_file.name)["text"]
        elif isinstance(audio_source, str):
            return self.model.transcribe(audio_source)["text"]
        else:
            raise ValueError("Unsupported audio source type")

def get_transcribe_tools() -> List[Tool]:
    """Creates audio transcription tools"""
    transcriber = AudioTranscribeTool()
    
    return [
        Tool(
            transcriber.transcribe,
            name="transcribe_audio",
            description="Transcribe audio from file path or bytes"
        )
    ]
