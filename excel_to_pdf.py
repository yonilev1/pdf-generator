import pandas as pd
import tempfile
import os
import io
from fpdf import FPDF
import matplotlib.pyplot as plt
from PIL import Image
import openpyxl
import re


class PDF(FPDF):
    """
    Extended FPDF class with Unicode support
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Unicode font support
        self.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
        self.add_font('DejaVu', 'B', 'DejaVuSansCondensed-Bold.ttf', uni=True)


class ExcelToPDFConverter:
    @staticmethod
    def clean_text(text):
        """
        Clean text to remove or replace problematic characters
        """
        if not isinstance(text, str):
            text = str(text)

        # Replace characters that might cause issues
        text = re.sub(r'[^\x00-\x7F]+', '?', text)
        return text

    @staticmethod
    def convert_excel_to_pdf(excel_file):
        """
        Static method to convert Excel file to PDF

        Parameters:
        excel_file: The uploaded Excel file

        Returns:
        List of file paths to the generated PDFs
        """
        # Create a temporary directory to store the PDF files
        temp_dir = tempfile.mkdtemp()
        output_paths = []

        try:
            # Get all sheet names from the Excel file
            xls = pd.ExcelFile(excel_file)
            sheet_names = xls.sheet_names

            # Create a PDF file using standard fonts
            pdf_path = os.path.join(temp_dir, "output.pdf")
            pdf = FPDF(orientation='L', unit='mm', format='A4')
            pdf.set_auto_page_break(auto=True, margin=15)

            # Add fonts that support more characters
            pdf.add_font('Arial Unicode', '', 'C:\\Windows\\Fonts\\arial.ttf', uni=True)

            # Process each sheet
            for sheet_name in sheet_names:
                # Add a new page for each sheet
                pdf.add_page()

                # Use ASCII-compatible characters for sheet name
                safe_sheet_name = ExcelToPDFConverter.clean_text(sheet_name)

                # Add sheet name as header
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, f"Sheet: {safe_sheet_name}", ln=True, align='C')
                pdf.ln(5)

                # Read sheet data
                try:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)

                    # Reset font for table
                    pdf.set_font("Arial", size=8)

                    # Calculate column widths - limit to avoid overlaps
                    col_width = min(40, 270 / max(len(df.columns), 1))

                    # Add headers
                    for col in df.columns:
                        col_name = ExcelToPDFConverter.clean_text(str(col)[:20])  # Clean and truncate
                        pdf.cell(col_width, 10, col_name, border=1, align='C')
                    pdf.ln()

                    # Add rows - limit the number to avoid huge PDFs
                    max_rows = min(100, len(df))
                    for i in range(max_rows):
                        for col in df.columns:
                            # Clean the value to ensure it can be encoded in latin-1
                            raw_value = str(df.iloc[i][col]) if i < len(df) else ""
                            value = ExcelToPDFConverter.clean_text(raw_value)

                            # Truncate long values
                            value = value[:20] + '...' if len(value) > 20 else value
                            pdf.cell(col_width, 10, value, border=1)
                        pdf.ln()

                    if len(df) > max_rows:
                        pdf.cell(0, 10, f"... (showing {max_rows} of {len(df)} rows)", ln=True)

                except Exception as e:
                    pdf.set_text_color(255, 0, 0)
                    pdf.cell(0, 10, f"Error processing sheet: {str(e)}", ln=True)
                    pdf.set_text_color(0, 0, 0)

            # Save the PDF
            pdf.output(pdf_path)
            output_paths.append(pdf_path)

            return output_paths

        except Exception as e:
            # In case of error, create a PDF with error message
            pdf_path = os.path.join(temp_dir, "error.pdf")
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, f"Error converting Excel to PDF: {str(e)}", ln=True)
            pdf.output(pdf_path)
            output_paths.append(pdf_path)

            return output_paths


# Alternative implementation using a different approach
class AlternativeExcelToPDFConverter:
    @staticmethod
    def convert_excel_to_pdf(excel_file):
        """
        Alternative static method to convert Excel file to PDF using a simpler approach
        that avoids encoding issues by using byte streams instead of file paths.

        Parameters:
        excel_file: The uploaded Excel file

        Returns:
        List containing a tuple of (pdf_bytes, filename)
        """
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        pdf_bytes = None

        try:
            # Save uploaded file to disk temporarily
            temp_excel_path = os.path.join(temp_dir, "temp_excel_file.xlsx")
            with open(temp_excel_path, "wb") as f:
                f.write(excel_file.getvalue())

            # Read all sheets
            xls = pd.ExcelFile(temp_excel_path)
            sheet_names = xls.sheet_names

            # Convert to CSV first (as an intermediary format)
            csv_paths = []
            for sheet_name in sheet_names:
                df = pd.read_excel(temp_excel_path, sheet_name=sheet_name)
                csv_path = os.path.join(temp_dir, f"{sheet_name}.csv")
                df.to_csv(csv_path, index=False, encoding='utf-8')
                csv_paths.append((sheet_name, csv_path))

            # Create PDF using CSV data - simpler approach with fewer encoding issues
            pdf_buffer = io.BytesIO()
            pdf = FPDF(orientation='L')

            for sheet_name, csv_path in csv_paths:
                # Add a page for each sheet
                pdf.add_page()

                # Add header
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, f"Sheet: {sheet_name}", ln=True, align='C')
                pdf.ln(5)

                # Read CSV
                with open(csv_path, 'r', encoding='utf-8') as csvfile:
                    lines = csvfile.readlines()

                if not lines:
                    pdf.cell(0, 10, "No data in this sheet", ln=True)
                    continue

                # Get headers
                headers = lines[0].strip().split(',')

                # Calculate cell width
                page_width = pdf.w - 20  # margins
                col_width = page_width / len(headers)

                # Add headers
                pdf.set_font('Arial', 'B', 8)
                for header in headers:
                    # Remove quotes that might come from CSV
                    header = header.strip('"')
                    header = header[:15] + '...' if len(header) > 15 else header
                    pdf.cell(col_width, 7, header, border=1)
                pdf.ln()

                # Add data
                pdf.set_font('Arial', '', 8)
                max_rows = min(100, len(lines) - 1)

                for i in range(1, max_rows + 1):
                    if i < len(lines):
                        cells = lines[i].strip().split(',')
                        for cell in cells:
                            # Remove quotes and handle encoding issues
                            cell_text = cell.strip('"')
                            cell_text = cell_text[:15] + '...' if len(cell_text) > 15 else cell_text

                            # Filter out non-ASCII characters if needed
                            cell_text = ''.join(c if ord(c) < 128 else '?' for c in cell_text)

                            pdf.cell(col_width, 6, cell_text, border=1)
                        pdf.ln()

                if len(lines) > max_rows + 1:
                    pdf.cell(0, 10, f"... (showing {max_rows} of {len(lines) - 1} rows)", ln=True)

            # Get PDF as bytes directly, avoiding file output
            pdf_bytes = pdf.output(dest='S').encode('latin-1', errors='replace')
            return [(pdf_bytes, "output.pdf")]

        except Exception as e:
            # Create error PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 10, f"Error: {str(e)}", ln=True)
            pdf_bytes = pdf.output(dest='S').encode('latin-1', errors='replace')
            return [(pdf_bytes, "error.pdf")]

        finally:
            # Clean up temp directory
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)