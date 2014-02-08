import math
import random
from pymunk.vec2d import Vec2d as vec
from phys import *

class Game_obj:
    def __init__(self, coord=None, vel=None, magic=None):
        self.owner = None
        if coord == None:
            self.coord = [100,100]
        else:
            self.coord = coord
        if vel == None:
            self.vel = vec(0,0)
        else:
            self.vel = vec(vel[0],vel[1])
        if magic == None:
            self.magic = [100,100,100]
        else:
            self.magic = magic
        self.force = vec(0,0)

        self.life_space = ([float("-Inf"), float("Inf")], [float("-Inf"), float("Inf")], [float("-Inf"), float("Inf")])
    
    def collide_with(self, other):
         if isinstance(other, Fireball): 
            self.owner.qmes.put(['remove_item',other])
            return
         vec_btw = vec(other.coord[0] - self.coord[0], other.coord[1] - self.coord[1])
         direct_vec=vec_btw.normalized()
         dist = vec_btw.length
         overlay = self.radius + other.radius - dist
         v1_direc = vec(self.vel.x, self.vel.y)
         v2_direc = vec(other.vel.x, other.vel.y)
         v1_direc.rotate(-direct_vec.angle)
         v2_direc.rotate(-direct_vec.angle)
         if  math.pi/2 < v2_direc.angle < 3/4 * math.pi: 
                v2_direc.x = -v2_direc.x
                v2_direc.rotate(direct_vec.angle)
                self.owner.qmes.put(['set_vel', v2_direc.x, v2_direc.y, other])
         #dcoor = (lambda x:  x+1 if x < 2   else  x**2)(overlay)
         dcoor = (lambda x:  x+1 if x < 2   else  x+3)(overlay)
         self.owner.qmes.put(['add_coord', dcoor * direct_vec.x, dcoor * direct_vec.y, other])

    def interact_with(self, other):    
        pass
class Spawner(Game_obj):
    def __init__(self, coord):
        super(Spawner, self).__init__(coord)
        self.radius  = 30 
        self.inertia = 400        

    def spawn(self, player):
        x_dir = (lambda x: -1 if x == 0 else 1)(random.randint(0,1)) * random.random()
        y_dir = (lambda x: -1 if x == 0 else 1)(random.randint(0,1)) * math.sqrt(1-x_dir**2)
        player.coord = [self.coord[0] + x_dir * (self.radius + player.radius + 2), self.coord[1] + y_dir * (self.radius + player.radius + 2)]
        player.magic = [100, 100, 100]
        self.owner.qmes.put(['force_add_item',player])
        #self.owner.qmes.put(['set_magic', 100, 100, 100, player])
        #self.owner.qmes.put(['set_coord', self.coord[0] + x_dir * (self.radius + player.radius + 2), self.coord[1] + y_dir * (self.radius + player.radius + 2),player])

class Player(Game_obj):
    def __init__(self, coord = None, vel=None, magic=None):
        super(Player, self).__init__(coord, vel, magic)
        self.radius = 20
        self.strength = 200 
        self.inertia = 150       
        self.life_space = ([1,200], [1,200], [1,200])
        self.armor = Armor()
                

    def throw_fireball(self, magic, direction ):
        direc = vec(direction[0], direction[1]).normalized()
        x = self.coord[0] + direc.x * (self.radius + 30) 
        y = self.coord[1] + direc.y * (self.radius + 30)             
        fireball = Fireball([x,y],[1.5*self.strength * direc.x + self.vel.x, 1.5*self.strength * direc.y + self.vel.y], magic)                    
        self.owner.qmes.put(['add_item',fireball])
    
    def move_to(self, direction):
        direction = vec(direction[0], direction[1]).normalized()
        speed = self.strength
        if self.owner:
            self.owner.qmes.put(['set_vel', speed*direction.x, speed*direction.y, self])
    def collide_with(self,other):
        if isinstance(other, Fireball): 
            self.owner.qmes.put(['remove_item',other])
        elif isinstance(other,Spawner):
            pass
        else:
            super(Player,self).collide_with(other)   

    def interact_with(self,other):
        if isinstance(other, Fireball):
            direction = vec(other.coord[0] - self.coord[0], other.coord[1] - self.coord[1])
            force = direction.normalized() *sum(a * b for a,b in zip(self.magic, self.armor.make_action(other.magic))) / direction.length
            self.owner.qmes.put(['add_force', force.x, force.y, other])

class Fireball(Game_obj):
    def __init__(self, coord=None , vel=None, magic=None):
        super(Fireball, self).__init__(coord, vel, magic)
        self.radius = 5
        self.inertia = math.sqrt(sum(x**2 for x in self.magic))

    def collide_with(self, other):
        if isinstance(other, Fireball):
            self.owner.qmes.put(['remove_item', other])
        elif isinstance(other, Player):
            mag = other.armor.make_impact(self.magic)
            self.owner.qmes.put(['hit_item', mag[0], mag[1], mag[2], other])
    def interact_with(self, other):
        if isinstance(other, Fireball):
            direction = vec(other.coord[0] - self.coord[0], other.coord[1] - self.coord[1])
            force=direction.normalized() * sum(x[0] * x[1] for x in zip(self.magic, other.magic)) / direction.length
            self.owner.qmes.put(['add_force', force.x, force.y, other])
class Armor:
    def __init__(self, action=None, impact=None):
        if action == None:
            self.action = [0,0,0]
        else:
            self.action = action
        if impact == None:
            self.action = [0,0,0]
        else:
            self.impact = impact

    def make_impact(self, magic):       
        return [mg * (1-imp/100) for mg,imp in zip(magic, self.impact)]
    
    def make_action(self, magic):
        #return sum([200/frc * mg for frc, mg in zip(self.action ,magic)])
        return [(1+abs(act)/100)*(lambda x: -1 if x<0 else 1)(act) * mag for act, mag in zip(self.action, magic)]
      
