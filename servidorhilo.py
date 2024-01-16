from threading import Thread
import socket

class Cliente(Thread):
    def __init__(self, socket_cliente, datos_cliente, codigo_cliente):
        Thread.__init__(self)
        self.socket = socket_cliente
        self.datos = datos_cliente
        self.codigo=codigo_cliente
      
    def run(self):
      seguir = True
      while seguir:
         peticion = self.socket.recv(1000).decode()
         
         if ("hola"==peticion):
             print ("Cliente "+str(self.codigo)+str(self.datos)+ " envia hola: contesto")
             self.socket.send("pues hola".encode())
             
         if ("adios"==peticion):
             print ("Cliente "+str(self.codigo)+str(self.datos)+ " envia adios: contesto y desconecto")
             self.socket.send("pues adios".encode())
             self.socket.close()
             print ("Cliente "+str(self.codigo)+" desconectado "+str(self.datos))
             seguir = False

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("", 9999))
server.listen(1)
codigo_cliente=1
# bucle para atender clientes
while 1:
    # Se espera a un cliente
    socket_cliente, datos_cliente = server.accept()
    # Se escribe su informacion
    print ("conectado "+str(datos_cliente))
    hilo = Cliente(socket_cliente, datos_cliente, codigo_cliente)
    hilo.start()
    codigo_cliente+=1

      
