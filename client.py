import sys
import socket
import select
import time
import pygame as pg
import hud

REF_RATE = 70
TIMEOUT = 10
SIZE = (800,600)
BYTES_IN_HEADER = 8
def receive_data(sock):
    read_sock, _, _ = select.select([sock],[],[],TIMEOUT)
    player_data = ''
    if read_sock:
        header = sock.recv(BYTES_IN_HEADER)
        if header == b'':
            return False
        n_bytes = int(header.decode())
        data = sock.recv(n_bytes).decode()
        return data        
    else:
        return False

def extract_info(in_data):
    [pl_inf, items_inf, frags] = [dat.split() for dat in  in_data.split('lim')]
    '''
    data = in_data.split()
    pl_inf , items_inf, frags = [], [], []
    limiter = False
    for word in data:
        if word == 'lim':
            limiter = True
            continue
        if limiter:
            items_inf.append(word)
        else:
            pl_inf.append(word)
    return (pl_inf, items_inf)'''
    return (pl_inf, items_inf, frags)    

def unpack_player_info(data):
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

def unpack_frags(frags_info):
    frags_dict = {}
    while frags_info:
        frags_dict[frags_info[0]] = frags_info[1]
        frags_info = frags_info[2:]
    return frags_dict

def unpack_game_items_info(items_raw):
    #items_raw = items_info.split()
    game_items = [items_raw[i:i+4] for i in range(0,len(items_raw),4)]
    for item in game_items:
        item[1], item[2], item[3] = int(item[1]), int(item[2]), int(item[3]) #??? dumb
    return game_items 

def unpack_field_info(f_info):
    info = f_info.split()
    if info == ['not_logged']:
        return False
    else:
        return (int(info[0]), int(info[1]))

def unpack_data(data):
    rcvd_data = data.decode().split()
    player_info = [rcvd_data[0:2],rcvd_data[2:5]]
    game_items = [rcvd_data[5:][i:i+3] for i in range(0,len(rcvd_data[5:]),3)]
    return (player_info,game_items)

def form_mess(in_list):
    if in_list:
        str_mess = [str(it) for it in in_list]
        mess = ' '.join(str_mess)
        mess = mess.encode('utf-8')
        mess_size = len(mess)
        str_size = str(mess_size).encode('utf-8')
        len_head = len(str_size)
        header = b'0'*(8 - len_head) + str_size
        return header + mess

def game(serv_addr, serv_port, name, password):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((serv_addr, serv_port))
    except:
        print('Can not connect to server')
        sock.close()
        return False
    sock.send(form_mess(['join_game', name, password]))
    field_data = receive_data(sock)
    if not field_data:
        print('no field data received')
        return False
    field_size = unpack_field_info(field_data) # (width, height)
    if not field_size:
        print('not logged')
        sock.close()
        return False
    cl_hud = hud.Hud(SIZE,field_size,name)
    if cl_hud.failed:
        print('hud init failed')
        return False
    work = True 
    while work:
        start_time = time.time()
        recv_data = receive_data(sock)
        if not recv_data:
            break
        pl_raw, game_raw, frags_raw = extract_info(recv_data) 
        pl_inf, game_items , frags = unpack_player_info(pl_raw), unpack_game_items_info(game_raw), unpack_frags(frags_raw)  
        messages = cl_hud.refresh(game_items, pl_inf, frags) 
        if messages == False:
            break
        for mess in messages:
            sock.send(form_mess(mess))
        
        end_time = time.time()
        dt = end_time - start_time
        if dt < 1 / REF_RATE:
            time.sleep(1/REF_RATE - dt)
    sock.send(form_mess(['leave_game']))
    sock.close()
    cl_hud.stop()
