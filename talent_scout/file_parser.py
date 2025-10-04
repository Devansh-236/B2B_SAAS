from pdf2image import convert_from_path
import pytesseract
from prompts import create_resume_parsing_prompt
import json
import os
import re
from dotenv import load_dotenv
from google import genai

load_dotenv()

def _secure_pdf_to_text(file_path: str) -> str:
    try:
        images = convert_from_path(file_path, dpi=300)
        full_text = ""
        for image in images:
            text = pytesseract.image_to_string(image, lang='eng')
            full_text += text + "\n\n"
        return full_text
    except Exception as e:
        print(f"  - Error in OCR process for {os.path.basename(file_path)}: {e}")
        return ""

def _clean_filename(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r'\s+', '_', name)
    name = re.sub(r'[^\w-]', '', name)
    return name if name else "unknown_candidate"

def process_resumes_to_json(
    resume_pdf_paths: list, 
    output_directory: str, 
    gemini_client
) -> list:
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        print(f"Created output directory: {output_directory}")

    processed_json_paths = []

    for pdf_path in resume_pdf_paths:
        base_filename = os.path.basename(pdf_path)
        print(f"Processing resume: {base_filename}")
        
        raw_text = _secure_pdf_to_text(pdf_path)
        if not raw_text or not raw_text.strip():
            print(f"  - Failed to extract any text from {base_filename}. Skipping.")
            continue

        try:
            prompt = create_resume_parsing_prompt(raw_text)
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            cleaned_text = response.text.strip().replace('```json', '').replace('```', '').strip()
            structured_data = json.loads(cleaned_text)
        except Exception as e:
            print(f"  - LLM parsing failed for {base_filename}: {e}")
            continue

        candidate_name = structured_data.get("name", "unknown")
        output_filename = f"{_clean_filename(candidate_name)}_{os.path.splitext(base_filename)[0]}.json"
        output_path = os.path.join(output_directory, output_filename)
        
        try:
            with open(output_path, 'w') as f:
                json.dump(structured_data, f, indent=4)
            print(f"  - Successfully created JSON file: {output_filename}")
            processed_json_paths.append(output_path)
        except IOError as e:
            print(f"  - Could not write to file {output_path}: {e}")

    return processed_json_paths

if __name__ == "__main__":
    resume_folder = "resume_files"
    output_folder = "output_files"
    api_key = os.getenv("GEMINI_API_KEY")

    resume_pdf_paths = [
        os.path.join(resume_folder, f)
        for f in os.listdir(resume_folder)
        if f.lower().endswith(".pdf")
    ]

    # Client-style Gemini setup
    client = genai.Client(api_key=api_key)

    processed_files = process_resumes_to_json(resume_pdf_paths, output_folder, client)
    print("Processed files:")
    for f in processed_files:
        print(f)