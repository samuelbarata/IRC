#!/bin/python3
import socket, sys, threading, signal, os
from threading import RLock

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


EMPTY_BOARD=[[0,0,0],[0,0,0],[0,0,0]]
EMPTY_LINE=[0,0,0]
users ={} #user: [socketfd, status, [game]]
#status 0 = available
#       1 = (in game) NOT USED
#       2 = waiting for reply
#       3 = invited
#       4 = MY TURN
#       5 = NOT MY TURN

server = 0
connections=[]
lock = RLock()

def help():
    return  "DISPLAY "+\
            "HELP\t\t\tDisplay this help text;"+\
            "REGISTER <username>\tRegister user in the game;"+\
            "LIST\t\t\tDisplays the list of online users;"+\
            "INVITE <username>\tInvites the other player to start a game;"+\
            "ACCEPT\t\t\tAccept a current invitation to play;"+\
            "REJECT\t\t\tDeclines a current invitation to play;"+\
            "PLAY <x> <y>\t\tPlay in selected cell;"+\
            "FOLD\t\t\tFolds the current game;"+\
            "EXIT\t\t\tLeaves the game\n"
#----

def exit_server(sig, frame):
    print("\nExiting server recieved signal {}...".format(sig))
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
    if(user in users):
        return "ERR REG_FAIL\n"
    users[user]=[client, 0, ["quem convida", "convidado", ["jogo"]]]
    return "SUC REG_OK " +user + "\n"
#----

def list():
    return "LIST " + str([(i, users[i][1]) for i in users]) + '\n'
#----

def registered(socket):
    for i in users:
        if(users[i][0]==socket):
            return i
    return 0
#----

def reply(responce, myself):
    """
    quem convida comeca
    myself = convidado
    other = primeiro a jogar
    """

    myself = registered(myself)
    if(myself==0):
        return "ERR USER_UNKNOWN\n"
    if(users[myself][1]!=3):
        return "ERR NO_ENV\n"
    other = users[myself][2][0]
    if(other not in users):
       users[myself][1]=0
       return "ERR NO_USER\n"

    if(responce=='ACCEPT'):
        users[other][1]=4
        users[myself][1]=5
        users[myself][2][2]=[EMPTY_LINE.copy(), EMPTY_LINE.copy(), EMPTY_LINE.copy()]
        users[other][2][2]=users[myself][2][2]
        users[other][0].send("GAME START {}\n".format(myself).encode())
        users[other][0].send("BOARD 1 {}\n".format(users[other][2][2]).encode())
        users[myself][0].send("GAME START {}\n".format(other).encode())
        return "BOARD 0 {}\n".format(users[myself][2][2])
    elif(responce=='REJECT'):
        users[other][0].send("SUC REJECT {}\n".format(myself).encode())
        users[other][1]=0
        users[myself][1]=0
        return "SUC\n"
    else:
        raise ValueError("NEVER HAPPENS")
#----

def play(x, y, myself, extra=0):
    myself=registered(myself)
    if(myself==0):
        return "ERR USER_UNKNOWN\n"
    if(users[myself][1]==0 or users[myself][1]==2 or users[myself][1]==3):
        return "ERR NOT_IN_GAME\n"
    if(users[myself][1]==5 and extra==0):
        return "ERR NO_TURN\n"
    x=int(x)
    y=int(y)
    if(not (0<=x<=2 and 0<=y<=2) and extra== 0):
        return "ERR INVALID_COOR\n"

    if(users[myself][2][2][y][x]!=0 and extra == 0):
        return "ERR INVALID_PLAY {} {} {}\n".format(y,x,"X" if users[myself][2][2][y][x]==1 else "O")

    other=users[myself][2][0]
    play=1      #X
    
    if(extra!=0 and users[myself][1]!=0):
        users[myself][1]=0
        users[other][1]=0
        if(extra==1):
            users[other][0].send("GAME FOLD {}\n".format(myself).encode())
        elif(extra==2):
            users[other][0].send("ERR USER_DISCONECTED\n".encode())
        return "GAME LOSE\n"


    if(other==myself):
        other=users[myself][2][1]
        play=2  #O

    users[myself][2][2][y][x]=play
    estado=check(myself) 
    
    otherStatus=1
    myStatus=0

    if(estado==1):  #myself ganhou
        users[myself][1]=0
        users[other][1]=0
        users[myself][0].send("GAME WIN\n".encode())
        users[other][0].send("GAME LOSE\n".encode())
        otherStatus=2
        myStatus=2
    elif(estado==2):  #empate
        users[myself][1]=0
        users[other][1]=0
        users[myself][0].send("GAME TIE\n".encode())
        users[other][0].send("GAME TIE\n".encode())
        otherStatus=2
        myStatus=2
    else:
        users[myself][1]=5
        users[other][1]=4
    
    users[other][0].send("BOARD {} {}\n".format(otherStatus, users[other][2][2]).encode())
    return "BOARD {} {}\n".format(myStatus, users[myself][2][2])
