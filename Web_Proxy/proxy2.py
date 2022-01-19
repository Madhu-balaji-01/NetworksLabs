# 50.012 network lab 1
# Harshit Garg, 1004422

import socket
import sys, os
import _thread as thread

proxy_port=12000
cache_directory = "./cache/"

def client_thread(clientFacingSocket):

  clientFacingSocket.settimeout(5.0)

  try:
    message = clientFacingSocket.recv(4096).decode()
    msgElements = message.split()
    print(msgElements[0].upper())
    
    if len(msgElements) < 5 or msgElements[0].upper() != 'GET' or 'Range:' in msgElements:
      # print("non-supported request: " , msgElements)
      clientFacingSocket.close()
      return

    # Extract the following info from the received message
    #   webServer: the web server's host name
    #   resource: the web resource requested
    #   file_to_use: a valid file name to cache the requested resource
    #   Assume the HTTP reques is in the format of:
    #      GET http://www.mit.edu/ HTTP/1.1\r\n
    #      Host: www.mit.edu\r\n
    #      User-Agent: .....
    #      Accept:  ......

    resource = msgElements[1].replace("http://","", 1)
  
    hostHeaderIndex = msgElements.index('Host:')
    webServer = msgElements[hostHeaderIndex+1]

    port = 80

    print("webServer:", webServer)
    print("resource:", resource)

    message=message.replace("Connection: keep-alive","Connection: close")
    
    website_directory = cache_directory + webServer.replace("/",".") + "/"

    if not os.path.exists(website_directory):
      os.makedirs(website_directory)
    
    
    file_to_use = website_directory + resource.replace("/",".")


  except:
    print(str(sys.exc_info()[0]))                                                
    clientFacingSocket.close()
    return
    
  # Check wether the file exists in the cache
  try:
    with open(file_to_use, "rb") as f:
      # ProxyServer finds a cache hit and generates a response message
      print("Found: Served from the cache")
      while True:
        buff = f.read(4096)
        if buff:
          clientFacingSocket.send(buff)
          print("Reading from cache file")  
        else:
          break

  except FileNotFoundError as e:
    try:        
      # Create a socket on the proxyserver
      serverFacingSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      # Connect to the socket to port 80
      serverFacingSocket.connect((webServer, port))
      print("connected to {webServer}")
      print(message)
      serverFacingSocket.send(message.encode())


      with open(file_to_use, "wb") as cacheFile:
        while True:
          buff = serverFacingSocket.recv(4096)
        
          if buff:
            print(buff)
            cacheFile.write(buff)
            print("New Website: Wrote cache file")
            clientFacingSocket.send(buff)
            print("Forwarded to the client")
          else:
            break
        print("Close cache file")
    except:
      print(str(sys.exc_info()[0]))                                                
    finally:
      serverFacingSocket.close()
      print("Close connection to server")
      
  except:
    print(str(sys.exc_info()[0]))

  finally:
    clientFacingSocket.close()
    print("Close client socket")


if len(sys.argv) > 2:
  print('Usage : "python proxy.py port_number"\n')
  sys.exit(2)
if len(sys.argv) == 2:
  proxy_port = int(sys.argv[1])

if not os.path.exists(cache_directory):
  os.makedirs(cache_directory)
  
# Create a server socket, bind it to a port and start listening
welcomeSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
welcomeSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
welcomeSocket.bind(("localhost", proxy_port))
welcomeSocket.listen(1)

print('Proxy ready to serve at port', proxy_port)

try: 
  while True:
    # Start receiving data from the client
    clientFacingSocket, addr = welcomeSocket.accept()
    print('Received a connection from:', addr)
  
    # the following function starts a new thread, taking the function name as the first argument, and a tuple of arguments to the function as its second argument
    thread.start_new_thread(client_thread, (clientFacingSocket, ))

except KeyboardInterrupt:
  print('bye...')

finally:
    welcomeSocket.close()
    print('Closed')