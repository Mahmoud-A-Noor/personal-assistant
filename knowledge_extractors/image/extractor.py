from typing import Dict, Any, Union, List, Tuple
from ..base.extractor import BaseExtractor
from PIL import Image
from easyocr import Reader
import imagehash
import io

class ImageExtractor(BaseExtractor):
    """Extractor for image files"""
    SUPPORTED_FORMATS = {
        '.jpg': 'JPEG',
        '.jpeg': 'JPEG',
        '.png': 'PNG',
        '.gif': 'GIF',
        '.bmp': 'BMP',
        '.tiff': 'TIFF'
    }
    
    def __init__(self, languages: Union[List[str], str] = None, use_gpu: bool = True):
        """
        Initialize the image extractor
        
        :param languages: List of languages to use for OCR, or 'all' to use all supported languages
                         Default languages are ['en', 'ar']
        :param use_gpu: Whether to use GPU acceleration if available
        """
        
        # Default languages if none specified
        if languages is None:
            languages = ['en', 'ar']
        
        # If 'all' is specified, use all supported languages
        if languages == 'all':
            from easyocr import lang_list
            languages = lang_list()
        
        # Initialize EasyOCR with specified languages
        self.reader = Reader(languages, gpu=use_gpu)
        # Store the languages used
        self.used_languages = languages

    def extract(self, 
                image_source: Union[str, bytes],
                languages: Union[List[str], str] = None,
                use_gpu: bool = None) -> Dict[str, Any]:
        """
        Extract information from an image
        
        :param image_source: Can be file path (str) or bytes
        :param languages: Optional list of languages to use for OCR, or 'all' to use all supported languages
                         Overrides the default languages specified in __init__
        :param use_gpu: Optional parameter to override GPU usage
        :return: Dictionary containing extracted information
        """
        """
        Extract information from an image
        :param image_source: Can be file path (str) or bytes
        :return: Dictionary containing extracted information
        """
        try:
            # Load image and convert to format expected by EasyOCR
            if isinstance(image_source, bytes):
                image = io.BytesIO(image_source)
            else:
                # EasyOCR can handle file paths directly
                image = image_source

            # Convert image to RGB if needed
            if isinstance(image, str):
                image = Image.open(image)
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Extract text using EasyOCR
            # EasyOCR expects either a file path, bytes, or numpy array
            if isinstance(image, str):
                # If it's a file path, use it directly
                results = self.reader.readtext(image)
            else:
                # For bytes or PIL image, convert to numpy array
                import numpy as np
                image_np = np.array(image)
                results = self.reader.readtext(image_np)
            
            # Process OCR results
            ocr_text = "\n".join([text for (_, text, _) in results])
            ocr_boxes = []
            for (box, text, confidence) in results:
                ocr_boxes.append({
                    'text': text,
                    'confidence': float(confidence),
                    'box': {
                        'top_left': box[0],
                        'top_right': box[1],
                        'bottom_right': box[2],
                        'bottom_left': box[3]
                    }
                })
            
            # Extract basic image properties
            properties = {
                "format": image.format,
                "mode": image.mode,
                "size": image.size,
                "width": image.width,
                "height": image.height
            }
            
            # Calculate perceptual hash
            hash_value = str(imagehash.average_hash(image))
            
            return {
                "content": ocr_text.strip(),
                "metadata": {
                    **properties,
                    "text_detected": bool(ocr_text.strip()),
                    "perceptual_hash": hash_value,
                    "aspect_ratio": image.width / image.height
                }
            }
        except Exception as e:
            return {"error": str(e)}
