import sys
import socket
import select
import queue
from queue import Full, Empty
import threading
#from multiprocessing import Process
#from Queue import Full, Empty
import time
import pygame as pg
import hud

REF_RATE = 70
TIMEOUT = 10
SIZE = (800,600)
BYTES_IN_HEADER = 8

class Receiver(threading.Thread):
    def __init__(self, socket, in_queue):
        super(Receiver,self).__init__()
        self.socket = socket
        self.in_queue = in_queue
    
    def recv_data(self):
        read_sock, _, _ = select.select([self.socket],[],[],TIMEOUT)
        player_data = ''
        if read_sock:
            header = self.socket.recv(BYTES_IN_HEADER)
            if header == b'':
                return False
            n_bytes = int(header.decode())
            data = self.socket.recv(n_bytes).decode()
            return data        
        else:
            return False            

    def recv_inits(self):
        field_data = self.recv_data()
        if not field_data:
            return False
        field_size = self.unpack_field_info(field_data)
        if not field_size:
            return False
        return field_size

    def unpack_field_info(self, f_info):
        info = f_info.split()
        if info == ['not_logged']:
            return False
        else:
            return (int(info[0]), int(info[1]))

    def unp_game_items_info(self, items_raw):
        #items_raw = items_info.split()
        game_items = [items_raw[i:i+4] for i in range(0,len(items_raw),4)]
        for item in game_items:
            item[1], item[2], item[3] = int(item[1]), int(item[2]), int(item[3]) #??? dumb
        return game_items 

    def unp_pl_info(self, data):
        #data = player_data.split()
        #[str(round(x)),str(round(y)),str(m1),str(m2),str(m3)] + inventory
        x,y = int(data[0]), int(data[1])
        magic = [int(data[2]), int(data[3]), int(data[4])]
        inv = data[5:]
        inventory = []
        while inv:
            if inv[0] == 'armor':
                inventory += [['armor',[int(x) for x in inv[1:4]]]] #, [int(x) for x in inv[4:7]]]]
                inv = inv[4:]
            else:
                inventory += [[inv[0], [int(x) for x in inv[1:4]] ]]
                inv = inv[4:]
        return ((x,y),magic, inventory)

    def unp_frags_info(self, frags_info):
        frags_dict = {}
        while frags_info:
            frags_dict[frags_info[0]] = frags_info[1]
            frags_info = frags_info[2:]
        return frags_dict
    
    def extract_info(self,in_data):
        [pl_inf, items_inf, frags] = [dat.split() for dat in  in_data.split('lim')]
        return (pl_inf, items_inf, frags)   

    def run(self):
        self.running = True
        while self.running:
            recv_data = self.recv_data()
            if recv_data:
                pl_raw, game_raw, frags_raw = self.extract_info(recv_data)
            #while not self.in_queue.empty():
            #    self.in_queue.get()
                for i in range(1, self.in_queue.qsize()):
                    self.in_queue.get()            
                self.in_queue.put( (self.unp_game_items_info(game_raw), self.unp_pl_info(pl_raw), self.unp_frags_info(frags_raw)))
            
        
class Sender(threading.Thread):
    def __init__(self, socket, out_queue):
        super(Sender, self).__init__()
        self.socket = socket
        self.out_queue = out_queue
        self.running = True

    def form_mess(self, in_list):
        if in_list:
            str_mess = [str(it) for it in in_list]
        mess = ' '.join(str_mess)
        mess = mess.encode('utf-8')
        mess_size = len(mess)
        str_size = str(mess_size).encode('utf-8')
        len_head = len(str_size)
        header = b'0'*(8 - len_head) + str_size
        return header + mess

    def run(self):
        while self.running:
            while not self.out_queue.empty():
                msg = self.out_queue.get()
                self.socket.send(self.form_mess(msg))

def game(serv_addr, serv_port, name, password):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((serv_addr, serv_port))
    except:
        sock.close()
        return False
    in_queue = queue.Queue()
    recver = Receiver(sock, in_queue)
    out_queue = queue.Queue()
    sender = Sender(sock, out_queue)
    sender.start()
    out_queue.put(['join_game', name, password])
    field_size = recver.recv_inits()
    if not field_size:
        return False
    cl_hud = hud.Hud(SIZE, field_size, name)
    if cl_hud.failed:
        return False
    recver.start()
    prev_state = ([],(0,0,[]),{name: 0})
    while True:
        start_time = time.time()
        try:
            (game_items, pl_inf, frags) = in_queue.get()
        except:
            (game_items, pl_inf, frags) = prev_state
        messages = cl_hud.refresh(game_items, pl_inf, frags)
        prev_state = (game_items, pl_inf, frags)
        if messages == False:
            break
        for mess in messages:
            out_queue.put(mess)
        end_time = time.time()
        dt = end_time - start_time
        #if dt < 1 / REF_RATE:
        #    time.sleep(1 / REF_RATE - dt)
    out_queue.put(['leave_game'])
    recver.running = False
    sender.running = False
    recver.join()
    sender.join()
    sock.close()
    cl_hud.stop()
