#!/usr/bin/python3

from socket import*
import sys
import math
import http.client
import struct
import time
import os
import _thread


##########################################
##  Alumno: Victor Miguel Mora Alcazar  ## 
##     Laboratorio: G4                  ##         
##########################################

    #### Gymkana para REDES II ####

direccion_servidor = 'atclab.esi.uclm.es'

puertoProxy = 5897

recvTamaño = 1024

# Metodos para obtener los datos necesarios #

def datoE1(instrucciones):

	aux = (str(instrucciones)).split("'")

	aux1 = (str(aux[1])).split("\\n") 

	codigo = ((aux1[0]+ ' 5897').encode('utf-8'))

	return codigo

def datoE2(instrucciones):

	aux = (str(instrucciones)).split('"')

	aux1 = (str(aux[1])).split("\\n")

	puerto = int(aux1[0])

	return puerto

def datoE3(instrucciones):

	aux = (str(instrucciones)).split("'")

	aux1 = (str(aux[1])).split("\\n")

	clave = ('/'+(aux1[0]))

	return clave

def datoE4(instrucciones):

	aux = (str(instrucciones)).split('"')

	aux1 = (str(aux[1])).split("\\n")

	dato_icmp = aux1[0]

	return dato_icmp

def datoE5(instrucciones):

	aux = (str(instrucciones)).split("\n")

	dato_proxy = aux[0]

	codigo = dato_proxy + " " + str(puertoProxy)

	return codigo

def respuestaE5(instrucciones):

	direccion = (instrucciones.split('/')[2].split('\n')[0].strip())

	return direccion


# Mostrar las instrucciones de los pasos siguientes #

def mostrarInstrucciones (mensaje):

	print ((str(mensaje)).replace('\\n','\n'))



# Paso 0: Establecer la conexión #

def etapa1():

	sock = socket(AF_INET,SOCK_STREAM)

	sock.connect((direccion_servidor,2000))

	instrucciones = sock.recv(recvTamaño)

	mostrarInstrucciones (instrucciones)


# Paso 1: Crear servidor UDP, puerto 5897 #

	serverUDP = socket(AF_INET, SOCK_DGRAM)

	serverUDP.bind(('', 5897))

	serverUDP.sendto(datoE1(instrucciones), (direccion_servidor, 2000))

	respuesta = serverUDP.recv(recvTamaño)

	mostrarInstrucciones (respuesta)

	serverUDP.close()

	return respuesta


# Paso 2: Evaluar aritmeticamente operaciones #

def etapa2 (respuesta):

	sock = socket(AF_INET,SOCK_STREAM)

	puerto = datoE2(respuesta)

	sock.connect((direccion_servidor, puerto))

	def sustituir(string):
		string = string.replace(' ', '')
		string = string.replace('{', '(')
		string = string.replace(']', ')')
		string = string.replace('[', '(')
		string = string.replace('}', ')')	
		    
		return string

	def operar(operacion, segundo, primero):
		if operacion == '+':
		    return (primero + segundo)
		elif operacion == '-':
		    return (primero - segundo)
		elif operacion == '*':
		    return (primero * segundo)
		elif operacion == '/':
		    return math.floor(primero / segundo)
		
	def preceden(primera, segunda):
		if segunda == '(' or segunda == ')':
		    return False
		elif (primera == '*' or primera == '*') and (segunda == '+' or segunda == '-'):
		    return False
		else:
		    return True

	def evaluar(string):    
		val = list(string)
		
		ops = []
		valores = []
		i = 0
		while i < len(val):
		    if val[i] >= '0' and val[i] <= '9':
		        numero = ""
		        while(i < len(val) and val[i] >= '0' and val[i] <= '9'):
		            numero += val[i]
		            i += 1
		        
		        valores.append(int(numero))
		        i -= 1
		        
		    elif val[i] == '(':
		        ops.append(val[i])
		    
		    elif val[i] == ')':
		        while len(ops) > 1 and len(valores) > 1 and ops[-1] != '(':
		            valores.append(operar(ops.pop(), valores.pop(), valores.pop()))
		            ops.pop()
		            
		    elif val[i] == '+' or val[i] == '-' or val[i] == '*' or val[i] == '/':
		        while len(ops) != 0 and len(valores) > 1 and preceden(val[i], ops[-1]):
		            valores.append(operar(ops.pop(), valores.pop(), valores.pop()))
		            
		        ops.append(val[i])
		    
		    i += 1
		    
		while len(ops) != 0 and len(valores) > 1:
		    valores.append(operar(ops.pop(), valores.pop(), valores.pop()))
		
		if len(valores) > 0:
		    numero = valores.pop()
		    return(numero)
		else:
		    return 0

	respuesta = True
	operaciones = sock.recv(recvTamaño)
	while respuesta:
		operaciones = sustituir((str(operaciones)).strip("b'"))
		print("Operacion: " + str(operaciones))
		while operaciones.count('(') != operaciones.count(')'):
		    opSiguiente = sock.recv(recvTamaño)
		    operaciones += sustituir((str(opSiguiente)).strip("b'"))
		
		sock.sendto(("(" + str(evaluar(operaciones)) + ")").encode('utf-8'), (direccion_servidor, puerto))
		print("Solucion: " + "(" + str(evaluar(operaciones)) + ")")

		operaciones = sock.recv(recvTamaño)
		
		respuesta = False if (str(operaciones).find("step") > -1 or str(operaciones).find("ERROR")) >     -1 else True
		    
		
	mostrarInstrucciones (operaciones)

	return operaciones


