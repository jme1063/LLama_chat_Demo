from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import subprocess
from fastapi import FastAPI, Request
import subprocess
import json
import uvicorn
import os



app = FastAPI()

# In-memory storage for last uploaded PDF text
uploaded_pdf_text = ""

# PDF upload endpoint
@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    import pdfplumber
    global uploaded_pdf_text
    if not file.filename.lower().endswith('.pdf'):
        return JSONResponse({"error": "Only PDF files are supported."}, status_code=400)
    pdf_bytes = await file.read()
    with open("_temp_upload.pdf", "wb") as f:
        f.write(pdf_bytes)
    try:
        with pdfplumber.open("_temp_upload.pdf") as pdf:
            uploaded_pdf_text = "\n".join(page.extract_text() or '' for page in pdf.pages)
    except Exception as e:
        uploaded_pdf_text = ""
        return JSONResponse({"error": f"Failed to extract PDF text: {e}"}, status_code=500)
    return {"message": "PDF uploaded and text extracted successfully."}

# Serve chat_demo.html at the root URL
@app.get("/")
def serve_chat_demo():
    html_path = os.path.join(os.path.dirname(__file__), "chat_demo.html")
    return FileResponse(html_path, media_type="text/html")

# Chat endpoints
@app.post("/chat")
async def chat_post(request: Request):
    data = await request.json()
    message = data.get("message", "")
    return run_chat(message)

@app.get("/chat")
async def chat_get(message: str = ""):
    return run_chat(message)

def run_chat(message: str):
    # If PDF text is available, include it in the prompt
    context = uploaded_pdf_text.strip()
    if context:
        prompt = f"You are a helpful assistant. The user has uploaded a PDF. Use the following context to answer their question.\n\nPDF Content:\n{context}\n\nUser: {message}\nAssistant:"
    else:
        prompt = f"You are a helpful assistant.\nUser: {message}\nAssistant:"
    process = subprocess.Popen(
        ["ollama", "run", "llama3", prompt],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    output, _ = process.communicate()
    return {"response": output.strip()}
@app.post("/check_syllabus")
async def check_syllabus_post(request: Request):
    data = await request.json()
    syllabus_text = data.get("text", "")
    return run_checker(syllabus_text)

# GET endpoint for browser/testing
@app.get("/check_syllabus")
async def check_syllabus_get(text: str = ""):
    return run_checker(text)

def run_checker(syllabus_text: str):
    prompt = f"""
    You are a syllabus compliance checker.
    Read this syllabus and list any missing required sections:
    (e.g., course title, instructor contact info, grading policy, academic integrity statement)

    Syllabus text:
    {syllabus_text}
    """
    process = subprocess.Popen(
        ["ollama", "run", "llama3", prompt],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    output, _ = process.communicate()
    return {"result": output.strip()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
