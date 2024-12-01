import fitz  # PyMuPDF
import json
import re
import time
from typing import Dict, Any
import anthropic
from django.conf import settings

class ClaudeError(Exception):
    """Custom exception for Anthropic API related errors"""
    pass

def parse_pdf(pdf_file_path: str) -> str:
    """
    Extract text from a PDF file using PyMuPDF.
    """
    try:
        doc = fitz.open(pdf_file_path)
        pdf_text = ""
        for page in doc:
            pdf_text += page.get_text("text")
        doc.close()  # Properly close the document
        return pdf_text.strip()
    except Exception as e:
        raise ClaudeError(f"Failed to extract text from PDF: {str(e)}")

def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Attempt to extract JSON from text using multiple methods
    """
    # Try standard JSON parsing first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON-like content between { }
        json_match = re.search(r'\{.*?\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # If all else fails, create a basic structure
        return {
            "restaurant_name": "Unknown Restaurant",
            "restaurant_location": "Unknown Location",
            "menu_sections": [],
            "raw_text": text
        }

def get_claude_response(pdf_text: str, max_retries: int = 3) -> Dict[str, Any]:
    """
    Get response from Claude API with retry mechanism and error handling.
    """
    # Verify API key
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
    if not api_key:
        raise ClaudeError("Anthropic API key is not configured in settings")

    for attempt in range(max_retries):
        try:
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                system="You are a menu parsing assistant. Extract menu information into structured JSON data.",
                messages=[
                    {
                        "role": "user",
                        "content": f"""Carefully extract menu information from this text and return a structured JSON:

{pdf_text}

Required JSON format:
{{
    "restaurant_name": "Name of Restaurant",
    "restaurant_location": "Location",
    "menu_sections": [
        {{
            "section_name": "Section Name",
            "items": [
                {{
                    "name": "Item Name",
                    "price": 0.00,
                    "description": "Item Description",
                    "dietary_restriction": "Optional Dietary Info"
                }}
            ]
        }}
    ]
}}
"""
                    }
                ]
            )
            
            # Extract content from Claude's response
            content = response.content[0].text
            
            # Extract and parse JSON
            return extract_json_from_text(content)
        
        except anthropic.APIError as e:
            if e.status_code == 529 and attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise ClaudeError(f"Claude API error: {str(e)}")
        except Exception as e:
            raise ClaudeError(f"Failed to communicate with Anthropic API: {str(e)}")

def process_menu_pdf(pdf_file_path: str) -> Dict[str, Any]:
    """
    Process the menu PDF and return structured data.
    """
    try:
        # Extract text from PDF
        pdf_text = parse_pdf(pdf_file_path)
        
        if not pdf_text:
            raise ClaudeError("No text could be extracted from the PDF")

        # Get and return the structured data
        return get_claude_response(pdf_text)
        
    except Exception as e:
        raise ClaudeError(f"Menu processing failed: {str(e)}")