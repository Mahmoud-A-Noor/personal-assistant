from typing import Dict, Any
from ..base.extractor import BaseExtractor
import phonenumbers
import email_validator
import re

class ContactExtractor(BaseExtractor):
    """Extractor for contact information from text"""
    
    def __init__(self):
        pass
    
    def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract contact information from text
        :param text: Text to extract contact information from
        :return: Dictionary containing extracted contact information
        """
        try:
            # Extract emails
            emails = []
            email_matches = re.finditer(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
            for match in email_matches:
                email = match.group(0)
                try:
                    email_validator.validate_email(email)
                    emails.append(email)
                except:
                    continue
            
            # Extract phone numbers
            phone_numbers = []
            for match in phonenumbers.PhoneNumberMatcher(text, None):
                number = phonenumbers.format_number(
                    match.number,
                    phonenumbers.PhoneNumberFormat.INTERNATIONAL
                )
                phone_numbers.append({
                    "number": number,
                    "type": phonenumbers.number_type(match.number)
                })
            
            # Extract addresses
            addresses = []
            address_patterns = [
                r'\d+\s+\w+\s+(?:\w+\s+)?\w+',  # Simple street address
                r'\d+\s+\w+\s+\w+\s+\w+',  # More complex address
                r'\d+\s+\w+\s+\w+\s+\w+\s+\w+'  # Even more complex address
            ]
            
            for pattern in address_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    address = match.group(0)
                    if not any(a['address'] == address for a in addresses):
                        addresses.append({
                            "address": address,
                            "confidence": "medium"
                        })
            
            return {
                # "content": text,
                # "metadata": {
                    "emails": emails,
                    "phone_numbers": phone_numbers,
                    "addresses": addresses,
                    "total_contacts": len(emails) + len(phone_numbers)
                # }
            }
        except Exception as e:
            return {"error": str(e)}
