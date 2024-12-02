import fitz  # PyMuPDF
from google.cloud import vision
from google.oauth2 import service_account
import io
from PIL import Image


# Function to extract text from a PDF using PyMuPDF (for PDFs with selectable text)
def extract_text_from_pdf(pdf_file_path):
    try:
        # Open the PDF file using PyMuPDF
        doc = fitz.open(pdf_file_path)
        text = ""

        # Extract text from each page
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)  # Page is 0-indexed
            text += page.get_text("text")  # Extract text as plain text

        return text
    except Exception as e:
        print(f"An error occurred while extracting text from the PDF: {e}")
        return None


# Function to extract text from an image (using Google Vision API)
def extract_text_from_image(image_path):
    try:
        # Set up credentials for Google Cloud Vision API
        credentials = service_account.Credentials.from_service_account_file(r"C:\Users\User\Downloads\output-results_output-1-to-1.json")
        client = vision.ImageAnnotatorClient(credentials=credentials)

        # Read image into memory
        with open(image_path, "rb") as image_file:
            content = image_file.read()

        image = vision.Image(content=content)  # Directly create the vision.Image object

        # Perform text detection on the image
        response = client.text_detection(image=image)
        texts = response.text_annotations

        if texts:
            return texts[0].description  # Return the full text detected by the API
        else:
            return "No text found."
    except Exception as e:
        print(f"An error occurred while extracting text from the image: {e}")
        return None


# Function to save text to a file
def save_text_to_file(text, output_file_path):
    try:
        with open(output_file_path, "w", encoding="utf-8") as file:
            file.write(text)
        print(f"Text successfully saved to {output_file_path}")
    except Exception as e:
        print(f"An error occurred while saving the text to a file: {e}")


# Main function to orchestrate the extraction and saving to a file
def main():
    pdf_file_path = r"C:\Users\User\Downloads\restaurante.pdf"  # Specify the path to your PDF file
    output_file_path = r"C:\Users\User\Downloads\extracted_text.txt"  # Path to save the extracted text

    # Extract text from PDF (if it contains text)
    extracted_text = extract_text_from_pdf(pdf_file_path)

    if extracted_text:
        print("Extracted text from PDF (direct text extraction):")
        print(extracted_text)
        save_text_to_file(extracted_text, output_file_path)  # Save the text to a file
    else:
        # If no text, extract text from images in the PDF using Google Vision API
        print("No text found in PDF. Attempting to extract text from images using Google Vision API.")

        # You may need to convert PDF pages to images for Google Vision API processing
        # For simplicity, let's assume we convert the first page to an image and send it to the Vision API
        extracted_image_text = extract_text_from_image('path_to_image_from_pdf.jpg')  # Replace with actual image path

        if extracted_image_text:
            print("Extracted text from image (Google Vision API):")
            print(extracted_image_text)
            save_text_to_file(extracted_image_text, output_file_path)  # Save the text to a file
        else:
            print("No text could be extracted from the image.")


if __name__ == "__main__":
    main()
