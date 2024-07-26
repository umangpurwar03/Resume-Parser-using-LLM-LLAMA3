from langchain.output_parsers import ResponseSchema, StructuredOutputParser

# Define individual schemas for each resume detail
name_schema = ResponseSchema(
    name="Name",
    description="Extract the full name from the resume text."
)

mailid_schema = ResponseSchema(
    name="Mail ID",
    description="Extract the email ID from the resume text."
)

linkedin_schema = ResponseSchema(
    name="LinkedIn",
    description="Extract the LinkedIn profile URL from the resume text."
)

workexp_schema = ResponseSchema(
    name="Work Experience",
    description="Extract all organization names where the person has worked, along with the number of years or months worked there and the designations held, and output them as a comma-separated Python list."
)

companydetails_schema = ResponseSchema(
    name="Company Details",
    description="Extract all company names and details where the person has worked, and output them as a comma-separated Python list."
)

technical_skills_schema = ResponseSchema(
    name="Technical Skills",
    description="Extract all technical skills mentioned in the resume text and output them as a comma-separated Python list."
)

soft_skills_schema = ResponseSchema(
    name="Soft Skills",
    description="Extract all soft skills mentioned in the resume text and output them as a comma-separated Python list."
)

projects_schema = ResponseSchema(
    name="Projects",
    description="Extract all project titles mentioned in the resume text and output them as a comma-separated Python list."
)

# Combine all schemas into a list
response_schemas = [
    name_schema,
    mailid_schema,
    linkedin_schema,
    workexp_schema,
    companydetails_schema,
    technical_skills_schema,
    soft_skills_schema,
    projects_schema
]

# Create the output parser using the response schemas
output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

# Get the format instructions
format_instructions = output_parser.get_format_instructions()

print(format_instructions)

import os
import csv
import re
import io
import pandas as pd
import json
from groq import Groq

# Path to the output CSV file
csv_file = 'output.csv'

def extract_text_from_docx(docx_path):
    """
    Extracts text from a .docx file.
    """
    try:
        import docx
        doc = docx.Document(docx_path)
        text = [para.text for para in doc.paragraphs]
        return '\n'.join(text)
    except Exception as e:
        raise ValueError(f"Failed to extract text from {docx_path}: {e}")

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a .pdf file.
    """
    try:
        from PyPDF2 import PdfReader
        pdf_text = []
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            for page in reader.pages:
                pdf_text.append(page.extract_text())
        return '\n'.join(pdf_text)
    except Exception as e:
        raise ValueError(f"Failed to extract text from {pdf_path}: {e}")

def extract_text_from_resume(file_path):
    """
    Extracts text from a resume file (.docx or .pdf).
    """
    if file_path.endswith('.docx'):
        return extract_text_from_docx(file_path)
    elif file_path.endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path}")

def ensure_fields(row, fieldnames):
    for field in list(row.keys()):
        if field not in fieldnames:
            del row[field]

def process_resumes(resumes_text):
    all_rows = []
    for filename, text in resumes_text.items():
        prompt_template = f'''
    You are an AI bot designed to act as a professional for parsing resumes. You are given with resume {text} and your job is to extract the following information from the resume:
    1. full name
    2. email id
    3. github portfolio
    4. linkedin id
    5. employment details
    6. technical skills
    7. soft skills
    Give the extracted information in csv format only not other text i want in start and end
    '''
        
        groq_api_key = st.secrets["groq"]["api_key"]
        
        client = Groq(api_key=groq_api_key)

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": prompt_template,
            }
        ],
        temperature=0.4,
        model="llama3-70b-8192",
    )

    response_content = chat_completion.choices[0].message.content
    print(response_content)
    
    # Extract the JSON part from the string
    start_index = response_content.find('{')
    end_index = response_content.rfind('}') + 1
    json_part = response_content[start_index:end_index]
    
    # Parse JSON string
    data = json.loads(json_part)
    
    # Convert the dictionary to a DataFrame
    df = pd.DataFrame([data])
    
    # Write to CSV
    if not os.path.isfile(csv_file):
        # Write header if the file does not exist
        df.to_csv(csv_file, index=False, mode='w')
    else:
        # Append to the file without writing the header
        df.to_csv(csv_file, index=False, mode='a', header=False)
