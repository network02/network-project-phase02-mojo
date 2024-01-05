## IN THE NAME OF ALLAH ##
##          SERVER      ##

import socket
import threading
import os
import re
import random
import shutil
import sqlite3
from passlib.hash import bcrypt

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
    DATA_PORTS[port] = True
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
        if len(command.split(' ')) < 3:
            return True
        else:
            return False
        #pattern = r"^LIST\s+/(.+)$"
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


def manage_dir(dir, current_dir):
    if dir.startswith('/'):
        return dir

    return current_dir + '/' + dir


def access(command, user_al):
    if command.upper() in ["STOR", "MKD"]:
        if user_al > 2:
            return False
    elif command.upper() in ["DELE", "RMD"]:
        if user_al > 1:
            return False
    return True


def handle_command(command, current_dir, control_channel):
    """
    Handles an FTP command based on its format and performs basic actions.

    Args:
        command: The FTP command string.

    Returns:
        A response message or None if the command is not supported.
    """
    
    # Action for command
    if command.upper().startswith("LIST"):
        print(f"Start of LIST command: {command}")
        print(f'current_dir: {current_dir}')
        directory = manage_dir(command.split(' ')[1], current_dir)
        print(f'LIST directory: {directory}')
        try:
            listing = os.listdir(directory)

            listing_string = "\n".join(listing)

            if listing_string:            
                return listing_string
            else:
                return 'Directory is empty.'
        except OSError as e:
            print(f"Error retrieving directory listing: {e}")
            return f"Error retrieving directory listing"
    
    elif command.upper().startswith("RETR"):
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
        
    elif command.upper().startswith("STOR"):
        print(f"start of STOR command: {command}")
        filename = BASE_DIR + str(command.split(' ')[1])
        file_size = int(command.split(' ')[2])

        response = ""

        # Find a random port number for the data channel
        with threading.Lock():
            print("Findig an open data port.")
            data_port = random.randint(*PORT_RANGE)
            while DATA_PORTS[data_port] == False:
                data_port = random.randint(*PORT_RANGE)

            DATA_PORTS[data_port] = False    # Close the port

        print(f'data_port:{data_port}')
        control_channel.send(f"PORT {data_port}".encode())

        # Create the data socket and listen for the client's connection
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket.bind(('localhost', data_port))
        data_socket.listen(1)
        data_channel, _ = data_socket.accept()
        print("STOR data_channel connected.")
        with open(filename, 'wb') as file: # Open the file or create it
            print("STOR file opened.")
            rcv_size = 0
            print(f'file_size:{file_size}')
            while True:
                data = data_channel.recv(1024)

                file.write(data)
                rcv_size += len(data)
                print(f'rcv_size:{rcv_size}')

                if rcv_size >= file_size:
                    response = '226 Transfer complete'
                    break
        print("STOR file recived. closing data_channel.")
        data_socket.close()
        data_channel.close()

        return response

    elif command.upper().startswith("DELE"):
        print(f"Start of DELE command: {command}")
        filename = manage_dir(command.split(' ')[1], current_dir)
        print(f'filename: {filename}')
        # Check if allowed

        try:
            os.remove(filename)
            response = '250 File deleted successfully'
        except FileNotFoundError:
            response = '550 File not found'
        except:
            response = '550 Invalid file name'
        
        return response

    elif command.upper().startswith("MKD"):
        print(f"Start of MKD command: {command}")
        directory = manage_dir(command.split(' ')[1], current_dir)
        print(f'directory: {directory}')

        if not os.path.exists(directory): 
            os.makedirs(directory)
            response = f"Directory '{command.split(' ')[1]}' created successfully."
        else: 
            response = f"Directory '{command.split(' ')[1]}' already exists"

        return response
        
    elif command.upper().startswith("RMD"):
        print(f"Start of RMD command: {command}")
        directory = manage_dir(command.split(' ')[1], current_dir)
        print(f'directory: {directory}')

        if not os.path.isdir(directory):
            response = "550 Directory does not exist"

        try:
            shutil.rmtree(directory)
            response = '250 Directory successfully removed'
        except OSError:
            response = '550 Directory does not exist'

        return response

    elif command.upper().startswith("CWD"):
        print(f"Start of RMD command: {command}")
        directory = manage_dir(command.split(' ')[1], current_dir)
        print(f'directory: {directory}')

        # check the directory

        if not os.path.isdir(directory):
            response = "550 Directory does not exist"
        else:
            current_dir = directory
            print(f'current_dir: {current_dir}')
            response = f"Current directory changed to '{command.split(' ')[1]}'"

        return response

    elif command.upper().startswith("CDUP"):
        print(f"Start of CDUP command: {command}")

        if current_dir == BASE_DIR:
            response = '550 Cannot change to parent directory of root directory'
        else:
            print("niggaz")
            parent_dir = os.path.dirname(current_dir)
            print("niggaz")
            current_dir = parent_dir
            response = '250 Directory successfully changed'    
    else:
        response = 'Command Invalid.'

        return response

