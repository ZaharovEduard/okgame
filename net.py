import socket
import sys
import time
import threading
import select

REFRESH_TIME = 1
TIMEOUT = 20
BYTES_IN_HEADER = 8 # b'00000000' -> 41 bytes

def send_message_to(messenger, name, message):
    message = ' '.join(message)
    message = message.encode('utf-8')  

    mess_size = len(message)
    str_size = str(mess_size).encode('utf-8')
    len_head = len(str_size)
    if len_head > 8:
        return # message length is too long.   exception needed really
    header = b'0'*(8 - len_head) + str_size
  
    if name in messenger.named_connects: 
        _, wr, _ = select.select([],[messenger.named_connects[name].connection],[],TIMEOUT)
        if wr:
            messenger.named_connects[name].connection.send(header+message)

class Messenger(threading.Thread):
    def __init__(self, out_queue, port, max_clients):
        super(Messenger, self).__init__()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.socket.setblocking(0)
        self.socket.bind((socket.gethostname(), port))
        self.socket.listen(max_clients)
        
        self.named_connects = {}
        self.connections = []
        self.out_queue = out_queue

        self.runn = False

    def run(self):
        self.runn = True
        while self.runn:  
            sock, _, _ = select.select([self.socket],[],[],REFRESH_TIME)           
            #print(new_conn)
            if sock:
                conn, addr = self.socket.accept()
                conn_thr = Connection(self, conn) 
                self.connections.append(conn_thr)
                conn_thr.start()
                print('connection to '+str(addr))

            
        for connect in self.connections:
            connect.runn = False
            connect.connection.close()        
        self.socket.close()

class Connection(threading.Thread):
    def __init__(self, owner, connection):
        super(Connection, self).__init__()
        self.owner = owner
        self.connection = connection
        self.runn = False
        self.client_name = False

    def run(self):
        self.runn = True
        while self.runn:
            con, _, _ = select.select([self.connection],[],[], TIMEOUT)
            if con:
                try:
                    header = self.connection.recv(BYTES_IN_HEADER)
                    if header == b'':
                        break
                    n_symbols = int(header.decode())
                    rcvd_data = self.connection.recv(n_symbols)
                    rcvd_data = rcvd_data.decode().split()
                except:
                    print('unexpected message')
                    break
                if len(rcvd_data) > 2:
                    if  not self.client_name:
                        #print('setting name')
                        self.client_name = rcvd_data[0]
                        #print(self.client_name)
                        self.owner.named_connects[self.client_name] = self
                    self.owner.out_queue.put(rcvd_data)
                    #print(self.client_name)  
                else:
                    continue
            else:
                print('connection closed because of timeout')
                self.runn = False
                break
            #print('data received')
        if self in self.owner.connections:
            self.owner.connections.remove(self)
            self.connection.close() 
            print('connection removed from list of connections')
        if self.client_name:    
            #self.owner.out_queue.put(['leave_game', self.client_name])
            if self.client_name in self.owner.named_connects:
                del self.owner.named_connects[self.client_name]
                #print('connection removed from connections dict')
        print('end')   
