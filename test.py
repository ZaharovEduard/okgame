import ok
import pygame as pg
def game():
    def eff(magic, dist):
        return 2*magic[0]
    def eff2(magic, dist):
        return -2*magic[0]
    ser = ok.Server()
    p1 = ok.Player([300,400],[0, 0], [100,100,100])
    p2 = ok.Player([400,300],[0,0], [100,100,100])
    p3 = ok.Player([30,500],[0,0], [100,100,100])
    p4 = ok.Player([700,300],[0,0], [100,100,100])
    p5 = ok.Player([100,20],[0,0], [100,100,100])
    p6 = ok.Player([600,20],[0,0], [100,100,100])
    arm = ok.Armor(p2, eff)
    arm2 = ok.Armor(p1, eff2)
    p1.armor = arm2
    p2.armor = arm
    fb = ok.Fireball([100,200],[10, 10], [10,10,10])
    ser.send(['add_env',[fb]])
    ser.send(['add_player',[p1]])
    ser.send(['add_player',[p2]])
    ser.send(['add_player',[p3]])
    ser.send(['add_player',[p4]])
    ser.send(['add_player',[p5]])
    ser.send(['add_player',[p6]])
    ser.run()
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
                    ser.stop()
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
                        p1.throw_fireball([-10,-10,0], [state[0][0] - p1.coord[0],state[0][1] - p1.coord[1]])
        if moving_direc == [0,0]:
            
            print(moving_direc)
            print(prev_state)
            if prev_state[:] != moving_direc[:]:
                     p1.stop()
                     print('stop')
        else:
            p1.move_to(moving_direc)
            print(moving_direc)
            print(str(prev_state)+'prs')
        prev_state = moving_direc
        background.fill((250,250,250))
        #print(p1.magic)
        screen.blit(background,(0,0))
        for item in ser.items:
            #print(item.coord[0], item.coord[1])
            pg.draw.circle(screen, (100,100,100),(round(item.coord[0]), round(item.coord[1])), round(item.radius))
        pg.display.flip()

    pg.quit()

if __name__ == "__main__":
    game()
