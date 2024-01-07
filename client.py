import socket
import os

IP = 'localhost'
PORT = 2100
ADDR = (IP, PORT)
FORMAT = "utf-8"
SIZE = 1024


def handle_report(control_channel):
    control_channel.send("REPORT".encode(FORMAT))

    size = int(control_channel.recv(SIZE).decode())
    print(f'size: {size}')

    report = ""
    rcv_size = 0
    while True:
        data = control_channel.recv(SIZE).decode()

        report += data
        rcv_size += len(data)
        print(rcv_size)
        if rcv_size >= size:
            break

    print(report)


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
            client.close()
            main()

        while True: # Main loop
            command = input("Enter your command: ")

            if command.upper().startswith("STOR"):
                # Check if command is valid
                if len(command.split(' ')) != 3:
                    print("STOR command is not valid.")
                    continue

                _, client_path, server_path = command.split(' ')

                file_size = os.path.getsize(client_path)

                # Send the command to the server with the size of file.
                client.sendall(f'STOR {server_path} {file_size}'.encode(FORMAT))

                # Recieve data port to connect to
                data_port = int(client.recv(SIZE).decode().split(' ')[1])
                print(f'data port: {data_port}')

                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as data_channel:
                    data_channel.connect((IP, data_port))

                    with open(client_path, 'rb') as file:
                        while True:
                            data = file.read(SIZE)
                            if not data:
                                break

                            data_channel.sendall(data)
                
                server_response = client.recv(SIZE).decode()
                print(server_response)

                # End of STOR
            if command.upper().startswith("RETR"):
                # Check if command is valid
                if len(command.split(' ')) != 2:
                    print("RETR command is not valid.")
                    continue

                # Send the command to the server
                client.send(command.encode(FORMAT))

                # Extract filename from the command
                filename = '/home/lash/Downloads/' + command.split(' ')[1].split('/')[-1]

                # Get the port number and size of file from the server
                # PORT {port_num} {file_size}
                server_response = client.recv(SIZE).decode()
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
                print(server_response)

                # End of RETR
            elif command.upper().startswith("DELE"):
                # Check if the user is sure
                choice = input("Do you really wish to delete y/n? ")
                if choice == 'y' or choice == 'Y':
                    # Send the command to the server
                    client.send(command.encode(FORMAT))

                    server_response = client.recv(SIZE).decode()
                    print(server_response)
                # Else do nothing
    
                # End of DELE
            elif command.upper().startswith("REPORT"):
                server_response = handle_report(control_channel=client)

                server_response = client.recv(SIZE).decode()
                print(server_response)
            elif command.upper().startswith("QUIT"):
                # Send the command to the server
                client.send(command.encode(FORMAT))

                # Close the connection after receiving server's response and then break
                server_response = client.recv(SIZE).decode()
                print(server_response)
                client.close()
                break
            else: # For other command:
                # Send the command to the server
                client.send(command.encode(FORMAT))

                # Get the response
                server_response = client.recv(SIZE).decode()
                print(server_response)


if __name__ == "__main__":
    main()
