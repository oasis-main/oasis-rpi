# TCP Chat server which listens for incoming connections from chat clients
# uses port 8000

import socket, select, sys
from _thread import *

#keep list of all sockets
CONNECTION_LIST = []
RECV_BUFFER = 4096 #fairly arbitrary buffer size, specifies maximum data to be recieved at once
PORT = 8000

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("0.0.0.0", PORT))
server_socket.listen(10)
CONNECTION_LIST.append(server_socket)

##https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
print("Oasis server started on Port: " + str(PORT)+' on IP: '+socket.gethostbyname(socket.gethostname()))

while True:
    read_sockets, write_sockets, error_sockets = select.select(CONNECTION_LIST, [], [])
    
    for sock in read_sockets:
        #new connection
        if sock == server_socket:
            sockfd, addr = server_socket.accept()
            CONNECTION_LIST.append(sockfd)
            print("Client (%s, %s) connected" % addr)
                
        #incoming message from client
        else:
            try:
                data = sock.recv(RECV_BUFFER)
                data = data.decode()
                print('received data from [%s:%s]: ' % addr + data)
                ##THIS IS WHERE YOU NEED TO VERIFY THAT THE INFORMATION IS RIGHT
                sock.send('connected'.encode())
                sock.close()
                CONNECTION_LIST.remove(sock)
                
            #disconnect
            except:
                sock.close()
                CONNECTION_LIST.remove(sock)

server_socket.close()
                