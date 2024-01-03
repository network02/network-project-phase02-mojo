## IN THE NAME OF ALLAH ##
##          SERVER      ##

import socket
import threading
import os
import re

BASE_DIR = os.path.dirname(os.path.realpath(__file__)) + "/data"
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)
    print(f"Directory '{BASE_DIR}' created successfully.")


def is_valid_string(text, pattern):
    """
    Checks if a string is valid based on a regular expression pattern.

    Args:
        text: The string to validate.
        pattern: The regular expression pattern.

    Returns:
        True if the string is valid, False otherwise.
    """
    match = re.fullmatch(pattern, text)
    return bool(match)


def validate_command(command):
    """
    Validates a FTP command based on its format.

    Args:
        command: The FTP command string.

    Returns:
        True if the command is valid, False otherwise.
    """

    if command.upper().startswith("USER"):
        pattern = r"^USER\s+(\w+)$"
    elif command.upper().startswith("PASS"):
        pattern = r"^PASS\s+(\w+)$"
    elif command.upper().startswith("LIST"):
        pattern = r"^LIST\s+/(.+)$"
    elif command.upper().startswith("RETR"):
        pattern = r"^RETR\s+(.+)$"  # Capture the filename
    elif command.upper().startswith("STOR"):
        pattern = r"^STOR\s+(.+)\s+(.+)$"  # Capture two filenames
    elif command.upper().startswith("DELE"):
        pattern = r"^DELE\s+(.+)$"  # Capture the filename
    elif command.upper().startswith("MKD"):
        pattern = r"^MKD\s+(.+)$"  # Capture the directory name
    elif command.upper().startswith("RMD"):
        pattern = r"^RMD\s+(.+)$"  # Capture the directory name
    elif command.upper().startswith("PWD"):
        pattern = r"^PWD$"  # No arguments expected
    elif command.upper().startswith("CWD"):
        pattern = r"^CWD\s+(.+)$"  # Capture the directory name
    elif command.upper().startswith("CDUP"):
        pattern = r"^CDUP$"  # No arguments expected
    elif command.upper().startswith("QUIT"):
        pattern = r"^QUIT$"  # No arguments expected
    else:
        return False

    return is_valid_string(command.upper(), pattern)


def handle_command(command, current_dir):
    """
    Handles an FTP command based on its format and performs basic actions.

    Args:
        command: The FTP command string.

    Returns:
        A response message or None if the command is not supported.
    """

    if not validate_command(command):
        return f"Command '{command}' not supported"

def handle_client(conn, addr):
    current_dir = BASE_DIR
    try:
        while True:
            # Receive data from the client
            command = conn.recv(1024)
            if not command:
                break

            response = handle_command(command, current_dir)
            conn.sendall(response)

    except Exception as e:
        print(f"Error handling client {addr}: {e}")

    finally:
        conn.close()


def main():
    HOST = 'localhost'
    PORT = 2100

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()

        print("Server listening on port", PORT)

        while True:
            conn, addr = s.accept()
            print("Connected by", addr)

            # Create a new thread for each client connection
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()

if __name__ == "__main__":
    main()
