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

# Define a range of ports for data transfer
DATA_PORTS = {}
PORT_RANGE = (50000, 60000)
# Iterate over the port range and create a dictionary of open ports
for port in range(*PORT_RANGE):
    DATA_PORTS[port] = True

# Get the absolute path of the directory containing the current file
BASE_DIR = os.path.dirname(os.path.realpath(__file__)) + "/data"
# Check if the data directory exists, and create it if it doesn't
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)
    print(f"Directory '{BASE_DIR}' created successfully.")

IP = 'localhost'
PORT = 2100
ADDR = (IP, PORT)
FORMAT = "utf-8"
SIZE = 1024


def command_is(usercommand, command):
    return usercommand.upper().startswith(command)


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


def validate_command2(command):
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
        if len(command.split(' ')) < 3:
            return True
        else:
            return False
        #pattern = r"^PASS\s+(\w+)$"
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
    elif command.upper().startswith("REPORT"):
        pattern = r"^REPORT$"  # No arguments expected
    else:
        return False

    return is_valid_string(command.upper(), pattern)


def validate_command(command):
    # Check if the command has the correct format
    #if command_is(usercommand=command, command="LIST") or command_is(usercommand=command, command="PWD") or command_is(usercommand=command, command="CDUP") or command_is(usercommand=command, command="QUIT"):

    try:
        # 0 arg
        if command.upper().split(' ')[0] in ["PWD", "CDUP", "QUIT"]:
            if len(command.split(' ')) != 1:
                return False
        # 1 arg
        elif command.upper().split(' ')[0] in ["USER", "PASS", "DELE", "RETR", "MKD", "CWD"]:
            if len(command.split(' ')) != 2:
                return False
        # 2 arg
        elif command.upper().split(' ')[0] in ["STOR"]:
            if len(command.split(' ')) != 3:
                return False
        elif command.upper().split(' ')[0] == "LIST":
            if len(command.split(' ')) > 2:
                return False
        else:
            return False

    except ValueError:
        print("Invalid format for FTP command:", command)
        return False
    
    return True


def manage_dir(dir, current_dir):
    if dir.startswith('/'):
        return BASE_DIR + dir

    return current_dir + '/' + dir


def access(command, user_al):
    if command.upper() in ["STOR", "MKD"]:
        if user_al > 2:
            return False
    elif command.upper() in ["DELE", "RMD"]:
        if user_al > 1:
            return False
    return True


def handle_list(command, current_dir):
    print(f"Start of LIST command: {command}")
    print(f'current_dir: {current_dir}')

    if len(command.split(' ')) > 1:
        directory = manage_dir(command.split(' ')[1], current_dir)
    else:
        directory = current_dir

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


def handle_retr(command, current_dir, control_channel):
    print("Start of RETR command.")
    directory = manage_dir(command.split(' ')[1], current_dir)
    print(f"directory: {directory}")
    
    try:
        # Find a random port number for the data channel
        with threading.Lock():
            data_port = random.randint(*PORT_RANGE)
            while DATA_PORTS[data_port] == False:
                data_port = random.randint(*PORT_RANGE)
            DATA_PORTS[data_port] = False    # Close the port

        # Send the port number to the client over the control channel
        file_size = os.path.getsize(directory)
        control_channel.send(f"PORT {data_port} {file_size}".encode())

        # Create the data socket and listen for the client's connection
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket.bind(('localhost', data_port))
        data_socket.listen(1)
        data_channel, _ = data_socket.accept()

        # Read the entire file into a buffer
        with threading.Lock():
            with open(directory, 'rb') as file:
                while True:
                    data = file.read(1024)
                    if not data:
                        break

                    data_channel.sendall(data)

        # Close the data channel
        data_socket.close()
        data_channel.close()

        with threading.Lock():
            DATA_PORTS[data_port] = True # Open the port

        response = "226 Transfer complete"
    
    except FileNotFoundError:
        response = "450 Requested file action not taken. File unavailable"

    except Exception as e:
        print(f"An error occurred: {e}")
        response = "451 Requested action aborted. Local error in processing"
    
    return response


def handle_stor(command, control_channel):
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
    control_channel.send(f"PORT {data_port}".encode(FORMAT))

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
            data = data_channel.recv(SIZE)

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


