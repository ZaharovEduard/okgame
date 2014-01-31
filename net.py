import socket
import sys
import time
import threading
import select

REFRESH_TIME = 1
TIMEOUT = 20

def send_message_to(messenger, name, message):
    message = ' '.join(message)
    message = message.encode('utf-8')    
    if name in messenger.named_connects: 
        print(message)
        _, wr, _ = select.select([],[messenger.named_connects[name].connection],[],TIMEOUT)
        if wr:
            messenger.named_connects[name].connection.send(message)
            print(message)    


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
                print(self.connections)
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
            print(con)
            if con:
                try:
                    print('asda')
                    rcvd_data = self.connection.recv(1024)
                    if rcvd_data == b'':
                        break
                    print(rcvd_data)
                    rcvd_data = rcvd_data.decode().split()
                    print(rcvd_data)
                except:
                    print('unexpected message')
                    break
                if len(rcvd_data) > 2:
                    if rcvd_data[2] == 'register':
                        self.connection.send(b'ok')
                    if  not self.client_name:
                        print('setting name')
                        self.client_name = rcvd_data[0]
                        print(self.client_name)
                        self.owner.named_connects[self.client_name] = self
                    self.owner.out_queue.put(rcvd_data)
                    print(self.client_name)  
                else:
                    continue
            else:
                print('connection closed because of timeout')
                self.runn = False
                break
            print('data received')
        if self in self.owner.connections:
            self.owner.connections.remove(self)
            self.connection.close() 
            print('connection removed from list of connections')
        if self.client_name:
            if self.client_name in self.owner.named_connects:
                del self.owner.named_connects[self.client_name]
                print('connection removed from connections dict')
        print('end')   
