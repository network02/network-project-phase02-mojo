## IN THE NAME OF ALLAH ##
##          SERVER      ##

import socket
import threading
import os
import re
import random
import shutil

users = {
    "mamad": {
        "password": "mamad",
        "access_level": 1
    },
    "ali": {
        "password": "ali",
        "access_level": 4
    }
}
DATA_PORTS = {}
PORT_RANGE = (50000, 60000)
for port in range(*PORT_RANGE):
    DATA_PORTS[port] = False
BASE_DIR = os.path.dirname(os.path.realpath(__file__)) + "/data"
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)
    print(f"Directory '{BASE_DIR}' created successfully.")
HEADERSIZE = 1024


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


def handle_command(command, current_dir, control_channel):
    """
    Handles an FTP command based on its format and performs basic actions.

    Args:
        command: The FTP command string.

    Returns:
        A response message or None if the command is not supported.
    """

    if not validate_command(command):
        return f"Command '{command}' not supported"
    
    # Action for command
    if command.upper().startswith("USER"):
        username = command.split(' ')[1]

        if username in users:   # User Database: "username": "password", "access_level"
            current_user = username
            return "User login successful"
        else:
            return "Invalid username"

    elif command.upper().starswith("PASS"):
        password = command.split(' ')[1]

        if current_user and users[current_user]["password"] == password:
            return "Password accepted"
        else:
            current_user = None
            return "Invalid password"
    
    elif command.upper().starswith("LIST"):
        directory = BASE_DIR + command.split(' ')[1]
        try:
            listing = os.listdir(directory)

            listing_string = "\n".join(listing)

            return listing_string.encode()
        except OSError as e:
            print(f"Error retrieving directory listing: {e}")
            return f"Error retrieving directory listing"
    
    elif command.upper().starswith("RETR"):
        directory = BASE_DIR + command.split(' ')[1]
        
        try:
            # Find a random port number for the data channel
            with threading.Lock():
                data_port = random.randint(*PORT_RANGE)
                while DATA_PORTS[data_port] == False:
                    data_port = random.randint(*PORT_RANGE)
                data_port[data_port] = False    # Close the port

            # Send the port number to the client over the control channel
            file_size = os.path.getsize(file)
            data_length = str(HEADERSIZE + file_size).encode()
            control_channel.send(f"PORT {data_port}\r\n{data_length}\r\n".encode())

            # Create the data socket and listen for the client's connection
            data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_socket.bind(('localhost', data_port))
            data_socket.listen(1)
            data_channel, _ = data_socket.accept()

            # Read the entire file into a buffer
            with threading.Lock():
                with open(file, 'rb') as file:
                    data = file.read()

            # Send the file data chunks to the client
            sent_bytes = HEADERSIZE
            while sent_bytes < file_size:
                # Check if the data is larger than the socket buffer
                if file_size - sent_bytes < 1024:
                    # Send the remaining data
                    data_chunk = data[sent_bytes:]
                    data_channel.sendall(data_chunk)
                else:
                    # Send the data in chunks of 1024 bytes
                    data_chunk = data[sent_bytes:sent_bytes + 1024]
                    data_channel.sendall(data_chunk)
                    sent_bytes += 1024

            # Close the data channel
            data_socket.close()
            data_channel.close()

            with threading.Lock():
                data_port[data_port] = True # Open the port

            # Send control messages to the client
            control_channel.send("226 Transfer complete\r\n".encode())
        
        except FileNotFoundError:
            control_channel.send("450 Requested file action not taken. File unavailable\r\n".encode())

        except Exception as e:
            print(f"An error occurred: {e}")
            control_channel.send("451 Requested action aborted. Local error in processing\r\n".encode())
        
    elif command.upper().starswith("STOR"):
        _, filename, file_size = BASE_DIR + command.split(' ')

                    # Find a random port number for the data channel
        with threading.Lock():
            data_port = random.randint(*PORT_RANGE)
            while DATA_PORTS[data_port] == False:
                data_port = random.randint(*PORT_RANGE)
            data_port[data_port] = False    # Close the port

        control_channel.send(f"PORT {data_port}\r\n".encode())

        # Create the data socket and listen for the client's connection
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket.bind(('localhost', data_port))
        data_socket.listen(1)
        data_channel, _ = data_socket.accept()

        with open(filename, 'wb') as file: # Open the file or create it

            rcv_size = 0
            while True:
                data = data_channel.recv(1024)
                
                file.write(data)
                rcv_size += len(data)

                if rcv_size >= file_size:
                    control_channel.sendall('226 Transfer complete'.encode('utf-8'))
                    break
        
        data_socket.close()
        data_channel.close()

    elif command.upper().starswith("DELE"):
        filename = BASE_DIR + command.split(' ')[1]

        # Check if allowed

        try:
            os.remove(filename)
            response = '250 File deleted successfully\r\n'
        except FileNotFoundError:
            response = '550 File not found\r\n'
        except:
            response = '550 Invalid file name\r\n'
        
        control_channel.sendall(response.encode('utf-8'))

    elif command.upper().starswith("MKD"):
        directory = command.split(' ')[1]

        if not os.path.exists(directory): 
            os.makedirs(directory)
            response = f"Directory '{directory}' created successfully."
        else: 
            response = f"Directory '{directory}' already exists"

        control_channel.sendall(response.encode('utf-8'))
        
    elif command.upper().startswith("RMD"):
        directory = command.split(' ')[1]

        if not os.path.isdir(directory):
            control_channel.sendall("550 Directory does not exist\r\n")
            return

        try:
            shutil.rmtree(directory)
            response = '250 Directory successfully removed\r\n'
        except OSError:
            response = '550 Directory does not exist\r\n'

        control_channel.sendall(response.encode('utf-8'))

    elif command.upper().startswith("CWD"):
        directory = command.split(' ')[1]

        # check the directory
        # response = 'Invalid directory'

        current_dir = directory
        response = f"Current directory changed to '{directory}'"

        control_channel.sendall(response.encode('utf-8'))

    elif command.upper().starswith("CDUP"):
        if current_dir == BASE_DIR:
            response = '550 Cannot change to parent directory of root directory\r\n'
        else:
            parent_dir = os.path.dirname(current_dir)
            current_dir = parent_dir
            response = '250 Directory successfully changed\r\n'
        
        control_channel.sendall(response.encode('utf-8'))
    
    else:
        response = 'Command Invalid.'

        control_channel.sendall(response.encode('utf-8'))

def handle_client(conn, addr):
    current_dir = BASE_DIR
    try:
        while True:
            # Receive data from the client
            command = conn.recv(1024)

            if command.upper().starswith("QUIT"):
                print(f'Client {addr} disconnected')
                conn.close()
                break

            response = handle_command(command, current_dir, conn)
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
