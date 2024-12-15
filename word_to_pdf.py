from docx import Document
from fpdf import FPDF

def convert_word_to_pdf(file_name):
    try:
        doc = Document(file_name)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for para in doc.paragraphs:
            pdf.multi_cell(0, 10, para.text)
        output_file = file_name.replace('.docx', '.pdf')
        pdf.output(output_file)
        return output_file
    except Exception as e:
        print(f"Error converting Word to PDF: {e}")
        return None
