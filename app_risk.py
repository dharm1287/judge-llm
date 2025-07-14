from fastapi import FastAPI, UploadFile, File, HTTPException
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from docx import Document
import fitz  # PyMuPDF
import os
from dotenv import load_dotenv
import json
load_dotenv()
app = FastAPI()

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = os.getenv('OPEN_AI_API_KEY')

# Define prompt for risk detection and RMF mapping
prompt_template = PromptTemplate(
    input_variables=["doc_content"],
    template="""
You are a risk analysis engine for scope documents. Given the following text, do two things:
1. List at least 4 types of risks present in the content (e.g., bias, PII, fairness, data leakage).
2. Map any tools, frameworks, or processes mentioned in the text to the relevant NIST RMF function: Identify, Protect, Detect, Respond, or Recover.

Document:
\"\"\"
{doc_content}
\"\"\"

Respond in this JSON format:
{{
  "risks": ["risk1", "risk2", ...],
  "rmf_mapping": {{
    "tool1": "RMF function",
    ...
  }}
}}
"""
)

# LangChain model
llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_text_from_docx(file_bytes: bytes) -> str:
    with open("temp.docx", "wb") as f:
        f.write(file_bytes)
    doc = Document("temp.docx")
    text = "\n".join([para.text for para in doc.paragraphs])
    os.remove("temp.docx")
    return text


@app.post("/analyze-scope/")
async def analyze_scope(file: UploadFile = File(...)):
    contents = await file.read()
    content_type = file.content_type
    print(f"Received file with content type: {content_type}")
    # Handle based on file type
    if content_type == "application/pdf":
        text = extract_text_from_pdf(contents)
    elif content_type in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword"
    ]:
        text = extract_text_from_docx(contents)
    elif content_type == "text/plain":
        text = contents.decode("utf-8")  # Only decode for plain text
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a PDF, DOCX, or TXT file.")

    # Format prompt with document content
    prompt = prompt_template.format(doc_content=text)
    raw_response = llm.predict(prompt)

    try:
        response_json = json.loads(raw_response)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="LLM response is not valid JSON. Try with simpler or smaller document.")

    return response_json

