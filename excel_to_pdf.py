import pandas as pd
from fpdf import FPDF


def convert_excel_to_pdf(excel_file):
    """Convert Excel file to PDF with proper table formatting"""
    # Create a temporary file for the PDF output
    output_pdf = "output.pdf"

    # Read the Excel file using pandas
    df = pd.read_excel(excel_file)

    # Initialize PDF
    pdf = FPDF(orientation='L', unit='mm', format='A4')  # Landscape orientation for wider tables
    pdf.add_page()

    # Add title
    pdf.set_font(family='Arial', style='B', size=16)
    pdf.cell(0, 10, f"Data from {excel_file.name}", ln=True, align='C')
    pdf.ln(5)

    # Get column names
    columns = df.columns.tolist()

    # Calculate dynamic column width (ensure it fits the page)
    page_width = pdf.w - 20  # 10mm margins on each side
    col_width = page_width / len(columns)

    # Set up the table header
    pdf.set_font(family="Arial", style='B', size=10)
    pdf.set_fill_color(230, 230, 230)  # Light grey background
    pdf.set_text_color(0, 0, 0)  # Black text

    # Print column headers
    for col in columns:
        pdf.cell(col_width, 10, str(col), border=1, fill=True)
    pdf.ln()

    # Print rows
    pdf.set_font(family="Arial", size=10)
    pdf.set_text_color(80, 80, 80)

    for index, row in df.iterrows():
        for col in columns:
            cell_value = str(row[col])
            # Truncate long text to fit in cell
            if len(cell_value) > 25:
                cell_value = cell_value[:22] + "..."
            pdf.cell(col_width, 10, cell_value, border=1)
        pdf.ln()

    # Save the PDF
    pdf.output(output_pdf)
    return output_pdf