def handle_dele(command, current_dir):
    print(f"Start of DELE command: {command}")
    filename = manage_dir(command.split(' ')[1], current_dir)
    print(f'filename: {filename}')

    try:
        os.remove(filename)
        response = '250 File deleted successfully'
    except FileNotFoundError:
        response = '550 File not found'
    except:
        response = '550 Invalid file name'
    
    return response


def handle_mkd(command, current_dir):
    print(f"Start of MKD command: {command}")
    directory = manage_dir(command.split(' ')[1], current_dir)
    print(f'directory: {directory}')

    if not os.path.exists(directory): 
        os.makedirs(directory)
        response = f"Directory '{command.split(' ')[1]}' created successfully."
    else: 
        response = f"Directory '{command.split(' ')[1]}' already exists"

    return response


def handle_rmd(command, current_dir):
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


def handle_pwd(current_dir):
    dir = current_dir.replace(BASE_DIR, "")
    if dir:
        return dir
    else:
        return "/"


def handle_client(conn, addr):
    current_dir = BASE_DIR
    username = ""
    password = ""
    inp_password = ""
    access_level = 4
    authenticated = False

    db = sqlite3.connect('ftp_users.db')
    curs = db.cursor()

    try:
        while True:
            # Receive data from the client
            command = conn.recv(1024).decode()
            print(command)

            if not validate_command(command):
                response = f"Command '{command}' not supported"
                conn.sendall(response.encode())
                continue

            if command_is(usercommand=command, command="USER"):
                cursor = db.cursor()

                username = command.split(' ')[1]

                cursor.execute('SELECT username, password, access_level FROM users WHERE username = ?', (username,))
                existing_user = cursor.fetchone()


                if existing_user:
                    username, password, access_level = existing_user
                    response = "200 User login successful"
                else:
                    response = "401 Invalid username"
                conn.sendall(response.encode())
                continue
            elif command_is(usercommand=command, command="PASS"):
                inp_password = command.split(' ')[1]

                if username and password == inp_password:
                    response = "200 Password accepted"
                    authenticated = True
                else:
                    response = "401 Invalid password"
                conn.sendall(response.encode())
                continue
            elif command_is(usercommand=command, command="QUIT"):
                print(f'Client {addr} disconnected')
                conn.sendall("You may disconnect.".encode())
                break


            if authenticated and access(command.split(' ')[0], access_level):
                print("authenticated user gonna handle his command")
                curs.execute('INSERT INTO report (username, command) VALUES (?, ?)',
                                (username, command))
                db.commit()


                if command.upper().startswith("LIST"):
                    response = handle_list(command=command, current_dir=current_dir)
                elif command.upper().startswith("RETR"):
                    response = handle_retr(command=command, current_dir=current_dir, control_channel=conn)
                elif command.upper().startswith("STOR"):
                    response = handle_stor(command=command, control_channel=conn)
                elif command.upper().startswith("DELE"):
                    response = handle_dele(command=command, current_dir=current_dir)
                elif command.upper().startswith("MKD"):
                    response = handle_mkd(command=command, current_dir=current_dir)
                elif command.upper().startswith("RMD"):
                    response = handle_rmd(command=command, current_dir=current_dir)
                elif command.upper().startswith("PWD"):
                    response = handle_pwd(current_dir=current_dir)
                elif command.upper().startswith("CWD"):
                    curs.execute('INSERT INTO report (username, command) VALUES (?, ?)',
                                    (username, command))
                    
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
                elif command.upper().startswith("CDUP"):
                    curs.execute('INSERT INTO report (username, command) VALUES (?, ?)',
                                    (username, command))
                    
                    print(f"Start of CDUP command: {command}")

                    if current_dir == BASE_DIR:
                        response = '550 Cannot change to parent directory of root directory'
                    else:
                        parent_dir = os.path.dirname(current_dir)
                        current_dir = parent_dir
                        response = '250 Directory successfully changed'
                elif command.upper().startswith("REPORT"):
                    curs.execute('INSERT INTO report (username, command) VALUES (?, ?)',
                                    (username, command))

                    curs.execute('SELECT command FROM report WHERE username = ?', (username,))
                    commands = curs.fetchall()

                    response = '\n'.join(command[0] for command in commands)

                conn.sendall(response.encode(FORMAT))
            else:
                response = "550 Permission Denied"

    except Exception as e:
        print(f"Error handling client {addr}: {e}")

    finally:
        print(f"User {addr} disconnected!")
        db.close()
        conn.close()


