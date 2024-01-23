import socket
import threading
import random
from questions import questions
from colorama import Fore, Style
from server import login_usuario
import inquirer


class TriviaServer:
    def __init__(self, host = 'localhost', port = 9999):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.clients = []
        self.nicknames = []
        self.scores = {}

    def broadcast(self, message):
        for client in self.clients:
            client.send(message)

    def handle(self, client):
        while True:
            try:
                message = client.recv(1024)
                self.broadcast(message)
            except:
                index = self.clients.index(client)
                self.clients.remove(client)
                client.close()
                nickname = self.nicknames[index]
                self.nicknames.remove(nickname)
                self.broadcast(f'{nickname} left the game!'.encode('ascii'))
                break
    def enviar_pregunta(self, client, pregunta):
     client.send(pregunta['question'].encode('utf-8'))
     opciones = [inquirer.List('respuesta',
                               message=pregunta['question'],
                               choices=pregunta['options'])]
     respuesta = inquirer.prompt(opciones)
     client.send(respuesta['respuesta'].encode())
    
    def receive(self):
        while len(self.clients) < 1:
            client, address = self.server.accept()
            print(Fore.GREEN + f"Conexión establecida con {str(address)}" + Style.RESET_ALL)

            if login_usuario(client):
                client.send('NICK'.encode('ascii'))
                nickname = client.recv(1024).decode('ascii')
                self.nicknames.append(nickname)
                self.clients.append(client)

                print(Fore.GREEN + f"Apodo del cliente: {nickname}!" + Style.RESET_ALL)
                self.broadcast(f"{nickname} se unió al juego!".encode('utf-8'))
                client.send('Conectado al servidor!'.encode('ascii'))

                # Envía la primera pregunta al cliente
                self.enviar_pregunta(client, questions[0])
            print(Fore.YELLOW + "Jugadores en el juego:" + Style.RESET_ALL)
            for nick in self.nicknames:
                print(nick)

            thread = threading.Thread(target=self.handle, args=(client,))
            thread.start()

        print(Fore.GREEN + "El juego ha comenzado!" + Style.RESET_ALL)

    def start(self):
        print(Fore.GREEN + "Servidor iniciado!" + Style.RESET_ALL)
        self.server.listen()
        self.receive()

server = TriviaServer()
server.start()
