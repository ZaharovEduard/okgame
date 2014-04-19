import math
import random
from pymunk.vec2d import Vec2d as vec

class Game_obj:
    def __init__(self, coord=None, vel=None, magic=None):
        self.owner = None
        self.coord = coord if coord else [100,100]
        self.vel = vec(vel[0],vel[1]) if vel else vec(0,0)
        self.magic = magic if magic else [100,100,100]
        self.force = vec(0,0)
        self.life_space = ([float("-Inf"), float("Inf")], [float("-Inf"), float("Inf")], [float("-Inf"), float("Inf")])
        self.pickable = False

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
         dcoor = (lambda x:  x+1 if x < 2   else  x+3)(overlay)
         self.owner.qmes.put(['add_coord', dcoor * direct_vec.x, dcoor * direct_vec.y, other])

    def interact_with(self, other):    
        pass

    def is_dead(self):
        if self.life_space[0][0] < self.magic[0] < self.life_space[0][1] and \
           self.life_space[1][0] < self.magic[1] < self.life_space[1][1] and \
           self.life_space[0][0] < self.magic[0] < self.life_space[0][1]:
            return False
        else:
            return True

class Spawner(Game_obj):
    def __init__(self, coord):
        super(Spawner, self).__init__(coord)
        self.radius  = 30 
        self.inertia = 400        
        self.obj_type = 'spawner'
    
    def spawn(self, player):
        x_dir = (lambda x: -1 if x == 0 else 1)(random.randint(0,1)) * random.random()
        y_dir = (lambda x: -1 if x == 0 else 1)(random.randint(0,1)) * math.sqrt(1-x_dir**2)
        player.coord = [self.coord[0] + x_dir * (self.radius + player.radius + 2), self.coord[1] + y_dir * (self.radius + player.radius + 2)]
        player.magic = [0, 0, 0]
        self.owner.qmes.put(['force_add_item',player])

class Player(Game_obj):
    def __init__(self, coord = None, vel=None, magic=None):
        super(Player, self).__init__(coord, vel, magic)
        self.radius = 20
        self.strength = 200 
        self.inertia = 150       
        self.life_space = ([-100,100], [-100,100], [-100,100])
        self.armor = Armor()
        self.inventory = []
        self.action_radius = 10
        self.obj_type = 'player'
        self.inv_capacity = 10  
        self.frags = 0      
                
    def pick_up(self):
        rem_pickab = set([])
        for item in self.owner.pickable_items:
            if math.sqrt((self.coord[0] - item.coord[0])**2 + (self.coord[1] - item.coord[1])**2) < self.action_radius + self.radius + item.radius:
                    if self.inv_capacity >= len(self.inventory):                    
                        self.inventory.append(item)                  
                        rem_pickab.add(item)
                    else:
                        break
        if self.inventory:
            if  isinstance(self.inventory[0], Armor):
                self.armor = self.inventory[0]
        for rem in rem_pickab:
            self.owner.qmes.put(['remove_item', rem])
    
    def drop_item(self):
        if self.inventory:
            to_drop = self.inventory.pop(0)
            direc = -self.vel.normalized()
            coor = []
            if direc == vec(0,0):            
                coor = [self.coord[0], self.coord[1] + self.radius + 20] #  20 is bag radius (10) + gap (10)
            else:
                coor = [self.coord[0] + direc.x * 40, self.coord[1] + direc.y * 40]     
            to_drop.coord = coor
            self.owner.qmes.put(['add_item', to_drop])
            if  self.inventory:
                if isinstance(self.inventory[0], Armor):
                    self.armor = self.inventory[0]

    def throw_fireball(self, magic, direction ):
        direc = vec(direction[0], direction[1]).normalized()
        x = self.coord[0] + direc.x * (self.radius + 30) 
        y = self.coord[1] + direc.y * (self.radius + 30)             
        fireball = Fireball([x,y],[1.5*self.strength * direc.x + self.vel.x, 1.5*self.strength * direc.y + self.vel.y], magic, self)                    
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
            force = direction.normalized() * sum(a * b for a,b in zip(self.magic, self.armor.make_action(other.magic))) / direction.length
            self.owner.qmes.put(['add_force', force.x, force.y, other])

class Fireball(Game_obj):
    def __init__(self, coord=None , vel=None, magic=None, firerer=None):
        super(Fireball, self).__init__(coord, vel, magic)
        self.radius = 5
        self.firerer = firerer
        sq_sum_magic = math.sqrt(sum(x**2 for x in self.magic))
        self.inertia = 5 
        self.obj_type = 'fireball'        

    def collide_with(self, other):
        if isinstance(other, Fireball):
            self.owner.qmes.put(['remove_item', other])
        elif isinstance(other, (Player, Armor)):
            self.owner.qmes.put(['hit_item', self, other])

    def interact_with(self, other):
        if isinstance(other, Fireball):
            direction = vec(other.coord[0] - self.coord[0], other.coord[1] - self.coord[1])
            force=direction.normalized() * sum(x[0] * x[1] for x in zip(self.magic, other.magic)) / direction.length
            self.owner.qmes.put(['add_force', force.x, force.y, other])

class Armor(Game_obj):
    def __init__(self, coord=None, action=None):
        super(Armor, self).__init__(coord = coord, magic = [10,10,10])
        self.life_space = ([1,20],[1,20],[1,20])
        self.radius = 10
        self.inertia = 400
        self.pickable = True 
        self.action = action if action else [0,0,0]
        self.obj_type = 'armor'        
    
    def make_action(self, magic):
        return [(1+abs(act)/100)*(lambda x: -1 if x<0 else 1)(act) * mag for act, mag in zip(self.action, magic)]
 
class Bag(Game_obj):
    def __init__(self, things = None, coord = None):
        super(Bag, self).__init__(coord=coord, magic=[10,10,10])
        self.things = things if things else []
        self.life_space = ([1,20],[1,20],[1,20])
        self.radius = 10
        self.inertia = 400
        self.pickable = True
        self.obj_type = 'bag'
