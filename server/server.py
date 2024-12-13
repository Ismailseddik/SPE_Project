import socket
import os
from threading import Thread
from file_type_detection import detect_file_type
from word_to_pdf import convert_word_to_pdf
from excel_to_pdf import convert_excel_to_pdf
from ppt_to_pdf import convert_ppt_to_pdf
import logging
import time
import uuid

# Configure the logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)
performance_logger = logging.getLogger("PerformanceLogger")
performance_logger.addHandler(logging.FileHandler("performance.log"))

HOST = '127.0.0.1'
PORT = 65432

CONVERTED_FILES_DIR = "converted_files"
os.makedirs(CONVERTED_FILES_DIR, exist_ok=True)


def generate_session_id(addr):
    """Generate a unique session ID for each client."""
    return f"{addr[0]}_{addr[1]}_{uuid.uuid4()}"


def receive_metadata(conn):
    """Receive and validate metadata."""
    metadata = conn.recv(1024).decode('utf-8', errors='ignore').strip()
    if ";" not in metadata:
        raise ValueError(f"Invalid metadata format: {metadata}")
    file_name, file_size = metadata.split(';')
    try:
        file_size = int(file_size)
    except ValueError:
        raise ValueError(f"Invalid file size in metadata: {file_size}")
    return file_name, file_size


def receive_file(conn, file_name, file_size):
    """Receive the file from the client."""
    with open(file_name, 'wb') as f:
        received = 0
        while received < file_size:
            data = conn.recv(4096)  # Increased buffer size for better performance
            if not data:
                break
            f.write(data)
            received += len(data)
            logging.debug(f"Received {len(data)} bytes. Total received: {received} bytes.")
    if received != file_size:
        raise IOError(f"Incomplete file transfer. Expected {file_size}, received {received}.")
    return os.path.getsize(file_name)


def detect_and_convert(file_name, session_id):
    """Detect the file type and perform the conversion."""
    file_type = detect_file_type(file_name)
    logging.info(f"Session {session_id}: Detected file type: {file_type}")
    try:
        if file_type == "word":
            output_file = convert_word_to_pdf(file_name)
        elif file_type == "excel":
            output_file = convert_excel_to_pdf(file_name)
        elif file_type == "powerpoint":
            output_file = convert_ppt_to_pdf(file_name)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    except Exception as e:
        logging.error(f"Session {session_id}: Conversion failed: {e}")
        raise
    # Move converted file to dedicated directory
    converted_file = os.path.join(CONVERTED_FILES_DIR, os.path.basename(output_file))
    os.rename(output_file, converted_file)
    return converted_file


def handle_client(conn, addr):
    """Handle a single client connection."""
    session_id = generate_session_id(addr)
    logger = logging.getLogger("ServerLogger")
    logger.info(f"Session {session_id}: Connected by {addr}")
    try:
        # Step 1: Metadata Handling
        start_time = time.time()
        file_name, file_size = receive_metadata(conn)
        metadata_time = time.time() - start_time
        performance_logger.info(f"Session {session_id}: Metadata reception time: {metadata_time:.4f} seconds")

        conn.send(b"metadata_received")
        logger.info(f"Session {session_id}: Metadata acknowledged. File name: {file_name}, File size: {file_size}")

        # Step 2: File Transfer
        file_name = f"{session_id}_{file_name}"  # Prefix file name with session ID
        start_time = time.time()
        actual_size = receive_file(conn, file_name, file_size)
        file_transfer_time = time.time() - start_time
        performance_logger.info(f"Session {session_id}: File transfer time: {file_transfer_time:.4f} seconds")

        # Step 3: File Type Detection and Conversion
        start_time = time.time()
        output_file = detect_and_convert(file_name, session_id)
        conversion_time = time.time() - start_time
        performance_logger.info(f"Session {session_id}: File conversion time: {conversion_time:.4f} seconds")

        # Step 4: Sending Converted File
        start_time = time.time()
        conn.send(b"conversion_successful")
        with open(output_file, 'rb') as f:
            while (chunk := f.read(4096)):  # Increased buffer size for file sending
                conn.sendall(chunk)
        response_time = time.time() - start_time
        performance_logger.info(f"Session {session_id}: File response time: {response_time:.4f} seconds")
        logger.info(f"Session {session_id}: Converted file {output_file} sent successfully.")
    except Exception as e:
        logger.error(f"Session {session_id}: Exception occurred: {e}")
        conn.send(b"server_error")
    finally:
        conn.close()
        logger.info(f"Session {session_id}: Connection closed.")


def start_server():
    """Start the server and listen for connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        logger = logging.getLogger("ServerLogger")
        logger.info(f"Server running on {HOST}:{PORT}")
        while True:
            conn, addr = server.accept()
            Thread(target=handle_client, args=(conn, addr)).start()


if __name__ == "__main__":
    start_server()
