def detect_file_type(file_name): 
    if file_name.endswith('.docx'):
         return "word" 
    elif file_name.endswith('.xlsx'): 
        return "excel" 
    elif file_name.endswith('.pptx'): 
        return "powerpoint" 
    else: return "unknown"