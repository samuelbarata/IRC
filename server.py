#!/bin/python3
import socket, sys, threading, signal, os

bind_address    = ''
bind_port       = 45080

#   Comandos:
#       HELP                -- lista os comandos a usar
#       REGISTER <nome>     -- regista um novo user
#       LIST                -- lista todos os jogadores online
#       INVITE <nome>       -- convida jogador para um jogo
#       ACCEPT              -- aceita convite para jogo
#       REJECT              -- rejeita convide para jogo
#       PLAY <x> <y>        -- joga na posicao X Y
#       FOLD                -- desiste do jogo atual
#       EXIT                -- sai da aplicacao

#mensagens erro:
ERR                 = "ERROR "
REG_FAIL            = "Username already in use, pick a different one\n"
NO_USER             = "No such user exists, LIST all users and pick a valid user\n"
USER_BUSY           = "User is busy, LIST all users to check their status\n"
INVALID_COOR        = "Invalid Coordinates, valid {0,1,2}\n"
INVALID_PLAY        = "{} already has {}\n"
USER_DISCONECTED    = "Oponent has left the game, you win\n"
NOT_IN_GAME         = "This command is only valid during a game type HELP to see how to start a new game\n"
SERVER_OFF          = "The server will exit and you'll be disconnected automatically\n"
BAD_REQUEST         = "Bad Request, type HELP to see available commands\n"
USER_UNKNOWN        = "User unregistered, you need to register before doing this action\n"
USER_REGISTERED     = "You are already registered\n"

#mensagens ok:
SUC                 = "OK "
REG_OK              = "Registado com sucesso\n"
INVITE_OK           = "Waiting for reply...\n"
ACEPT               = "{} has acepted your request\n"
REJECT              = "{} has rejected your request\n"
WAITING_FOR_PLAY    = "Not your turn to play\n"
WIN                 = "Congratulations, you have won\n"
LOSE                = "Better luck next time\n"
TIE                 = "Tie\n"
DISPLAY             = "DISPLAY "

users ={} #user: [socketfd, status, [game]]
server = 0
connections=[]

def help():
    return "DISPLAY insert help text here\n"
#----

def exit_server(sig, frame):
    print("\nExiting server recieved signal {}, on {}...".format(sig, frame))
    server.close()
    for c in connections:
        c.send("SERVER_OFF\n".encode())
        c.close()
    exit(0)
#----

def register(user, client):
    for i in users:
        if(users[i][0]==client):
            return "ERR USER_REGISTERED\n"
    users[user]=[client, 0]
    return "SUC REG_OK " +user + "\n"
#----

def list():
    return "LIST " + str([(i, users[i][1]) for i in users]) + '\n'
#----

def invite(myself, user):
    for i in users:
        if(users[i][0] == myself):
            myself=users[i]
            break
    if(myself not in users):
        return ERR + USER_UNKNOWN
    if(user not in users):
        return ERR + NO_USER
    if(users[user][1]!=0):
        return ERR + USER_BUSY
    users[myself][1]=1
    users[user][0].send("INVITE {}".format(myself).encode())
    return "SUC INVITE_OK\n"
#----

def process_input(msg, client):
    msg=msg[:-1:] #retira o \n
    msg=msg.upper()
    msg=msg.split(" ")
    print("Recieved >{}<".format(msg))

    if(msg[0]=="HELP"):
        return help()
    elif(msg[0]=="REGISTER"):
        if(len(msg)==2):
            return register(msg[1], client)
        else:
            return ERR + BAD_REQUEST
    elif(msg[0]=="LIST"):
        if(len(msg)==1):
            return list()
        else:
            return ERR + BAD_REQUEST
    elif(msg[0]=="EXIT"):
        raise socket.timeout()

    elif(msg[0]=="INVITE"):
        if(len(msg)!=2):
            pass
        else:
            return invite(msg[1])

 
    return "ERR BAD_REQUEST\n"
#----



def handle_client_connection(client_sock):
    signal.pthread_sigmask(signal.SIG_SETMASK, [signal.SIGINT, signal.SIGKILL])
    try:
        connections.append(client_sock)
        while True:
            request=''
            #soma strings ate ter mensagem completa
            while(request=='' or request[-1]!='\n'):
                msg_from_client = client_sock.recv(1024)
                if(not msg_from_client):
                    raise socket.timeout()
                request += str(msg_from_client.decode())
                
            client_sock.send(process_input(request, client_sock).encode())
    except socket.timeout:
        for i in users:
            if(users[i][0]==client_sock):
                del(users[i])
                break
        for i in range(len(connections)):
            if(connections[i]==client_sock):
                del(connections[i])
                break
        client_sock.close()
        print("Client disconected".format(client_sock))
        exit(0)
#----




def main():
    global server
    server=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((bind_address, bind_port))
    server.listen(100);
    print("Listening on {}:{}".format(bind_address, bind_port))
    signal.signal(signal.SIGINT, exit_server)
    while  True:
        client_sock, address = server.accept()
        print("Acepted connection from {}:{}".format(address[0],address[1]))
        client_handler=threading.Thread(target=handle_client_connection, args=(client_sock, ))
        client_handler.start()
#----

if(__name__ == '__main__'):
    main()

