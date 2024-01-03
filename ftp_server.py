## IN THE NAME OF ALLAH ##
##          SERVER      ##

import socket
import threading
import os

BASE_DIR = os.path.dirname(os.path.realpath(__file__)) + "/data"
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)
    print(f"Directory '{BASE_DIR}' created successfully.")


def handle_command(command, current_dir):
    ...

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
