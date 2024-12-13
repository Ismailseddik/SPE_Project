import pandas as pd

def convert_excel_to_pdf(file_name):
    try:
        data = pd.read_excel(file_name)
        output_file = file_name.replace('.xlsx', '.pdf')
        data.to_csv(output_file, index=False)
        return output_file
    except Exception as e:
        print(f"Error converting Excel to PDF: {e}")
        return None
