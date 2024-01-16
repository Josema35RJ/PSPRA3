import socket
import time
# Se establece la conexion
s = socket.socket()
s.connect(("localhost", 9999))

# Se envia "hola"
s.send("hola".encode())
# Se recibe la respuesta y se escribe en pantalla
datos = s.recv(1024)
print (datos.decode())   
# Espera de 2 segundos
time.sleep(10)    
# Se envia "adios"
s.send("adios".encode())    
# Se espera respuesta, se escribe en pantalla y se cierra la
# conexion
datos = s.recv(1024)
print (datos.decode())
s.close()