def main():
    db = sqlite3.connect('ftp_users.db')
    cursor = db.cursor()

    # Create the 'users' table if it doesn't already exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            access_level INTEGER NOT NULL    
        )
    ''')

    db.commit()
    db.close()

    db = sqlite3.connect('ftp_users.db')
    cursor = db.cursor()

    # Create the 'report' table if it doesn't already exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS report (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            command TEXT NOT NULL
        )
    ''')

    db.commit()
    db.close()

    while True:
        print("--- --- --- --- ---")
        print("-1- Start the server.")
        print("-2- Manage Users.")
        print("-3- Report.")
        print("-4- EXIT.")
        choice = input("--- Enter Your Choice: ")
        print("--- --- --- --- ---")

        if choice == '1':   # Start the server
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(ADDR)
                s.listen()

                print("Server listening on port", PORT)

                while True:
                    conn, addr = s.accept()
                    conn.sendall(f"Welcome to the server, {addr}! You are now connected.".encode())
                    print("Connected by", addr)

                    # Create a new thread for each client connection
                    client_thread = threading.Thread(target=handle_client, args=(conn, addr))
                    client_thread.start()
        elif choice == '2': # Manage users
            print("-1- Add a new user")
            print("-2- Delete a user")
            print("-3- User's profile")
            choice = input("--- Enter Your Choice: ")
            print("--- --- --- --- ---")

            db = sqlite3.connect('ftp_users.db')
            cursor = db.cursor()

            if choice == '1':   # Add a new user
                # Get input for username, password, and access level of new user
                username = input("Enter user's username: ")
                password = input("Enter user's password: ")
                access_level = int(input("Enter user's access_level [1, 2, 3, 4]: "))
        
                # Check if the user already exists in the database
                cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
                existing_user = cursor.fetchone()

                if existing_user:
                    print(f"User '{username}' already exists.")
                else:
                    # Insert the new user into the database
                    cursor.execute('INSERT INTO users (username, password, access_level) VALUES (?, ?, ?)',(username, password, access_level))

                    print(f"User '{username}' registered with access level {access_level}.")

                # End of adding a new user
            elif choice == '2': # Delete a user
                # Get the username to delete from the user
                username = input("Enter user's username: ")
        
                # Check if the user exists in the database
                cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
                existing_user = cursor.fetchone()

                if existing_user:
                    # Delete the user from the database
                    cursor.execute('DELETE FROM users WHERE username = ?', (username,))
                    print(f"User '{username}' deleted from the database.")
                else:
                    print(f"User '{username}' not found in the database.")

                # End of deleting a user
            elif choice == '3': # User's profile
                # Get the username
                username = input("Enter user's username: ")

                # Check if the user exists in the database
                cursor.execute('SELECT username, access_level FROM users WHERE username = ?', (username,))
                existing_user = cursor.fetchone()

                if existing_user:
                    # Display the user's current information
                    username, access_level = existing_user
                    print(f'username: {username}')
                    print(f'access_level: {access_level}')

                    # Fetch the user's past commands from the 'report' table
                    cursor.execute('SELECT command FROM report WHERE username = ?', (username,))
                    commands = cursor.fetchall()

                    # Display the list of past commands
                    print('\n'.join(command[0] for command in commands))

                    print("\n-1- Edit")
                    print("-2- To Continue")
                    choice = input("-Enter Your Choice: ")

                    if choice == '1':   # Edit
                        # Prompt the user for new password and access level
                        new_password = input("Enter user's password: ")
                        new_access_level = int(input("Enter user's access_level [1, 2, 3, 4]: "))

                        # Update the user's information in the 'users' table
                        cursor.execute('UPDATE users SET password = ?, access_level = ? WHERE username = ?',(new_password, new_access_level, username))
                        print(f"User '{username}' updated in the database.")
                    # Else continue
                else:
                    print(f"User '{username}' not found in the database.")
            
            db.commit()
            db.close()
        elif choice == '3': # Report
            db = sqlite3.connect('ftp_users.db')
            cursor = db.cursor()

            cursor.execute('SELECT command, username FROM report')
            commands = cursor.fetchall()

            db.close()

            print('\n'.join(command[0]+','+command[1] for command in commands))

            main()
        else:   # EXIT
            break

if __name__ == "__main__":
    main()
