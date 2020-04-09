#!/bin/python3
import socket, signal, sys, select

server_ip = [socket.gethostbyname("samuel.freetcp.com"), "127.0.0.1"]
server_port = 45080
server = -1
MSG_SIZE = 1024
HLINE="  {}{}{}{}{}{}{}{}{}{}{}\n".format(chr(9472), chr(9472), chr(9472),chr(9532),chr(9472), chr(9472),
                                      chr(9472),chr(9532), chr(9472), chr(9472), chr(9472))
username=''

#mensagens erro:
ERR                 = "ERROR "
REG_FAIL            = "Username already in use, pick a different username"
NO_USER             = "No such user exists, LIST all users and pick a valid user"
USER_BUSY           = "User is busy, LIST all users to check their status"
INVALID_COOR        = "Invalid Coordinates, valid {0,1,2}"
INVALID_PLAY        = "{} {} already has {}"
USER_DISCONECTED    = "Oponent has left the game, you win"
NOT_IN_GAME         = "This command is only valid during a game type HELP to see how to start a new game"
SERVER_OFF          = "The server will exit and you'll be disconnected automatically"
BAD_REQUEST         = "Bad Request, type HELP to see available commands"
USER_UNKNOWN        = "User unregistered, you need to register before doing this action"
USER_REGISTERED     = "You are already registered"
IMBUSY              = "You are in the middle of a game"
NO_ENV              = "You dont have any invites pending"
NO_TURN             = "Not your turn to play"



#mensagens ok:
SUC                 = "OK "
REG_OK              = "Registado com sucesso"
INVITE_OK           = "Waiting for reply..."
INVITE_REC          = "You've been invited to play by {} ACCEPT | REJECT"
ACEPT               = "{} has acepted your request"
REJECT              = "{} has rejected your request"
WAITING_FOR_PLAY    = "Not your turn to play"
WIN                 = "Congratulations, you have won"
LOSE                = "Better luck next time"
TIE                 = "Tie"
START               = "Game started against {}"

def exit_sig(sig=0, frame=0):
    client.close()
    exit(0)
#----

def process_input(server_msg):
    """
    Recieves the server Message, returned value will be sent to server
    """
    global username
    original=server_msg
    server_msg=server_msg.split(" ")    #separa por args

    if(server_msg[0]=="DISPLAY"):
        print(original[8::])


    elif(server_msg[0]=="SUC"):
        if(len(server_msg)>1):
            if(server_msg[1]=="REG_OK"):
                username='[' + server_msg[2].lower() + ']'
                print(REG_OK)
            elif(server_msg[1]=='INVITE_OK'):
                print(INVITE_OK)
            elif(server_msg[1]=='REJECT'):
                print(REJECT.format(server_msg[2]))

    elif(server_msg[0]=='GAME'):
        if(server_msg[1]=='START'):
            print(START.format(server_msg[2]))
        elif(server_msg[1]=='WIN'):
            print(WIN)
        elif(server_msg[1]=='LOSE'):
            print(LOSE)
        elif(server_msg[1]=='TIE'):
            print(TIE)


    elif(server_msg[0]=="ERR"):
        if(server_msg[1]=="BAD_REQUEST"):
            print(BAD_REQUEST)
        elif(server_msg[1]=="REG_FAIL"):
            print(REG_FAIL)
        elif(server_msg[1]=="USER_REGISTERED"):
            print(USER_REGISTERED)
        elif(server_msg[1]=='USER_BUSY'):
            print(USER_BUSY)
        elif(server_msg[1]=='USER_UNKNOWN'):
            print(USER_UNKNOWN)
        elif(server_msg[1]=='IMBUSY'):
            print(IMBUSY)
        elif(server_msg[1]=='NO_USER'):
            print(NO_USER)
        elif(server_msg[1]=='NO_ENV'):
            print(NO_ENV)
        elif(server_msg[1]=='NOT_IN_GAME'):
            print(NOT_IN_GAME)
        elif(server_msg[1]=='NO_TURN'):
            print(NO_TURN)
        elif(server_msg[1]=='REG_FAIL'):
            print(REG_FAIL)
        elif(server_msg[1]=='INVALID_PLAY'):
            print(INVALID_PLAY.format(server_msg[2], server_msg[3], server_msg[4]))

    
    elif(server_msg[0]=="INVITE"):
        print(INVITE_REC.format(server_msg[1]))



    elif(server_msg[0]=="BOARD"):
        if(server_msg[1]=='1'):
            print("\n\nYour turn to play\n")
        elif(server_msg[1]=='0'):
            print("\n\nWaiting for oponent...\n")
        board=eval(original[8::])
        for i in range(len(board)):
            for k in range(len(board[i])):
                if(board[i][k]==0):
                    board[i][k]=' '
                elif(board[i][k]==1):
                    board[i][k]='X'
                else:
                    board[i][k]='O'
        print("\n   0   1   2  \n"\
            +"0  {} | {} | {} \n".format(board[0][0], board[0][1], board[0][2])\
            +HLINE\
            +"1  {} | {} | {} \n".format(board[1][0], board[1][1], board[1][2])\
            +HLINE\
            +"2  {} | {} | {} \n".format(board[2][0], board[2][1], board[2][2]))

    elif(server_msg[0]=="LIST"):
        all_users=eval(original[5::])
        print("USER\t|\tSTATUS")
        for i in all_users:
            print("{}\t|\t{}".format(i[0], "available" if i[1] == 0 else "unavailable"))
        print("\n")

    elif(server_msg[0]=="SERVER_OFF"):
        print('\n' + SERVER_OFF + '\n\n')
        exit_sig()
    sys.stdout.flush()
#----



while(not 0<=server<len(server_ip)):
    server = int(input("Select server:\n0: Remote Server\n1: Localhost\n"))

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client.connect((server_ip[server], server_port))
except:
    print("ERROR: Server {} is offline".format(server_ip[server]))
    client.close()
    exit(1)

signal.signal(signal.SIGINT, exit_sig)
inputs = [client, sys.stdin]
message=''
print("COMMAND: ",  end='')
sys.stdout.flush()
while True:
    ins, outs, exs = select.select(inputs, [], [])
    for i in ins:
        if(i==sys.stdin):
            response=sys.stdin.readline()
            client.sendto(response.encode(),(server_ip[server],server_port))
        elif(i==client):
            (server_msg, addr) = client.recvfrom(MSG_SIZE)
            if(not server_msg):
                exit_sig()
            message+=str(server_msg.decode())
            if(message[-1]!='\n'):
                continue
            message=message.split('\n')
            for k in message:
                process_input(k)
            message=''
            print("{}COMMAND: ".format(username), end='')
            sys.stdout.flush()

