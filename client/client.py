import socket
import os

HOST = '127.0.0.1'
PORT = 65432

def send_file(file_path):
    try:
        # Check if the file exists
        if not os.path.exists(file_path):
            print("[ERROR] File does not exist.")
            return
        
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            print("[ERROR] File is empty. Cannot send.")
            return
        
        print(f"[DEBUG] File name: {file_name}, File size: {file_size}")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect((HOST, PORT))
            print(f"[INFO] Connected to server at {HOST}:{PORT}")

            # Send Metadata
            metadata = f"{file_name};{file_size}"
            client.send(metadata.encode('utf-8'))
            print(f"[DEBUG] Metadata sent: {metadata}")

            # Wait for Metadata Acknowledgment
            ack = client.recv(1024).decode('utf-8')
            if ack != "metadata_received":
                print("[ERROR] Metadata acknowledgment failed.")
                return

            print("[INFO] Metadata acknowledged by server.")

            # Send File Data
            with open(file_path, 'rb') as f:
                sent = 0
                while (chunk := f.read(4096)):
                    client.sendall(chunk)
                    sent += len(chunk)
                    print(f"[DEBUG] Sent {len(chunk)} bytes. Total sent: {sent} bytes.")
            print(f"[INFO] File {file_name} sent successfully.")

            # Handle Server Response
            status = client.recv(1024).decode('utf-8')
            print(f"[DEBUG] Server response: {status}")
            if status == "conversion_successful":
                print("[INFO] File converted successfully. Downloading...")
                output_dir = "converted_files"
                os.makedirs(output_dir, exist_ok=True)
                output_file = os.path.join(output_dir, f"converted_{file_name}.pdf")
                with open(output_file, 'wb') as f:
                    while (data := client.recv(1024)):
                        f.write(data)
                print(f"[INFO] Converted file saved as {output_file}.")
            else:
                print(f"[ERROR] Server error: {status}")
    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")

if __name__ == "__main__":
    file_path = input("Enter the full path of the file to upload: ")
    send_file(file_path)
