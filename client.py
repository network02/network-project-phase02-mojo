import socket
import os

IP = 'localhost'
PORT = 2100
ADDR = (IP, PORT)
FORMAT = "utf-8"
SIZE = 1024

def main():
    """ Starting a TCP socket. """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        """ Connecting to the server. """
        client.connect(ADDR)
        server_response = client.recv(SIZE).decode()
        print(server_response)
        
        username = input("Enter your Username: ")
        client.sendall(f"USER {username}".encode())
        server_response = client.recv(SIZE).decode()
        
        print(server_response)
        # Check if Username was not valid.
        if not server_response.startswith("200"):
            client.close()
            main()
 
        password = input("Enter your Password: ")
        client.sendall(f"PASS {password}".encode())
        server_response = client.recv(SIZE).decode()

        print(server_response)
        # Check if Password was not valid.
        if not server_response.startswith("200"):
            print("shit")
            client.close()
            main()

        while True:
            command = input("Enter your command: ")

            if "STOR" in command:
                _, client_path, server_path = command.split(' ')

                file_size = os.path.getsize(client_path)
                client.sendall(f'STOR {server_path} {file_size}'.encode(FORMAT))

                data_port = int(client.recv(SIZE).decode().split(' ')[1])
                print(data_port)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as data_channel:
                    data_channel.connect((IP, data_port))

                    with open(client_path, 'rb') as file:
                        while True:
                            data = file.read(SIZE)
                            if not data:
                                break

                            data_channel.sendall(data)
                
                    # Send the file data chunks to the server
                #    sent_bytes = SIZE
                #    while sent_bytes < file_size:
                        # Check if the data is larger than the socket buffer
                #        if file_size - sent_bytes <= SIZE:
                            # Send the remaining data
                #            data_chunk = data[sent_bytes:]
                #            data_channel.sendall(data_chunk)
                #            break
                #        else:
                            # Send the data in chunks of SIZE bytes
                #            data_chunk = data[sent_bytes + SIZE]
                #            data_channel.sendall(data_chunk)
                #            sent_bytes += SIZE
                print("HAHA")
                server_response = client.recv(SIZE).decode()
                print("shooot")
                print(server_response)
            elif "RETR" in command:
                ...
            elif "DELE" in command:
                ...
            elif command.upper().startswith("QUIT"):
                client.send(command.encode(FORMAT))

                server_response = client.recv(SIZE).decode()
                print(server_response)
                client.close()
                break
            else:
                client.send(command.encode(FORMAT))

                server_response = client.recv(SIZE).decode()
                print(server_response)


if __name__ == "__main__":
    main()
