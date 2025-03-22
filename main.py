from docx_to_pdf import *
from excel_to_pdf import *
from image_to_pdf import *
import streamlit as st


st.header("Convert files to PDF")

uploaded_file = st.file_uploader("Upload your file (Docx or Excel)", accept_multiple_files=False)

if uploaded_file is not None:
    if uploaded_file.name.endswith(".docx") or uploaded_file.name.endswith(".doc"):
        pdf_file = convert_docx_to_pdf(uploaded_file)
        st.title("")
        st.download_button(label="Download PDF", data=pdf_file, file_name="output.pdf", mime="application/pdf")

    elif uploaded_file.name.endswith(".xlsx") or uploaded_file.name.endswith(".xls"):
        pdf_files = ExcelToPDFConverter.convert_excel_to_pdf(uploaded_file)
        st.title("")
        with open(pdf_files[0], "rb") as pdf:
            pdf_data = pdf.read()
        st.download_button(label="Download PDF", data=pdf_data, file_name="output.pdf", mime="application/pdf")

    elif uploaded_file.name.endswith(".jpg") or uploaded_file.name.endswith(".jpeg") or uploaded_file.name.endswith(".png"):
        pdf_file, filename = image_to_pdf(uploaded_file)
        st.title("")
        st.download_button(label="Download PDF", data=pdf_file, file_name=filename, mime="application/pdf")
