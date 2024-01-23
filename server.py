import socket
import hashlib
import os
import threading
from cryptography.fernet import Fernet
from colorama import Fore, Style
import base64
from questions import questions

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
                    conn.send("El correo electrónico ya está registrado.".encode())
                    return
        if opcion == '2':
            with open('usuarios.bin', 'ab') as f:
                f.write(encriptar_mensaje(email + ',' + hash_password(contrasena), clave) + b'\n')
                conn.send("OK".encode())
                return True
        conn.send("Correo electrónico o contraseña incorrectos.".encode())
    return False
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
                if client in self.clients:  # Verifica si el cliente aún está conectado
                    message = client.recv(1024)
                    self.broadcast(message)
                else:
                    break
            except:
                if client in self.clients:
                    index = self.clients.index(client)
                    self.clients.remove(client)
                    client.close()
                    nickname = self.nicknames[index]
                    self.nicknames.remove(nickname)
                    self.broadcast(f'{nickname} left the game!'.encode('ascii'))
                break



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

    def enviar_pregunta(self, client, pregunta):
     opciones = '\n'.join([f"{i}. {opcion}" for i, opcion in enumerate(pregunta['options'])])
     client.send(f"{pregunta['question']}\n{opciones}".encode('utf-8'))

    def start(self):
        print(Fore.GREEN + "Servidor iniciado!" + Style.RESET_ALL)
        self.server.listen()
        self.receive()

if __name__ == "__main__":
    server = TriviaServer()
    server.start()