#----

def check(user):
    """
    0=jogo
    1=vitoria
    2=empate
    """
    board=users[user][2][2]
    if(board[0][0]==board[0][1]==board[0][2]!=0 or \
       board[1][0]==board[1][1]==board[1][2]!=0 or\
       board[2][0]==board[2][1]==board[2][2]!=0 or\
       board[0][0]==board[1][0]==board[2][0]!=0 or\
       board[0][1]==board[1][1]==board[2][1]!=0 or\
       board[0][2]==board[1][2]==board[2][2]!=0 or\
       board[0][0]==board[1][1]==board[2][2]!=0 or\
       board[2][0]==board[1][1]==board[0][2]!=0):
        return 1

    for a in range(3):
        for b in range(3):
            if(board[a][b] == 0):
                return 0 
    return 2
#----


def invite(user, myself):
    myself = registered(myself)
    if(myself==0):
        return "ERR USER_UNKNOWN\n"
    if(users[myself][1]!=0):
        return "ERR IMBUSY\n"
    if(user not in users):
        return "ERR NO_USER\n"
    if(users[user][1]!=0):
        return "ERR USER_BUSY\n"
    users[myself][1]=2
    users[user][1]=3
    users[myself][2]=[myself, user, '?']
    users[user][2]=[myself, user, '?']
    users[user][0].send("INVITE {}\n".format(myself).encode())
    return "SUC INVITE_OK\n"
#----

def bad_format():
    return "ERR BAD_FORMAT\n"
#----


def process_input(msg, client):
    msg=msg.upper()
    msg=msg[:-1:]
    msg=msg.split(" ")
    print("Recieved >{}<".format(msg))

    if(msg[0]==''):
        return "OK\n"
    elif(msg[0]=="HELP" or msg[0]=='?'):
        return help()
    elif(msg[0]=="REGISTER" or msg[0]=='REG'):
        if(len(msg)==2):
            return register(msg[1], client)
        else:
            return bad_format()
    elif(msg[0]=="LIST" or msg[0]=='LS'):
        if(len(msg)==1):
            return list()
    elif(msg[0]=="INVITE" or msg[0]=='INV'):
        if(len(msg)==2):
            return invite(msg[1], client)
        else:
            return bad_format()
    elif(msg[0]=="PLAY"):
        if(len(msg)==3):
            return play(msg[1], msg[2], client)
        else:
            return bad_format()
    elif(msg[0]=='FOLD'):
        return play(0,0,client,1)
    elif(msg[0]=="ACCEPT" or msg[0]=="REJECT"):
         return reply(msg[0], client)
    elif(msg[0]=="EXIT" or  msg[0]=='X'):
        raise socket.timeout()

    
 
    return "ERR BAD_REQUEST\n"
#----



def handle_client_connection(client_sock):
    signal.pthread_sigmask(signal.SIG_SETMASK, [signal.SIGINT, signal.SIGKILL])
    try:
        with lock:
            connections.append(client_sock)
        while True:
            request=''
            #soma strings ate ter mensagem completa
            while(request=='' or request[-1]!='\n'):
                msg_from_client = client_sock.recv(1024)
                if(not msg_from_client):
                    raise socket.timeout()
                request += str(msg_from_client.decode())
            with lock:
                client_sock.send(process_input(request, client_sock).encode())
    except socket.timeout:
        with lock:
            for i in users:
                if(users[i][0]==client_sock):
                    if(users[i][1]!=0):
                        play(0,0,client_sock,2) #send user disconected signal to game handler
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

