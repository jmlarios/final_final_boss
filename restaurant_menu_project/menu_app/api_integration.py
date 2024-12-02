import os
from PDFreader import extract_text_from_pdf, extract_text_from_image
from AIreader import get_claude_response
import mysql.connector
from datetime import datetime


def normalize_text(text):
    """
    Normalize Spanish text by removing accents.
    """
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))


def insert_into_database(data):
    """
    Insert structured data into the MySQL database.
    """
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Mine-craft1",
            database="restaurantmenusystem"
        )
        cursor = conn.cursor()

        for restaurant in data.get("Restaurant", []):
            cursor.execute(
                "INSERT INTO Restaurant (restaurant_id, name, location) VALUES (%s, %s, %s)",
                restaurant
            )

        # Repeat similar steps for Menu, MenuSection, MenuItem, and DietaryRestriction

        conn.commit()
        print("Data inserted successfully.")
    except Exception as e:
        print(f"Error inserting into database: {e}")
    finally:
        if conn.is_connected():
            conn.close()


def main():
    pdf_path = r"C:\Users\User\Downloads\restaurante_2.pdf"
    credentials_path = r"C:\Users\User\Downloads\database-443218-8d1a699e81ad.json"
    api_key = "your-anthropic-api-key"

    pdf_text = extract_text_from_pdf(pdf_path)
    if not pdf_text:
        print("Failed to extract text from PDF. Trying image OCR.")
        pdf_text = extract_text_from_image("path_to_image.jpg", credentials_path)

    if not pdf_text:
        print("No text could be extracted.")
        return

    print("Extracted text from PDF:")
    print(pdf_text)

    structured_data = get_claude_response(api_key, pdf_text)
    if structured_data.get("error"):
        print("Error in structured data:")
        print(structured_data["error"])
        return

    structured_data = normalize_text(structured_data)
    insert_into_database(structured_data)


if __name__ == "__main__":
    main()
