from typing import Dict, Any
from ..base.extractor import BaseExtractor
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse

class WebExtractor(BaseExtractor):
    """Extractor for web content"""
    
    def __init__(self):
        pass
    def extract(self, url: str) -> Dict[str, Any]:
        """
        Extract content from a web page
        :param url: URL to extract content from
        :return: Dictionary containing extracted information
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract main content
            content = ''
            for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                content += p.get_text() + '\n'
            
            # Extract metadata
            title = soup.title.string if soup.title else ''
            description = soup.find('meta', attrs={'name': 'description'})
            description = description['content'] if description else ''
            
            # Extract images including those in <picture> tags
            images = []
            
            # Extract images from <picture> tags
            for picture in soup.find_all('picture'):
                # Get sources from <source> tags
                for source in picture.find_all('source'):
                    srcset = source.get('srcset')
                    if srcset:
                        # Split srcset into individual URLs
                        urls = [url.strip().split()[0] for url in srcset.split(',')]
                        images.extend([url for url in urls if not url.startswith('data:')])
                
                # Get img if present
                img = picture.find('img')
                if img:
                    src = img.get('src')
                    if src and not src.startswith('data:'):
                        images.append(src)
            
            # Extract regular images
            for img in soup.find_all('img'):
                if img.find_parent('picture') is None:  # Skip images already processed in picture tags
                    src = img.get('src')
                    if src and not src.startswith('data:'):  # Skip data URIs
                        images.append(src)
            
            return {
                # "content": content.strip(),
                # "metadata": {
                    "title": title,
                    "description": description,
                    "url": url,
                    "domain": urlparse(url).netloc,
                    "images": images,
                    "word_count": len(content.split())
                # }
            }
        except Exception as e:
            return {"error": str(e)}
