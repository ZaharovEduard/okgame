import pygame as pg
import os

class Hud:
    def __init__(self, size):
        self.window_x = size[0]
        self.window_y = size[1]
        self.failed = False
        print(self.failed)
        pg.init()
        self.scr = pg.display.set_mode(size)
        self.panel = pg.image.load(os.path.join('res','inventory_panel.png')).convert_alpha()
        self.lifebar = pg.image.load(os.path.join('res','lifebar.png')).convert_alpha()
        self.armor_icon = pg.image.load(os.path.join('res','armor_icon.png')).convert_alpha()
        self.big_slider = pg.image.load(os.path.join('res','big_scroller.png')).convert_alpha()
        self.background = pg.image.load(os.path.join('res','background.jpeg')).convert()
        self.player = pg.image.load(os.path.join('res','player.png')).convert_alpha()
        self.fireball = pg.image.load(os.path.join('res','fireball.png')).convert_alpha()
        self.spawner = pg.image.load(os.path.join('res','spawner.png')).convert_alpha()
        self.bag = pg.image.load(os.path.join('res','bag.png')).convert_alpha()
        self.armor = pg.image.load(os.path.join('res','armor.png')).convert_alpha()
        self.launch_panel = pg.image.load(os.path.join('res','launch_panel.png')).convert_alpha()
        self.small_slider = pg.image.load(os.path.join('res','small_scroller.png')).convert_alpha()     

    def get_magicbar(self, magic):
        # [x,y,z]=magic
        out_surf = pg.Surface(self.lifebar.get_size()).convert_alpha()
        out_surf.blit(self.lifebar,(0,0))
        for ind, mag in zip(range(0,3), magic):
            x_slider = 62 + mag/100 * 60 - 3 
            y_slider = 2 + ind * 20
            out_surf.blit(self.big_slider, (x_slider,y_slider))
        return out_surf
        
    def get_panel(self, inventory):
        out_surf = pg.Surface(self.panel.get_size()).convert_alpha()    
        out_surf.blit(self.panel,(0,0))
        for i, item in enumerate(inventory):
            x_item = 5 + i*60  
            y_item = 10
            out_surf.blit(self.armor_icon,(x_item, y_item))
        return out_surf

    def get_launch_panel(self, prev_launch):
        out_surf = pg.Surface(self.launch_panel.get_size()).convert_alpha()
        out_surf.blit(self.launch_panel, (0,0))
        for ind , mag in zip(range(0,3), prev_launch):
            x_slider = 60 + mag/100 * 56 - 2
            y_slider = 3 + 20 * ind
            out_surf.blit(self.small_slider,(x_slider, y_slider))
        return out_surf

    def make_background(self, field_size):
        out_surf = pg.Surface(field_size)
        b_x, b_y = self.background.get_size()
        x_times = field_size[0] // b_x + 1
        y_times = field_size[1] // b_y + 1
        for i in range(0, x_times):
            for j in range(0, y_times):
                out_surf.blit(self.background,(i * b_x, j * b_y))
        return out_surf
