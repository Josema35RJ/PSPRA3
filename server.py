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
                # Selecciona una pregunta aleatoria
                pregunta = random.choice(questions)
                questions.remove(pregunta)

                # Envía la pregunta al cliente
                self.enviar_pregunta(client, pregunta)

                # Recibe la respuesta del cliente
                respuesta = client.recv(1024).decode('utf-8')

                # Verifica si la respuesta es correcta
                acertado = self.verificar_respuesta(respuesta, pregunta)
                if acertado:
                    self.scores[self.nicknames[self.clients.index(client)]] += 1

                # Envía feedback al cliente
                feedback = "Correcto!" if acertado else "Incorrecto."
                client.send(feedback.encode('utf-8'))

                # Envía la puntuación actual al cliente
                puntuacion = self.scores[self.nicknames[self.clients.index(client)]]
                client.send(f"Tu puntuación actual es {puntuacion}.".encode('utf-8'))

                if len(questions) == 0:
                    break
            except:
              break
    def enviar_pregunta(self, client, pregunta):
        mensaje = pregunta['question'] + '\n' + '\n'.join(pregunta['options'])
        client.send(mensaje.encode('utf-8'))

    def verificar_respuesta(self, respuesta, pregunta):
        return respuesta == pregunta['answer']

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
                    self.broadcast(f"{nickname} se uniÃ³ al juego!".encode('utf-8'))
                    client.send('Conectado al servidor!'.encode('ascii'))

                    thread = threading.Thread(target=self.handle, args=(client,))
                    thread.start()
            else:
                print(Fore.GREEN + "El juego ha comenzado!" + Style.RESET_ALL)
                for i in range(5):
                    pregunta = questions[i]
                    self.broadcast(("Pregunta {}: {}\n{}".format(i+1, pregunta['question'], '\n'.join(pregunta['options']))).encode('utf-8'))
                    for client in self.clients:
                        self.enviar_pregunta(client, pregunta)
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
