import shutil

async def save_upload_file(upload_file, destination):
    with open(destination, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

def parse_pdf_to_text(pdf_path):
    # Dummy implementation, replace with your PDF parser
    return "Extracted text from PDF"