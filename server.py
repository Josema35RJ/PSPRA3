import socket
import hashlib
import os
import threading
from cryptography.fernet import Fernet
from colorama import Fore, Style
import base64
from questions import questions
import random
import json

def hash_password(password):
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return base64.b64encode(salt + key).decode('utf-8')

def verify_password(stored_password, provided_password):
    stored_password = base64.b64decode(stored_password.encode('utf-8'))
    salt = stored_password[:32]
    stored_key = stored_password[32:]
    key = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt, 100000)
    return stored_key == key

def cargar_clave():
    return open("clave.key", "rb").read()

def encriptar_mensaje(mensaje, clave):
    f = Fernet(clave)
    mensaje_encriptado = f.encrypt(mensaje.encode('utf-8'))
    return mensaje_encriptado

def desencriptar_mensaje(mensaje_encriptado, clave):
    f = Fernet(clave)
    mensaje_desencriptado = f.decrypt(mensaje_encriptado).decode('utf-8')
    return mensaje_desencriptado

def login_usuario(conn):
    while True:
        clave = cargar_clave()
        opcion, email, contrasena = conn.recv(1024).decode().split(',')

        # Verifica si el archivo existe antes de abrirlo
        if not os.path.exists('usuarios.bin'):
            open('usuarios.bin', 'a').close()

        with open('usuarios.bin', 'rb') as f:
            usuarios = f.read().splitlines()
            for usuario in usuarios:
                correo, contrasena_guardada = desencriptar_mensaje(usuario, clave).split(',')
                if correo == email:
                    if opcion == '1' and verify_password(contrasena_guardada, contrasena):
                        conn.send("OK".encode())
                        return True
                    elif opcion == '2':
                        conn.send("El correo electrÃ³nico ya estÃ¡ registrado.".encode())
                        return False

            if opcion == '2':
                with open('usuarios.bin', 'ab') as f:
                    f.write(encriptar_mensaje(email + ',' + hash_password(contrasena), clave) + b'\n')
                    conn.send("OK".encode())
                    return True
            conn.send("Correo electrÃ³nico o contraseÃ±a incorrectos. IntÃ©ntalo de nuevo.".encode())


class TriviaServer:
    def __init__(self, host = 'localhost', port = 1234):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.clients = []
        self.nicknames = []
        self.scores = {}
        self.historial = {}

    def broadcast(self, message):
        for client in self.clients:
            client.send(message)

    def handle(self, client):
     while True:
        try:
            respuesta = client.recv(1024).decode('utf-8')
            self.enviar_pregunta(client, questions[0])
        except:
            index = self.clients.index(client)
            nickname = self.nicknames[index]
            self.clients.remove(client)
            client.close()
            self.nicknames.remove(nickname)
            break

    def enviar_pregunta(self, client, pregunta):
     # Crear el mensaje con la pregunta y las opciones
     mensaje = pregunta['question'] + '\n' + '\n'.join(pregunta['options'])
     # Enviar el mensaje al cliente
     client.send(mensaje.encode('utf-8'))
     # Recibir la respuesta del cliente
     respuesta = client.recv(1024).decode('utf-8')
     # Verificar si la respuesta es correcta
     # Informar al cliente de su puntuación actual
     client.send(f"Tu puntuación actual es {self.scores[self.nicknames[self.clients.index(client)]]}.".encode())
     # Añadir la pregunta, la respuesta y si fue correcta o no al historial del cliente
     #self.historial[self.nicknames[self.clients.index(client)]].append((pregunta['question'], respuesta, acertado))

    def receive(self):
        while True:
            if len(self.clients) < 2:
                print(Fore.YELLOW + "Esperando jugadores..." + Style.RESET_ALL)
                client, address = self.server.accept()
                print(Fore.GREEN + f"ConexiÃ³n establecida con {str(address)}" + Style.RESET_ALL)

                if login_usuario(client):
                    client.send('NICK'.encode('ascii'))
                    nickname = client.recv(1024).decode('ascii')
                    self.nicknames.append(nickname)
                    self.clients.append(client)
                    self.scores[nickname] = 0
                    self.historial[nickname] = []

                    print(Fore.GREEN + f"Apodo del cliente: {nickname}!" + Style.RESET_ALL)
                    pregunta_numero = random.randint(0, len(questions) - 1)
                    pregunta_texto = questions[pregunta_numero]['question']
                    self.broadcast(f"{nickname} se uniÃ³ al juego!".encode('utf-8'))
                    client.send('Conectado al servidor!'.encode('ascii'))

                    thread = threading.Thread(target=self.handle, args=(client,))
                    thread.start()
            else:
                print(Fore.GREEN + "El juego ha comenzado!" + Style.RESET_ALL)
                for i in range(len(questions)):
                    self.broadcast(("Pregunta {}: {}\n{}".format(i+1, pregunta_texto, '\n'.join(questions[pregunta_numero]['options']))).encode('utf-8'))
                    for client in self.clients:
                        pregunta_numero = random.randint(0, len(questions) - 1)
                        self.enviar_pregunta(client, questions[pregunta_numero]) 
                break

    def start(self):
        print(Fore.GREEN + "Servidor iniciado!" + Style.RESET_ALL)
        self.server.listen()
        self.receive()
        self.finalizar_juego()

    def finalizar_juego(self):
        max_score = max(self.scores.values())
        ganadores = [nick for nick, score in self.scores.items() if score == max_score]
        self.broadcast(f"El juego ha terminado. {'Empate' if len(ganadores) > 1 else 'Ganador'}: {', '.join(ganadores)}".encode('utf-8'))
        with open('historial.json', 'w') as f:
            json.dump(self.historial, f)

server = TriviaServer()
server.start()
