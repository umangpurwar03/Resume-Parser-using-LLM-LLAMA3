import streamlit as st
import pandas as pd
import zipfile
import io
import json
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from groq import Groq
# import win32com.client
import time

# Define individual schemas for each resume detail
name_schema = ResponseSchema(
    name="Name",
    description="Extract the full name from the resume text."
)

mailid_schema = ResponseSchema(
    name="Mail ID",
    description="Extract the email ID from the resume text."
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

# New schemas for educational details, languages spoken, and presence of specific terms
education_schema = ResponseSchema(
    name="Education",
    description="Extract all educational qualifications mentioned in the resume text, including degrees, institutions, and years attended."
)

languages_schema = ResponseSchema(
    name="Languages Spoken",
    description="Extract all languages spoken by the person mentioned in the resume text."
)

specific_terms_schema = ResponseSchema(
    name="Specific Terms",
    description="Check if any of the specified terms are present in the resume and list their headings if found."
)

# Combine all schemas into a list
response_schemas = [
    name_schema,
    mailid_schema,
    workexp_schema,
    companydetails_schema,
    technical_skills_schema,
    soft_skills_schema,
    projects_schema,
    education_schema,
    languages_schema,
    specific_terms_schema  # Add new schema
]

# Create the output parser using the response schemas
output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

# Get the format instructions
format_instructions = output_parser.get_format_instructions()

# List of specific terms to check for
specific_terms = [
    "Credit", "Derivatives", "Insurance Linked Securities", "Long/Short equity",
    "Private Equity", "Crypto / Digital Assets", "Real Estate", "Venture Capital",
    "Fund Investments (Fund of Funds)", "Hedge Funds",
    "Private Funds", "Fund of Funds", "SOC Reports", "Management Companies",
    "Financial Corporate Service Providers", "AML", "Public Companies (ICFR engagements)",
    "IFRS", "US GAAP", "Retail Banks", "Private Banks", "Trust Companies",
    "Captive insurance", "Non public commercial carriers", "Public companies",
    "Life insurance", "Property and casualty insurance"
]

def extract_text_from_docx(docx_file):
    import docx
    doc = docx.Document(io.BytesIO(docx_file.read()))
    text = [para.text for para in doc.paragraphs]
    return '\n'.join(text)

# def extract_text_from_doc(doc_path):
#     word = win32com.client.Dispatch("Word.Application")
#     doc = word.Documents.Open(doc_path)
#     text = doc.Content.Text
#     doc.Close(False)
#     word.Quit()
#     return text

def extract_text_from_pdf(pdf_file):
    from PyPDF2 import PdfReader
    pdf_text = []
    reader = PdfReader(io.BytesIO(pdf_file.read()))
    for page in reader.pages:
        pdf_text.append(page.extract_text())
    return '\n'.join(pdf_text)

def extract_text_from_resume(file):
    if file.name.endswith('.docx'):
        return extract_text_from_docx(file)
    # elif file.name.endswith('.doc'):
    #     return extract_text_from_doc(file)
    elif file.name.endswith('.pdf'):
        return extract_text_from_pdf(file)
    else:
        raise ValueError(f"Unsupported file format: {file.name}")

def process_resumes(resumes_text):
    all_rows = []
    csv_file = 'combined_employee_data.csv'
    for filename, text in resumes_text.items():
        prompt_template = f'''
        You are an AI bot designed to act as a professional for parsing resumes.
        You are given a resume, and your job is to extract the following information from it without adding any additional text:
        1. Full name
        2. Email ID
        3. Employment details
        4. Technical skills
        5. Soft skills
        6. Projects
        7. Education
        8. Languages Spoken
        9. Specific Terms
        Check if any of the following terms are present or similar in the resume and list their headings if found: {', '.join(specific_terms)}
        Give the extracted information in the following format: {format_instructions}

        Resume:
        {text}
        '''
        api_key = st.secrets["groq"]["api_key"]
        # api_key="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"
        client = Groq(api_key=api_key)

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
        response_content 
        start_index = response_content.find('{')
        end_index = response_content.rfind('}') + 1
        # try:
        json_part = response_content[start_index:end_index]
        
        try:
            if json_part.startswith('{') and json_part.endswith('}'):
                data = json.loads(json_part)
                df = pd.DataFrame([data])
                all_rows.append(df)
            else:
                pass
                # st.error("Extracted JSON part is not valid.")
        except json.JSONDecodeError as e:
            st.error(f"Failed to decode JSON: {e}")

        # Wait for 10 seconds before processing the next resume
        time.sleep(10)
    try:
        result_df = pd.concat(all_rows, ignore_index=True)
        result_df.to_csv(csv_file, index=False)
        return csv_file, result_df
    except:
        st.error(f"resume parsing got error")

def main():
    st.title("Resume Parser")
    st.markdown("""
    <style>
        .main {
            background-color: #FFFFFF;
            padding: 10px;
        }
        .stButton button {
            background-color: #4CAF50;
            color: white;
            padding: 15px 32px;
            text-align: center;
            font-size: 16px;
            margin: 2px 2px;
            cursor: pointer;
            border-radius: 12px;
            width: 100%;
        }
        .stFileUploader {
            margin-bottom: 20px;
        }
    </style>
    """, unsafe_allow_html=True)

    uploaded_files = st.sidebar.file_uploader(
        "Upload individual resumes (.docx or .pdf ), multiple resumes, or a zip folder containing resumes.",
        type=["pdf", "docx", "zip"], 
        accept_multiple_files=True
    )

    if uploaded_files:
        process_button = st.sidebar.button("Process Resumes")
        if process_button:
            resumes_text = {}
            for file in uploaded_files:
                if file.name.endswith('.zip'):
                    with zipfile.ZipFile(file, 'r') as zip_ref:
                        for zip_info in zip_ref.infolist():
                            if zip_info.filename.endswith(('.docx', '.pdf')):
                                with zip_ref.open(zip_info) as extracted_file:
                                    text = extract_text_from_resume(extracted_file)
                                    resumes_text[zip_info.filename] = text
                else:
                    text = extract_text_from_resume(file)
                    resumes_text[file.name] = text
            try:
                csv_file, all_rows = process_resumes(resumes_text)
            except:
                st.error(f"resume parsing got error")

            st.write("### Extracted Information")
            st.dataframe(all_rows)

            st.download_button(
                label="Download CSV",
                data=open(csv_file, 'rb').read(),
                file_name='combined_employee_data.csv',
                mime='text/csv'
            )

if __name__ == "__main__":
    main()
