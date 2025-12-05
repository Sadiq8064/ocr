from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import tempfile
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import docx2txt

app = FastAPI()


# Helper: write text to .txt file and return FileResponse
def create_txt_response(text: str, filename="extracted_text.txt"):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    tmp.write(text.encode("utf-8"))
    tmp.close()

    return FileResponse(
        path=tmp.name,
        media_type="text/plain",
        filename=filename
    )


# 1. PDF → TEXT → TXT FILE
@app.post("/extract/pdf")
async def extract_pdf(file: UploadFile = File(...)):
    # Save uploaded PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        pdf_path = tmp.name

    pdf = fitz.open(pdf_path)
    text_output = []

    for page_num in range(len(pdf)):
        page = pdf.load_page(page_num)
        pix = page.get_pixmap()  # Render page as image

        img_bytes = pix.tobytes("png")

        # Save to temp PNG
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as img_tmp:
            img_tmp.write(img_bytes)
            img_path = img_tmp.name

        image = Image.open(img_path)

        # OCR
        extracted_text = pytesseract.image_to_string(image)
        text_output.append(f"--- PAGE {page_num+1} ---\n{extracted_text}")

    final_text = "\n".join(text_output)

    return create_txt_response(final_text, "pdf_extracted.txt")


# 2. IMAGE → TEXT → TXT FILE
@app.post("/extract/image")
async def extract_image(file: UploadFile = File(...)):
    # Save image temporarily
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        image_path = tmp.name

    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)

    return create_txt_response(text, "image_extracted.txt")


# 3. DOCX → TEXT → TXT FILE
@app.post("/extract/docx")
async def extract_docx(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(await file.read())
        docx_path = tmp.name

    extracted_text = docx2txt.process(docx_path)

    return create_txt_response(extracted_text, "docx_extracted.txt")