def handle_client(conn, addr):
    current_dir = BASE_DIR
    username = ""
    password = ""
    inp_password = ""
    access_level = 4
    authenticated = False
    try:
        while True:
            # Receive data from the client
            command = conn.recv(1024).decode()
            print(command)

            if not validate_command(command):
                response = f"Command '{command}' not supported"
                conn.sendall(response.encode())
                continue

            if command.upper().startswith("QUIT"):
                print(f'Client {addr} disconnected')
                conn.sendall("You may disconnect.".encode())
                break
            elif command.upper().startswith("USER"):
                db = sqlite3.connect('ftp_users.db')
                cursor = db.cursor()

                username = command.split(' ')[1]

                cursor.execute('SELECT username, password, access_level FROM users WHERE username = ?', (username,))
                existing_user = cursor.fetchone()

                db.close()

                if existing_user:
                    username, password, access_level = existing_user
                    response = "200 User login successful"
                else:
                    response = "401 Invalid username"
                conn.sendall(response.encode())
                continue
            elif command.upper().startswith("PASS"):
                inp_password = command.split(' ')[1]

                if username and password == inp_password:
                    response = "200 Password accepted"
                    authenticated = True
                else:
                    response = "401 Invalid password"
                conn.sendall(response.encode())
                continue
            elif command.upper().startswith("CWD"):
                print(f"Start of CWD command: {command}")
                directory = manage_dir(command.split(' ')[1], current_dir)
                print(f'directory: {directory}')

                # check the directory

                if not os.path.isdir(directory):
                    response = "550 Directory does not exist"
                else:
                    current_dir = directory
                    print(f'current_dir: {current_dir}')
                    response = f"Current directory changed to '{command.split(' ')[1]}'"

                conn.sendall(response.encode())
                continue
            elif command.upper().startswith("CDUP"):
                print(f"Start of CDUP command: {command}")

                if current_dir == BASE_DIR:
                    response = '550 Cannot change to parent directory of root directory'
                else:
                    print("niggaz")
                    parent_dir = os.path.dirname(current_dir)
                    print("niggaz")
                    current_dir = parent_dir
                    response = '250 Directory successfully changed'

                conn.sendall(response.encode())
                continue

            if authenticated:
                if access(command.split(' ')[0], access_level):
                    print("authenticated user gonna handle his command")
                    response = handle_command(command, current_dir, conn)
                else:
                    response = "550 Permission Denied"
            else:
                response = "You must login first"
            conn.sendall(response.encode('utf-8'))

    except Exception as e:
        print(f"Error handling client {addr}: {e}")

    finally:
        print("finally!")
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
            conn.sendall("Connected.".encode())
            print("Connected by", addr)

            # Create a new thread for each client connection
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()

if __name__ == "__main__":
    main()
