'''
from docx_to_pdf import *
from excel_to_pdf import *
from image_to_pdf import *
import streamlit as st


st.header("Convert files to PDF")

uploaded_file = st.file_uploader("Upload your file (Docx or Excel)", accept_multiple_files=False)

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".docx") or uploaded_file.name.endswith(".doc"):
            pdf_file = convert_docx_to_pdf(uploaded_file)
            st.title("")
            st.download_button(label="Download PDF", data=pdf_file, file_name="output.pdf", mime="application/pdf")

        elif uploaded_file.name.endswith(".xlsx") or uploaded_file.name.endswith(".xls"):
            pdf_file = convert_excel_to_pdf(uploaded_file)
            st.title("")
            with open(pdf_file, "rb") as pdf:
                pdf_data = pdf.read()
            st.download_button(label="Download PDF", data=pdf_data, file_name="output.pdf", mime="application/pdf")

        elif uploaded_file.name.endswith(".jpg") or uploaded_file.name.endswith(".jpeg") or uploaded_file.name.endswith(".png"):
            pdf_file, filename = image_to_pdf(uploaded_file)
            st.title("")
            st.download_button(label="Download PDF", data=pdf_file, file_name=filename, mime="application/pdf")
        else:
            st.warning("Currently supporting only Docx, Excel, and Image files, please try again.")
    except Exception as error:
        st.error(error)
'''


from docx_to_pdf import *
from excel_to_pdf import *
from image_to_pdf import *
import streamlit as st
import os
from datetime import datetime
import unicodedata


def create_safe_path(base_directory, filename):
    # Normalize the filename to handle Unicode characters
    filename = unicodedata.normalize('NFC', filename)

    # Replace any characters that might cause path issues
    filename = filename.replace('/', '_').replace('\\', '_')

    # Create the full path
    full_path = os.path.join(base_directory, filename)

    return full_path

# Specify the download directory (you can change this to your preferred path)
DOWNLOAD_DIRECTORY = os.path.join(os.path.expanduser('~'), 'Downloads', f'PDF receipts of year {str(datetime.now().year)}')

st.header("Convert files to PDF")

uploaded_file = st.file_uploader("Upload your file (Docx, Excel or Image)", accept_multiple_files=False)

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".docx") or uploaded_file.name.endswith(".doc"):
            pdf_file = convert_docx_to_pdf(uploaded_file)
            st.title("")
            st.download_button(label="Download PDF", data=pdf_file, file_name="output.pdf", mime="application/pdf")

        elif uploaded_file.name.endswith(".xlsx") or uploaded_file.name.endswith(".xls"):
            pdf_file = convert_excel_to_pdf(uploaded_file)
            st.title("")
            with open(pdf_file, "rb") as pdf:
                pdf_data = pdf.read()
            st.download_button(label="Download PDF", data=pdf_data, file_name="output.pdf", mime="application/pdf")

        if uploaded_file.name.endswith((".jpg", ".jpeg", ".png")):
            if not os.path.exists(DOWNLOAD_DIRECTORY):
                os.makedirs(DOWNLOAD_DIRECTORY)

            pdf_file, original_filename = image_to_pdf(uploaded_file)

            try:
                # If pdf_file is a BytesIO object, convert it to bytes
                if hasattr(pdf_file, 'getvalue'):
                    pdf_bytes = pdf_file.getvalue()
                elif hasattr(pdf_file, 'read'):
                    pdf_bytes = pdf_file.read()
                else:
                    pdf_bytes = pdf_file

                # Ensure the filename ends with .pdf
                if not original_filename.lower().endswith('.pdf'):
                    original_filename += '.pdf'

                output_path = create_safe_path(DOWNLOAD_DIRECTORY, original_filename)

                with open(output_path, 'wb') as f:
                    f.write(pdf_bytes)

                st.success(f"file downloaded successfully, you can find in in {DOWNLOAD_DIRECTORY}")

            except Exception as error:
                st.error(f"Error saving file: {error}")
                import traceback

                st.error(traceback.format_exc())
        else:
            st.warning("Currently supporting only Docx, Excel, and Image files, please try again.")
    except Exception as error:
        st.error(error)