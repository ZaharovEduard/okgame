import pygame as pg
import server
import queue
import time
q1 = queue.Queue()
q2 = queue.Queue()
q3 = queue.Queue()
ser = server.Server(q1,q2, q3)
ser.start()
time.sleep(3)
q1.put(['register',['as','as']])
q1.put(['join_game', ['as','as']])

q1.put(['register',['dad','dad']])
q1.put(['join_game',['dad','dad']])
print(ser.game.items)
print(ser.all_players)
print(ser.game.items)
screen = pg.display.set_mode(ser.game.field_size)
background = pg.Surface(ser.game.field_size)
background = background.convert()
work = True
while work:
        for event in pg.event.get():
                if event.type == pg.QUIT:
                    work = False
                    q1.put(['exit'])
        things = ser.game.items[:]
        background.fill((250,250,250))
        #print(p1.magic,p2.magic)
        screen.blit(background,(0,0))
        for item in things:
            pg.draw.circle(screen, (10,10,10),(round(item.coord[0]), round(item.coord[1])), round(item.radius))
        pg.display.flip()
q1.put(['exit'])
ser.join()
pg.quit()

