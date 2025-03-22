import streamlit as st
import io
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY


def convert_docx_to_pdf(docx_file):
    try:
        # Read the uploaded DOCX file
        doc = Document(docx_file)

        # Create an in-memory PDF file
        pdf_buffer = io.BytesIO()
        pdf = SimpleDocTemplate(pdf_buffer, pagesize=letter)

        # Set up styles
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

        # Create content for the PDF
        pdf_content = []

        # Extract and convert text from paragraphs
        for para in doc.paragraphs:
            if para.text:
                # Determine style based on paragraph properties
                if para.style.name.startswith('Heading1') or para.style.name.startswith('Title'):
                    style = styles['Heading1']
                elif para.style.name.startswith('Heading2'):
                    style = styles['Heading2']
                elif para.style.name.startswith('Heading'):
                    style = styles['Heading3']
                else:
                    style = styles['Normal']

                # Add the paragraph to the PDF content
                pdf_content.append(Paragraph(para.text, style))
                pdf_content.append(Spacer(1, 12))  # Add some space after each paragraph

        # Build the PDF
        pdf.build(pdf_content)

        # Get the PDF data
        pdf_data = pdf_buffer.getvalue()
        pdf_buffer.close()

        return pdf_data

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None