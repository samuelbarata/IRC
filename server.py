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
REG_FAIL            = "Username already in use, pick a different one"
NO_USER             = "No such user exists, LIST all users and pick a valid user"
USER_BUSY           = "User is busy, LIST all users to check their status"
INVALID_COOR        = "Invalid Coordinates, valid {0,1,2}"
INVALID_PLAY        = "{} already has {}"
USER_DISCONECTED    = "Oponent has left the game, you win"
NOT_IN_GAME         = "This command is only valid during a game type HELP to see how to start a new game"
SERVER_OFF          = "The server will exit and you'll be disconnected automatically"

#mensagens ok:
SUC                 = "OK "
REG_OK              = "Registado com sucesso"
INVITE_OK           = "Waiting for reply..."
ACEPT               = "{} has acepted your request"
REJECT              = "{} has rejected your request"
WAITING_FOR_PLAY    = "Not your turn to play"
WIN                 = "Congratulations, you have won"
LOSE                = "Better luck next time"
TIE                 = "Tie"

users ={} #user: [socketfd, status]
server = 0


def exit_server(sig, frame):
    print("\nEXITing server recieved signal {}, on {}".format(sig, frame))
    server.close()
    for user in users:
        users[user][0].send(SERVER_OFF.encode())
        socket.close(users[user][0])
    exit(0)

def process_input(msg):
    #return "OLA"
    return "BOARD [[0,0,0],[0,1,2],[0,0,0]]"




def handle_client_connection(client_sock):
    signal.pthread_sigmask(signal.SIG_SETMASK, [signal.SIGINT, signal.SIGKILL])
    try:
        while True:
            request=''
            #soma strings ate ter mensagem completa
            while(request=='' or request[-1]!='\n'):
                msg_from_client = client_sock.recv(1024)
                request += msg_from_client.decode()
            client_sock.send(process_input(request).encode())
    except:
        client_sock.close()
        print("Client disconected".format(client_sock))
        exit(0)





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

if(__name__ == '__main__'):
    main()

