import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("", 9999))
server.listen(1)

socket_cliente, datos_cliente = server.accept()
print ("Conectado "+str(datos_cliente))

# Bucle indefinido hasta que el cliente envie "adios"
while True:
   # Espera por datos
   peticion = socket_cliente.recv(1024).decode()
   # Contestacion a "hola"
   if ("hola"==peticion):
       print (str(datos_cliente)+ " envia hola: contesto")
       socket_cliente.send("Hola Amigo".encode())
       
   # Contestacion y cierre a "adios"
   if ("adios"==peticion):
       print (str(datos_cliente)+ " envia adios: contesto y desconecto")
       socket_cliente.send("Adiós Amigo".encode())
       socket_cliente.close()
       print ("desconectado "+str(datos_cliente))
       break
          
