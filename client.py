import socket

IP = 'localhost'
PORT = 21
ADDR = (IP, PORT)
FORMAT = "utf-8"
SIZE = 1024

def main():
    """ Starting a TCP socket. """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        """ Connecting to the server. """
        client.connect(ADDR)
        response = client.recv(SIZE).decode()

        username = input("Enter your Username: ")
        client.sendall(f"USER {username}\r\n".encode())
        server_response = client.recv(SIZE).decode()

        print(server_response)
        # Check if Username was not valid.
        if not server_response.startswith("200"):
            client.close()
            main()
 
        password = input("Enter your Password: ")
        client.sendall(f"PASS {password}\r\n".encode())
        server_response = client.recv(SIZE).decode()

        print(server_response)
        # Check if Password was not valid.
        if not server_response.startswith("200"):
            client.close()
            main()

        while True:
            command = input("Enter your command: ")


if __name__ == "__main__":
    main()