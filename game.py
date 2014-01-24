import serv
import pygame as pg

def game():
    
    player = serv.Player()
    server = serv.Server()
    game_object = serv.Game_object((200,200), [-2,-2,-2])
    server.mess(['add_player', player])
    server.mess(['add_env', game_object])
    pg.init()
    screen = pg.display.set_mode(server.field.size)
    background = pg.Surface(server.field.size)
    background = background.convert()
    work = True    
    server.run()
    while work:
        for event in pg.event.get():
                if event.type == pg.QUIT:
                    work = False
                    server.stop()
                elif event.type == pg.MOUSEBUTTONDOWN:
                    state = (pg.mouse.get_pos(), pg.mouse.get_pressed())
                    print(state)
                    if state[1][0] == 1:
                        player.move_to(state[0])
                    if state[1][2] == 1:
                        player.throw_fireball(state[0],[2,2,2])
        background.fill((250,250,250))
        
        screen.blit(background,(0,0))
        for item in server.items:
            print(item.coord[0], item.coord[1])
            pg.draw.circle(screen, (100,100,100),(int(item.coord[0]), int(item.coord[1])),8)
        pg.display.flip()

    pg.quit()
