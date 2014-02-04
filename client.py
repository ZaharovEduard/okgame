import sys
import socket
import select
import time
import pygame as pg
REF_RATE = 70
TIMEOUT = 10
SIZE = (800,600)
BYTES_IN_HEADER = 8

def unpack_data(data):
    rcvd_data = data.decode().split()
    player_info = [rcvd_data[0:2],rcvd_data[2:5]]
    game_items = [rcvd_data[5:][i:i+3] for i in range(0,len(rcvd_data[5:]),3)]
    #print(player_info, game_items)
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
        #print(header+mess)
        return header + mess

def game(serv_addr, serv_port, register, name, password):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((serv_addr, serv_port))
    except:
        print('Can not connect to server')
        return
    if register:
        mess = form_mess([name, password, 'register'])
        sock.send(mess)
        #sock.recv(64)
    pg.init()
    screen = pg.display.set_mode(SIZE)
    background = pg.Surface(SIZE)
    background = background.convert()
    work = True 
    sock.send(form_mess([name, password, 'join_game']))
    prev_state = [0,0]
    moving_direc = [0,0] 
    while work:
        start_time = time.time()
        sock.send(form_mess([name, password, 'alive']))
        read_sock, _, _ = select.select([sock],[],[],TIMEOUT)
        data = ''
        if read_sock:
            header = sock.recv(BYTES_IN_HEADER)
            if header == b'':
                print('Server closed connection')
                break
            n_bytes = int(header.decode())
            data = sock.recv(n_bytes)
            #print(data)
        else:
            print('Server does not answer')
            break

        (player_info, game_items) = unpack_data(data)
        #print(player_info, game_items)
        for event in pg.event.get():
                #print(moving_direc)
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
                    #print('keydown')                
                elif event.type == pg.KEYUP:
                    if event.key in (pg.K_UP, pg.K_w):
                        moving_direc[1] = 0
                    if event.key in (pg.K_DOWN, pg.K_s):
                        moving_direc[1] = 0
                    if event.key in (pg.K_RIGHT, pg.K_d):
                        moving_direc[0] = 0
                    if event.key in (pg.K_LEFT, pg.K_a):
                        moving_direc[0] = 0
                    #print('keyup')
                elif event.type == pg.MOUSEBUTTONDOWN:
                    state = (pg.mouse.get_pos(), pg.mouse.get_pressed())
                    if state[1][0] == 1:
                        x, y = state[0][0] - float(player_info[0][0]), state[0][1] - float(player_info[0][1])
                        [mag1, mag2, mag3] = player_info[1]
                        sock.send(form_mess([name, password, 'throw_fireball', mag1, mag2, mag3, x, y]))
        if moving_direc == [0,0]:        
            if prev_state != moving_direc:        
                sock.send(form_mess([name, password, 'move_to', moving_direc[0], moving_direc[1]]))
                #pass
        else:
            sock.send(form_mess([name, password, 'move_to', moving_direc[0], moving_direc[1]]))
            #pass
        prev_state = moving_direc[:]
        background.fill((250,250,250))
        screen.blit(background,(0,0))
        for item in game_items:
            pg.draw.circle(screen, (10,10,10),(round(float(item[0])), round(float(item[1]))), round(float(item[2])))
        pg.display.flip()
        end_time = time.time()
        dt = end_time - start_time
        #print(dt)
        if dt < 1 / REF_RATE:
            time.sleep(1/REF_RATE - dt) 
    sock.send(form_mess([name, password, 'leave_game']))
    sock.close()
    pg.quit()
