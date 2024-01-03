## IN THE NAME OF ALLAH ##
##          SERVER      ##

import socket
import threading

def main():
    HOST = 'localhost'
    PORT = 21

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
