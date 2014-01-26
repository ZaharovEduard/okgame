import queue
import pygame as pg
from pymunk.vec2d import Vec2d as vec
from ok import *
from main_objects import *
from  server import *
def game():
    qu = queue.Queue()
    ser = Physics_server(qu,(1000,1000))
    ser.daemon = True
    ser.start()
    print(ser.field_size)
    p1 = Player([300,400],[0, 0], [100,100,100])
    p2 = Player([400,300],[10,0], [100,100,100])
    p3 = Player([30,500],[0,0], [100,100,100])
    p4 = Player([700,300],[0,0], [100,100,100])
    p5 = Player([100,20],[0,0], [100,100,100])
    p6 = Player([600,20],[0,0], [100,100,100])
    arm = Armor(p2, [-10,-10,-10 ],[100,100,100])
    arm2 = Armor(p1, [-30,-30,-30],[100,100, 100])
    arm3 = Armor(p3, [-30,-30,-30],[10,40, -30])
    arm4 = Armor(p4, [40,-80,-70],[0,0, 0])
    arm5 = Armor(p5, [0,0,0],[90,90, 90])
    #arm3 = ok.Armor(p1, [-20,0,-10],[-10,-30, -20])
    #arm4 = ok.Armor(p1, [-40,0,-20],[40,40, 40])
    p1.armor = arm2
    p2.armor = arm
    p3.armor = arm3
    p4.armor = arm4
    p5.armor = arm5
    fb = Fireball([100,200],[10, 10], [10,10,10])
    #ser.send(['add_env',[fb]])
    qu.put(['add_player',[p1],p1])
    #qu.put(['add_player',[p2],p2])
    qu.put(['add_player',[p3],p3])
    qu.put(['add_player',[p4],p4])
    #qu.put(['add_player',[p5],p5])
    #qu.put(['add_player',[p6],p6])
    #ser.send(['add_player',[p3]])
    #ser.send(['add_player',[p4],p1])
    #ser.send(['add_player',[p5]])
    #ser.send(['add_player',[p6],p1])

    screen = pg.display.set_mode(ser.field_size)
    background = pg.Surface(ser.field_size)
    background = background.convert()
    work = True    
    moving_direc = [0,0]
    prev_state = [0,0]
    while work:
        for event in pg.event.get():
                if event.type == pg.QUIT:
                    work = False
                    qu.put(['exit'])
                elif event.type == pg.KEYDOWN:
                    if event.key in (pg.K_UP, pg.K_w):
                        moving_direc[1] = -1
                    if event.key in (pg.K_DOWN, pg.K_s):
                        moving_direc[1] = 1
                    if event.key in (pg.K_RIGHT, pg.K_d):
                        moving_direc[0] = 1
                    if event.key in (pg.K_LEFT, pg.K_a):
                        moving_direc[0] = -1
                    print('keydown')                
                elif event.type == pg.KEYUP:
                    if event.key in (pg.K_UP, pg.K_w):
                        moving_direc[1] = 0
                    if event.key in (pg.K_DOWN, pg.K_s):
                        moving_direc[1] = 0
                    if event.key in (pg.K_RIGHT, pg.K_d):
                        moving_direc[0] = 0
                    if event.key in (pg.K_LEFT, pg.K_a):
                        moving_direc[0] = 0
                    print('keyup')
                elif event.type == pg.MOUSEBUTTONDOWN:
                    state = (pg.mouse.get_pos(), pg.mouse.get_pressed())
                    
                    print('mouse')
                    if state[1][0] == 1:
                        p1.throw_fireball([100,100,100], [state[0][0] - p1.coord[0],state[0][1] - p1.coord[1]])
        #if moving_direc == [0,0]:
            
        #    print(moving_direc)
        #    print(prev_state)
        #    if prev_state[:] != moving_direc[:]:
        #             p1.stop()
        #             print('stop')
        #else:
        p1.move_to(moving_direc)
        prev_state = moving_direc
        background.fill((250,250,250))
        #print(p1.magic,p2.magic)
        screen.blit(background,(0,0))
        things = ser.items[:]
        for item in things:
            pg.draw.circle(screen, (10,10,10),(round(item.coord[0]), round(item.coord[1])), round(item.radius))
        pg.display.flip()
    ser.join()
    pg.quit()

if __name__ == "__main__":
    game()
