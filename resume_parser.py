import csv
import io
import zipfile
import streamlit as st
from groq import Groq

def extract_text_from_docx(docx_file):
    try:
        import docx
        doc = docx.Document(docx_file)
        text = [para.text for para in doc.paragraphs]
        return '\n'.join(text)
    except Exception as e:
        raise ValueError(f"Failed to extract text from .docx: {e}")

def extract_text_from_pdf(pdf_file):
    try:
        from PyPDF2 import PdfReader
        pdf_text = []
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            pdf_text.append(page.extract_text())
        return '\n'.join(pdf_text)
    except Exception as e:
        raise ValueError(f"Failed to extract text from .pdf: {e}")

def extract_text_from_resume(file):
    if file.name.endswith('.docx'):
        return extract_text_from_docx(file)
    elif file.name.endswith('.pdf'):
        return extract_text_from_pdf(file)
    else:
        raise ValueError(f"Unsupported file format: {file.name}")

def ensure_fields(row, fieldnames):
    for field in list(row.keys()):
        if field not in fieldnames:
            del row[field]

def process_resumes(resumes_text):
    all_rows = []
    for filename, text in resumes_text.items():
        prompt_template = f'''
        You are an AI bot designed to act as a professional for parsing resumes.
        You are given with resume and your job is to extract the following information from the resume in csv just that dont give additional text in the begining and end just this info:
        1. full name
        2. email id
        3. github portfolio
        4. linkedin id
        5. employment details
        6. technical skills
        7. soft skills
        Give the extracted information in csv format only
        and this is resume{text} and dont add additional text in begining and end just extract csv and give complete information i dont want such line also
        Here is the extracted information in CSV format:
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
        response_content
        data_io = io.StringIO(response_content.strip())
        reader = csv.DictReader(data_io, delimiter=',')
        rows = list(reader)
        for row in rows:
            ensure_fields(row, ["Full Name", "Email ID", "Github Portfolio", "LinkedIn ID", "Employment Details", "Technical Skills", "Soft Skills"])
        all_rows.extend(rows)

    csv_file = 'combined_employee_data.csv'
    with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["Full Name", "Email ID", "Github Portfolio", "LinkedIn ID", "Employment Details", "Technical Skills", "Soft Skills"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    return csv_file, all_rows

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

    uploaded_files = st.sidebar.file_uploader("Upload individual resumes (.docx or .pdf), multiple resumes, or a zip folder containing resumes.", type=["pdf", "docx", "zip"], accept_multiple_files=True)
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

            csv_file, all_rows = process_resumes(resumes_text)

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
