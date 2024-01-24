import socket
import re
import inquirer
from colorama import Fore, Style
from tqdm import tqdm
import time

HOST = '10.10.1.14'
PORT = 1234

client_socket = socket.socket()
client_socket.connect((HOST, PORT))

def ingresar_credenciales():
    questions = [
        inquirer.Text('email', message="Ingrese su correo electrónico", validate=lambda _, x: re.match(r"[^@]+@[^@]+\.[^@]+", x) is not None),
        inquirer.Password('contrasena', message="Ingrese su contraseña")
    ]
    answers = inquirer.prompt(questions)
    return f"{answers['email']},{answers['contrasena']}"

def iniciar_sesion_o_registrarse():
    ingresado_con_exito = False
    while not ingresado_con_exito:
        questions = [
            inquirer.List('opcion',
                          message="Seleccione una opción",
                          choices=['Iniciar sesión', 'Registrarse'],
                          ),
        ]
        answers = inquirer.prompt(questions)
        opcion = '1' if answers['opcion'] == 'Iniciar sesión' else '2'
        credenciales = ingresar_credenciales()
        client_socket.send(f"{opcion},{credenciales}".encode())
        respuesta = client_socket.recv(1024).decode()
        if respuesta == "OK":
            print(Fore.GREEN + "Operación exitosa." + Style.RESET_ALL)
            ingresado_con_exito = True
        else:
            print(Fore.RED + respuesta + Style.RESET_ALL)

iniciar_sesion_o_registrarse()

# Espera la confirmación del servidor antes de solicitar el apodo
confirmacion = client_socket.recv(1024).decode()
if confirmacion == "NICK":
    nickname = input("Ingrese su apodo: ")
    client_socket.send(nickname.encode())

while True:
    try:
        message = client_socket.recv(1024).decode()
        if message.endswith('?'):  # Si el mensaje termina con un signo de interrogación, es una pregunta
            print(Fore.GREEN + message + Style.RESET_ALL)
            answer = input("Ingrese el número de su respuesta: ")
            client_socket.send(answer.encode())
        elif message.endswith('!'):
            print(Fore.YELLOW + message + Style.RESET_ALL)
        else:  # Si no, es un mensaje normal 
            print(Fore.YELLOW + message + Style.RESET_ALL)
    except Exception as e:
        print(f"Error: {e}")
        break

client_socket.close()
