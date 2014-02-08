import sys
import socket
import select
import time
import pygame as pg
REF_RATE = 70
TIMEOUT = 10
SIZE = (800,600)
BYTES_IN_HEADER = 8

def unpack_field_info(f_info):
    info = f_info.decode().split()
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

def count_assertion(field_size, pl_coord):
    if field_size[0] - pl_coord[0] < SIZE[0]/2:
        x_assert = field_size[0] - SIZE[0]
    elif pl_coord[0] < SIZE[0]/2:
        x_assert = 0
    else:
        x_assert = pl_coord[0] - SIZE[0] // 2
    
    if field_size[1] - pl_coord[1] < SIZE[1]/2:
        y_assert = field_size[1] - SIZE[1]
    elif pl_coord[1] < SIZE[1]/2:
        y_assert = 0
    else:
        y_assert = pl_coord[1] - SIZE[1] // 2
    return x_assert, y_assert

def game(serv_addr, serv_port, name, password):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((serv_addr, serv_port))
    except:
        print('Can not connect to server')
        sock.close()
        return
    sock.send(form_mess(['join_game', name, password]))
    read_sock, _, _ = select.select([sock],[],[],TIMEOUT)
    field_data = ''
    if read_sock:
        header = sock.recv(BYTES_IN_HEADER)
        if header == b'':
            print('Server closed connection')
            sock.close()
            return
        n_bytes = int(header.decode())
        field_data = sock.recv(n_bytes)
    else:
        print('Server does not answer')
        sock.close()
        return
    field_size = unpack_field_info(field_data) # (width, height)
    if not field_size:
        print('not logged')
        sock.close()
        return
    pg.init()
    screen = pg.display.set_mode(SIZE)
    background = pg.Surface(SIZE)
    background = background.convert()

    prev_state = [0,0]
    moving_direc = [0,0]     
    work = True 
    while work:
        start_time = time.time()
        sock.send(form_mess(['alive', name]))
        read_sock, _, _ = select.select([sock],[],[],TIMEOUT)
        data = ''
        if read_sock:
            header = sock.recv(BYTES_IN_HEADER)
            if header == b'':
                print('Server closed connection')
                break
            n_bytes = int(header.decode())
            data = sock.recv(n_bytes)
        else:
            print('Server does not answer')
            break
        inc = unpack_data(data)
        if inc =='not_logged':
            break
        (player_info, game_items) = inc
        pl_coord = [int(player_info[0][0]), int(player_info[0][1])]
        pl_magic = player_info[1]
        background.fill((250,250,250))
        screen.blit(background,(0,0))

        x_assert, y_assert = count_assertion(field_size, pl_coord)

        for item in game_items:
            pg.draw.circle(screen, (10,10,10), (round(float(item[0])) - x_assert, round(float(item[1])) - y_assert), round(float(item[2])) )
        pg.display.flip()
        for event in pg.event.get():
                if event.type == pg.QUIT:
                    work = False
                    break
                elif event.type == pg.KEYDOWN:
                    if event.key in (pg.K_UP, pg.K_w):
                        moving_direc[1] = -1
                    if event.key in (pg.K_DOWN, pg.K_s):
                        moving_direc[1] = 1
                    if event.key in (pg.K_RIGHT, pg.K_d):
                        moving_direc[0] = 1
                    if event.key in (pg.K_LEFT, pg.K_a):
                        moving_direc[0] = -1           
                elif event.type == pg.KEYUP:
                    if event.key in (pg.K_UP, pg.K_w):
                        moving_direc[1] = 0
                    if event.key in (pg.K_DOWN, pg.K_s):
                        moving_direc[1] = 0
                    if event.key in (pg.K_RIGHT, pg.K_d):
                        moving_direc[0] = 0
                    if event.key in (pg.K_LEFT, pg.K_a):
                        moving_direc[0] = 0
                elif event.type == pg.MOUSEBUTTONDOWN:
                    state = (pg.mouse.get_pos(), pg.mouse.get_pressed())
                    if state[1][0] == 1:
                        x, y = state[0][0] + x_assert - float(player_info[0][0]), state[0][1] + y_assert - float(player_info[0][1])
                        mag1, mag2, mag3 = 10,10,-10
                        sock.send(form_mess(['throw_fireball', name,  mag1, mag2, mag3, x, y]))
        if moving_direc == [0,0]:        
            if prev_state != moving_direc:        
                sock.send(form_mess(['move_to', name, moving_direc[0], moving_direc[1]]))
        else:
            sock.send(form_mess(['move_to', name, moving_direc[0], moving_direc[1]]))
        prev_state = moving_direc[:]

        end_time = time.time()
        dt = end_time - start_time
        if dt < 1 / REF_RATE:
            time.sleep(1/REF_RATE - dt) 
    sock.send(form_mess(['leave_game',name]))
    sock.close()
    pg.quit()
