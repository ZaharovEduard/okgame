import sys
import socket
import select
import time
import pygame as pg
from hud import *
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

def unpack_player_info(player_data):
    data = player_data.split()
    #[str(round(x)),str(round(y)),str(m1),str(m2),str(m3)] + inventory
    x,y = int(data[0]), int(data[1])
    magic = [int(data[2]), int(data[3]), int(data[4])]
    inv = data[5:]
    inventory = []
    while inv:
        if inv[0] == 'armor':
            inventory += [['armor',[int(x) for x in inv[1:4]], [int(x) for x in inv[4:7]]]]
            inv = inv[7:]
        else:
            inventory += [[inv[0], [int(x) for x in inv[1:4]] ]]
            inv = inv[4:]
    return ((x,y),magic, inventory)

def unpack_game_items_info(items_info):
    items_raw = items_info.split()
    game_items = [items_raw[i:i+4] for i in range(0,len(items_raw),4)]
    for item in game_items:
        item[1], item[2], item[3] = int(item[1]), int(item[2]), int(item[3])
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

def count_assertion(field_size, pl_coord):
    if field_size[0] - pl_coord[0] < SIZE[0]/2:
        x_assert = field_size[0] - SIZE[0]
    elif pl_coord[0] < SIZE[0]/2:
        x_assert = 0
    else:
        x_assert = pl_coord[0] - SIZE[0] // 2
    
    if field_size[1] - pl_coord[1] < SIZE[1]/2-50:
        y_assert = field_size[1] - SIZE[1] + 50
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
    pg.init()
    hud = Hud(SIZE)
    if hud.failed:
        print('hud init failed')
        return False
    screen = pg.display.set_mode(SIZE)
    #background = pg.Surface(SIZE)
    #background = background.convert()
    background = hud.make_background(field_size)


    prev_state = [0,0]
    moving_direc = [0,0]     
    work = True 
    prev_fb_launch = [0,0,0]
    while work:
        start_time = time.time()
        sock.send(form_mess(['alive', name]))
        player_data = receive_data(sock)
        if not player_data:
            break
        (pl_coord, pl_magic, pl_inventory) = unpack_player_info(player_data) 

        game_items_data = receive_data(sock)
        if not game_items_data:
            break
        game_items = unpack_game_items_info(game_items_data)
        #background.fill((250,250,250))

        x_assert, y_assert = count_assertion(field_size, pl_coord)
        screen.blit(background,(-x_assert,-y_assert))
        # draw background and game items
        for item in game_items:
            obj_type = item[0]
            if obj_type == 'player':
                screen.blit(hud.player, (item[1] - x_assert - hud.player.get_size()[0]//2, item[2] - y_assert - hud.player.get_size()[1]//2))
            elif obj_type == 'fireball':
                screen.blit(hud.fireball, (item[1] - x_assert - hud.fireball.get_size()[0]//2, item[2] - y_assert - hud.fireball.get_size()[1]//2))           
            elif obj_type == 'bag':
                screen.blit(hud.bag, (item[1] - x_assert - hud.bag.get_size()[0]//2, item[2] - y_assert - hud.bag.get_size()[1]//2))
            elif obj_type == 'spawner': 
                screen.blit(hud.spawner, (item[1] - x_assert - hud.spawner.get_size()[0]//2, item[2] - y_assert - hud.spawner.get_size()[1]//2))
            elif obj_type == 'armor':
                screen.blit(hud.armor, (item[1] - x_assert - hud.armor.get_size()[0]//2, item[2] - y_assert - hud.armor.get_size()[1]//2))
            else:            
                pg.draw.circle(screen, (10,10,10), (item[1] - x_assert, item[2] - y_assert), item[3] )
        #draw interface
        magic_bar = hud.get_magicbar(pl_magic).convert_alpha()
        invent_panel = hud.get_panel(pl_inventory)
        launch_panel = hud.get_launch_panel(prev_fb_launch)
        screen.blit(magic_bar,(0,0))
        inv_pan_coord = (SIZE[0]//2 - 400, SIZE[1] - 50)
        screen.blit(invent_panel, inv_pan_coord)
        launch_pan_coord = (SIZE[0] - 130, SIZE[1] - 120)
        screen.blit(launch_panel, launch_pan_coord) 
        pg.display.flip()
        for event in pg.event.get():
                if event.type == pg.QUIT:
                    work = False
                    break
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_o:
                        sock.send(form_mess(['drop_item', name, '0']))
                    if event.key == pg.K_p:
                        sock.send(form_mess(['pick_up', name]))
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
                    (x, y), (but1, but2, but3) = pg.mouse.get_pos(), pg.mouse.get_pressed()
                    if y > SIZE[1] - 50: # width of inv panel
                        if SIZE[0]//2 - 398 < x < SIZE[0]//2 + 398: # x borders of panel 
                            inv_index = (x - inv_pan_coord[0]) // 60 # 80 pixels in one cell ov invent
                            if but1:
                                sock.send(form_mess(['put_on', name, inv_index]))
                            elif but3:
                                sock.send(form_mess(['drop_item', name, inv_index]))
                    if  launch_pan_coord[1] < y < launch_pan_coord[1] + 60 and launch_pan_coord[0] + 3 < x < launch_pan_coord[0] + 120 - 4:
                        if but1:
                            row = (y - launch_pan_coord[1]) // 20
                            power = round((x - launch_pan_coord[0] - 60) / 58 * 100)
                            prev_fb_launch[row] = power 
                    else:
                        n_x, n_y = x + x_assert - pl_coord[0], y + y_assert - pl_coord[1]
                        [mag1, mag2, mag3] = prev_fb_launch
                        sock.send(form_mess(['throw_fireball', name,  mag1, mag2, mag3, n_x, n_y]))
                        
                    #state = (pg.mouse.get_pos(), pg.mouse.get_pressed())
                    #if state[1][0] == 1:
                     #   x, y = state[0][0] + x_assert - pl_coord[0], state[0][1] + y_assert - pl_coord[1]
                      #  mag1, mag2, mag3 = 10,0,-10
                       # sock.send(form_mess(['throw_fireball', name,  mag1, mag2, mag3, x, y]))
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
