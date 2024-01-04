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

        while True:
            command = input("Enter your command: ")


if __name__ == "__main__":
    main()