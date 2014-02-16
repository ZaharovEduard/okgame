import threading
import os
import pygame as pg

class Hud:
    def __init__(self, win_size, field_size, pl_name):
        super(Hud,self).__init__()
        self.win_size = self.win_x, self.win_y = win_size
        self.field_size = self.field_x, self.field_y = field_size
        self.pl_name = pl_name
        try:        
            pg.init()
            self.scr = pg.display.set_mode(win_size)    
            ld = pg.image.load 
            self.pics = {'player': ld(os.path.join('res','player.png')).convert_alpha(),
                         'fireball': ld(os.path.join('res','fireball.png')).convert_alpha(),
                         'bag': ld(os.path.join('res','bag.png')).convert_alpha(),
                         'spawner': ld(os.path.join('res','spawner.png')).convert_alpha(),
                         'armor': ld(os.path.join('res','armor.png')).convert_alpha(),
                         'panel': ld(os.path.join('res','inventory_panel.png')).convert_alpha(),
                         'lifebar': ld(os.path.join('res','lifebar.png')).convert_alpha(),
                         'armor_icon': ld(os.path.join('res','armor_icon.png')).convert_alpha(),
                         'big_slider': ld(os.path.join('res','big_slider.png')).convert_alpha(),
                         'small_slider': ld(os.path.join('res','small_slider.png')).convert_alpha(),
                         'launch_panel': ld(os.path.join('res','launch_panel.png')).convert_alpha(),
                         'background': ld(os.path.join('res','background.png')).convert_alpha() }
            self.pics['background'] = self.make_background(self.pics['background'], field_size)          
            self.prev_launch = [0,0,0]
            self.prev_mov_dir = [0,0]
            self.moving_direc = [0,0]
            self.failed = False
        except:
            self.failed = True

    def refresh(self, game_items, player_info):
        (pl_coord, pl_magic, pl_inventory) = player_info
        x_assert, y_assert = self.count_assertion(pl_coord)
        print(x_assert,y_assert)
        self.scr.blit(self.pics['background'],(-x_assert, -y_assert))
        px = self.pics
        for item in game_items:
            [obj_type, item_x, item_y, item_r] = item
            self.scr.blit(px[obj_type], (item_x - x_assert - px[obj_type].get_size()[0]//2, item_y - y_assert - px[obj_type].get_size()[1]//2))
        mb = self.get_magicbar(pl_magic)
        ip = self.get_panel(pl_inventory)
        lp = self.get_launch_panel(self.prev_launch)
        self.mag_bar = (mb, (5,5))
        self.invent_p = (ip, (self.win_x // 2 - ip.get_size()[0] // 2, self.win_y - ip.get_size()[1]))
        self.launch_p = (lp, (self.win_x - lp.get_size()[0] - 5, self.win_y - lp.get_size()[1] - ip.get_size()[1] - 5))
        self.scr.blit(*self.mag_bar)
        self.scr.blit(*self.invent_p)
        self.scr.blit(*self.launch_p)
        pg.display.flip() 
        out= []
        for event in pg.event.get():
                if event.type == pg.QUIT:
                    return False
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_o:
                        out.append(['drop_item', self.pl_name, '0'])
                    if event.key == pg.K_p:
                        out.append(['pick_up', self.pl_name])
                    if event.key in (pg.K_UP, pg.K_w):
                        self.moving_direc[1] = -1
                    if event.key in (pg.K_DOWN, pg.K_s):
                        self.moving_direc[1] = 1
                    if event.key in (pg.K_RIGHT, pg.K_d):
                        self.moving_direc[0] = 1
                    if event.key in (pg.K_LEFT, pg.K_a):
                        self.moving_direc[0] = -1           
                elif event.type == pg.KEYUP:
                    if event.key in (pg.K_UP, pg.K_w):
                        self.moving_direc[1] = 0
                    if event.key in (pg.K_DOWN, pg.K_s):
                        self.moving_direc[1] = 0
                    if event.key in (pg.K_RIGHT, pg.K_d):
                        self.moving_direc[0] = 0
                    if event.key in (pg.K_LEFT, pg.K_a):
                        self.moving_direc[0] = 0
                elif event.type == pg.MOUSEBUTTONDOWN:
                    (x, y), (but1, but2, but3) = pg.mouse.get_pos(), pg.mouse.get_pressed()
                    invp_x, invp_y, invp_width, invp_height = self.invent_p[1][0], self.invent_p[1][1], \
                                                              self.invent_p[0].get_size()[0], self.invent_p[0].get_size()[1]
                    lp_x, lp_y, lp_width, lp_height = self.launch_p[1][0], self.launch_p[1][1], \
                                                      self.launch_p[0].get_size()[0], self.launch_p[0].get_size()[1]
                    if y > invp_y + 7:
                        if invp_x + 5 < x < invp_x + invp_width: 
                            inv_index = (x - invp_x - 5) // self.pics['armor_icon'].get_size()[1]
                            if but1:
                                out.append(['put_on', self.pl_name, inv_index])
                            elif but3:
                                out.append(['drop_item', self.pl_name, inv_index])
                    if lp_x < x < lp_x + lp_width and lp_y < y < lp_y + lp_height:
                        if but1:
                            row = (y - lp_y) // (lp_height // 3)
                            power = round((x - lp_x - lp_width // 2) / (lp_width // 2) * 100)
                            print(power)
                            self.prev_launch[row] = power 
                           # round((x - launch_pan_coord[0] - 60) / 58 * 100)
                    else:
                        n_x, n_y = x + x_assert - pl_coord[0], y + y_assert - pl_coord[1]
                        [mag1, mag2, mag3] = self.prev_launch
                        out.append(['throw_fireball', self.pl_name,  mag1, mag2, mag3, n_x, n_y])
                        
        if self.moving_direc == [0,0]:        
            if self.prev_mov_dir != self.moving_direc:        
                out.append(['move_to', self.pl_name, self.moving_direc[0], self.moving_direc[1]])
        else:
            out.append(['move_to', self.pl_name, self.moving_direc[0], self.moving_direc[1]])
        self.prev_mov_dir = self.moving_direc[:]    
        print(out)
        return out

    def count_assertion(self, pl_coord):
        if self.field_x - pl_coord[0] < self.win_x // 2:
            x_assert = self.field_x - self.win_x
        elif pl_coord[0] < self.win_x/2:
            x_assert = 0
        else:
            x_assert = pl_coord[0] - self.win_x // 2
    
        if self.field_y - pl_coord[1] < self.win_y // 2 - self.pics['panel'].get_size()[1]:
            y_assert = self.field_y - self.win_y + self.pics['panel'].get_size()[1]
        elif pl_coord[1] < self.win_y // 2:
            y_assert = 0
        else:
            y_assert = pl_coord[1] - self.win_y // 2
        return x_assert, y_assert

    def make_background(self, back_tex, field_size):
        out_surf = pg.Surface(field_size)
        b_x, b_y = back_tex.get_size()
        x_times = field_size[0] // b_x + 1
        y_times = field_size[1] // b_y + 1
        for i in range(0, x_times):
            for j in range(0, y_times):
                out_surf.blit(back_tex,(i * b_x, j * b_y))
        return out_surf

    def get_magicbar(self, magic):
        # [x,y,z]=magic
        lb = self.pics['lifebar']
        sld = self.pics['big_slider']
        out_surf = pg.Surface(lb.get_size(), pg.SRCALPHA)
        out_surf.blit(lb,(0,0))
        for ind, mag in zip(range(0,3), magic):
            x_slider = lb.get_size()[0]//2 + mag/100 * lb.get_size()[0]//2 - sld.get_size()[0]//2 
            y_slider = ind * lb.get_size()[1] // 3
            out_surf.blit(sld, (x_slider,y_slider))
        return out_surf
        
    def get_panel(self, inventory):
        pn = self.pics['panel']
        ar = self.pics['armor_icon']
        out_surf = pg.Surface(pn.get_size(), pg.SRCALPHA)    
        out_surf.blit(pn,(0,0))
        asset_x, asset_y = 5, 7
        for i, item in enumerate(inventory):
            x_item = asset_x + i*ar.get_size()[0]  
            y_item = asset_y
            out_surf.blit(ar,(x_item, y_item))
        return out_surf

    def get_launch_panel(self, prev_launch):
        lp = self.pics['launch_panel']
        sld = self.pics['small_slider']
        out_surf = pg.Surface(lp.get_size(), pg.SRCALPHA)
        out_surf.blit(lp, (0,0))
        for ind , mag in zip(range(0,3), prev_launch):
            x_slider = lp.get_size()[0] // 2  + mag/100 * lp.get_size()[0] // 2  - sld.get_size()[0] // 2
            y_slider = lp.get_size()[1] // 3 * ind
            out_surf.blit(sld,(x_slider, y_slider))
        return out_surf

    def stop(self):
        pg.quit()
