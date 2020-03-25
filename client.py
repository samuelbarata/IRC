#!/bin/python3
import socket, signal, sys, select

server_ip = [socket.gethostbyname("samuel.freetcp.com"), "127.0.0.1", "192.168.1.42"]
server_port = 45080
server = -1
MSG_SIZE = 1024
HLINE="{}{}{}{}{}{}{}{}{}{}{}\n".format(chr(9472), chr(9472), chr(9472),chr(9532),chr(9472), chr(9472),
                                      chr(9472),chr(9532), chr(9472), chr(9472), chr(9472))

def exit_sig(sig=0, frame=0):
    client.close()
    exit(0)

def process_input(server_msg):
    """
    Recieves the server Message, returned value will be sent to server
    """ 
    server_msg=str(server_msg).split(" ")
    if(server_msg[0]=="BOARD"):
        board=eval(server_msg[1])
        for i in range(len(board)):
            for k in range(len(board[i])):
                if(board[i][k]==0):
                    board[i][k]=' '
                elif(board[i][k]==1):
                    board[i][k]='X'
                else:
                    board[i][k]='O'
        print(\
            " {} | {} | {} \n".format(board[0][0], board[0][1], board[0][2])\
            +HLINE\
            +" {} | {} | {} \n".format(board[1][0], board[1][1], board[1][2])\
            +HLINE\
            +" {} | {} | {} \n".format(board[2][0], board[2][1], board[2][2]))
while(not 0<=server<len(server_ip)):
    server = int(input("Select server:\n0: Remote Server\n1: Localhost\n2: VM\n"))

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client.connect((server_ip[server], server_port))
except:
    print("ERROR: Server {} is offline".format(server_ip[server]))
    client.close()
    exit(1)

signal.signal(signal.SIGINT, exit_sig)
inputs = [client, sys.stdin]

while True:
    print("COMAND:")
    ins, outs, exs = select.select(inputs, [], [])
    for i in ins:
        if(i==sys.stdin):
            response=sys.stdin.readline()
            client.sendto(response.encode(),(server_ip[server],server_port))
        elif(i==client):
            (server_msg, addr) = client.recvfrom(MSG_SIZE)
            process_input(server_msg.decode())