# Paso 3: Cliente http #

def etapa3(operaciones):                            
	 
	conexion = http.client.HTTPConnection(direccion_servidor,5000)

	conexion.request('GET', datoE3(operaciones)) 

	respuesta = conexion.getresponse()

	instrucciones = respuesta.read()

	mostrarInstrucciones (instrucciones)
	
	return instrucciones	
	

# Paso 4: ICMP Echo Request #

def etapa4(instrucciones):
	
	dato_icmp = datoE4(instrucciones)

 # Fragmento copiado: https://bitbucket.org/arco_group/python-net/raw/72d7cd022ebaa1fdfdaeb4f35d4ae666874d38f1/raw/icmp_checksum.py
 # Autor: David Villa Alises

	def cksum(data):

		def sum16(data):
		    "sum all the the 16-bit words in data"
		    if len(data) % 2:
		        data += b'\0'

		    return sum(struct.unpack("!%sH" % (len(data) // 2), data))

		retval = sum16(data)                       # sum
		retval = sum16(struct.pack('!L', retval))  # one's complement sum
		retval = (retval & 0xFFFF) ^ 0xFFFF        # one's complement
		return retval


	header = struct.pack("!BBHHH",8,0,0,0,0)

	timestamp= struct.pack('!d',time.time())

	paqueteIncompleto = header+timestamp+dato_icmp.encode('utf-8')

	checksum=cksum(paqueteIncompleto)

	paqueteCompleto = struct.pack("!BBHHH",8,0,checksum,0,0)+timestamp+(dato_icmp).encode('utf-8')

	sock = socket(AF_INET,SOCK_RAW,getprotobyname('icmp'))

	sock.sendto(paqueteCompleto, (direccion_servidor, 80))

	sock.recv(recvTamaño)

	respuesta = (sock.recv(recvTamaño)[36:]).decode()

	print(respuesta)	

	return respuesta


# Paso 5: Proxy web #

def etapa5(respuesta):

	def preparado (direccion_servidor, puertoProxy, recvTamaño):

		sock = socket(AF_INET, SOCK_STREAM)

		sock.connect((direccion_servidor, 9000))

		codigo = datoE5(respuesta)	
		
		sock.sendto(codigo.encode('utf-8'), (direccion_servidor, 2000))

		respuestaEspera = sock.recv(recvTamaño).decode()
				
		print(respuestaEspera)
		    
		
	def listen(conexion, recvTamaño):
		
		respuesta = conexion.recv(recvTamaño).decode()

		sockCliente = socket(AF_INET, SOCK_STREAM)

		direccion = respuestaE5(respuesta)
		
		sockCliente.connect((direccion, 80))

		sockCliente.send(respuesta.encode('utf-8'))
		
		while 1:
			dato = sockCliente.recv(recvTamaño)
				    
			if (len(dato)):
				conexion.send(dato)
			else:
				break
				    
		conexion.close()		
		sockCliente.close()


	proxy = socket(AF_INET, SOCK_STREAM)

	proxy.bind(('', puertoProxy))

	proxy.listen(30)
		
	_thread.start_new_thread(preparado, (direccion_servidor, puertoProxy, recvTamaño))
		
	while 1:
		conexion, address = proxy.accept()
		_thread.start_new_thread(listen, (conexion, recvTamaño))
		
	proxy.close()


# --------------------------------------------------------------------------------------------------------------- #


## EJECUCIÓN DE LA GYMKANA ##

respuestaE1 = etapa1() # Etapa 0 y 1

respuestaE2 = etapa2(respuestaE1) # Etapa 2

respuestaE3 = etapa3 (respuestaE2) # Etapa 3

respuestaE4 = etapa4(respuestaE3) # Etapa 4

etapa5(respuestaE4) # Etapa 5






	
