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

            if command.upper().startswith("STOR"):
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
            if command.upper().startswith("RETR"):
                client.send(command.encode(FORMAT))
                filename = command.split(' ')[1].split('/')[-1]
                filename = '/home/lash/Downloads/' + filename

                server_response = client.recv(SIZE).decode()
                print(server_response)
                data_port = int(server_response.split(' ')[1])
                file_size = int(server_response.split(' ')[2])
                print(f'data_port: {data_port}, file_size:{file_size}')

                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as data_channel:
                    data_channel.connect((IP, data_port))

                    with open(filename, 'wb') as file:
                        rcv_size = 0

                        while True:
                            data = data_channel.recv(SIZE)

                            file.write(data)
                            rcv_size += len(data)

                            if rcv_size >= file_size:
                                break
                
                server_response = client.recv(SIZE).decode()
                print("fletcher")
                print(server_response)
            elif command.upper().startswith("DELE"):
                choice = input("Do you really wish to delete y/n? ")
                if choice == 'y' or choice == 'Y':
                    client.send(command.encode(FORMAT))

                    server_response = client.recv(SIZE).decode()
                    print(server_response)
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
