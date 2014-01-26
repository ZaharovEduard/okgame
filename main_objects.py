import math
from pymunk.vec2d import Vec2d as vec
from ok import *

class Game_obj:
    def __init__(self, coord=[100,100], vel=[0,0], magic=[1,1,1]):
        self.owner = None
        self.coord = coord
        self.vel = vec(vel[0],vel[1])
        self.magic = magic
        self.force = vec(0,0)
        self.inertia = math.sqrt(sum(x**2 for x in self.magic))
        self.life_space = ([float("-Inf"), float("Inf")], [float("-Inf"), float("Inf")], [float("-Inf"), float("Inf")])
    
    def collide_with(self, other):
         if isinstance(other, Fireball): 
            self.owner.qmes.put(['remove',[other],self])
            return
         vec_btw = vec(-self.coord[0] + other.coord[0], -self.coord[1] + other.coord[1])
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
                self.owner.qmes.put(['set_vel', [v2_direc, other], self])
         dcoor = (lambda x:  x+1 if x < 2   else  x**2)(overlay)
         add_coor = [dcoor * direct_vec.x, dcoor * direct_vec.y]
         #other.coord[0] -= direct_vec.x * (1+(lambda x:  x if x < 2   else  x**2)( overlay))
         #other.coord[1] -= direct_vec.y * (1+(lambda x:  x if x < 2   else  x**2)( overlay))
         self.owner.qmes.put(['add_coord',[add_coor, other],self])

    def interact_with(self, other):    
        pass

class Player(Game_obj):
    def __init__(self, coord=[100, 100] , vel=[0,0], magic=[10,10,10]):
        super(Player, self).__init__(coord, vel, magic)
        self.radius = 20
        self.strength = 200        
        self.life_space = ([1,200], [1,200], [1,200])
        self.armor = Armor(self)
                

    def throw_fireball(self, magic, direction ):
        if self.owner:
            self.owner.qmes.put(['throw_fireball',[magic, direction],self])
    
    def move_to(self, direction):
        if self.owner:
            self.owner.qmes.put(['move_to',[direction],self])
    def collide_with(self,other):
        if isinstance(other, Fireball): 
            self.owner.qmes.put(['remove',[other],self])
        else:
            super().collide_with(other)   

    def interact_with(self,other):
        if isinstance(other, Fireball):
            direction = vec(other.coord[0] - self.coord[0], other.coord[1] - self.coord[1])
            self.owner.qmes.put(['add_force', [sum(a * b for a,b in zip(self.magic, self.armor.make_action(other.magic)))*\
                                                                    direction.normalized()/direction.length, other],self])
    def stop(self):
        if self.owner:
            self.owner.qmes.put(['stop',self])

class Fireball(Game_obj):
    def __init__(self, coord=[100, 100] , vel=[0,0], magic=[ 1, 1, 1]):
        super(Fireball, self).__init__(coord, vel, magic)
        self.radius = 5
    def collide_with(self, other):
        if isinstance(other, Fireball):
            self.owner.qmes.put(['remove',[other], self])
        elif isinstance(other, Player):
            mag = other.armor.make_impact(self.magic)
            self.owner.qmes.put(['hit',[mag, other],self])
    def interact_with(self, other):
        if isinstance(other, Fireball):
            direction = vec(other.coord[0] - self.coord[0], other.coord[1] - self.coord[1])
            force=direction.normalized() * sum(x[0] * x[1] for x in zip(self.magic, other.magic)) / direction.length
            print(force)
            self.owner.qmes.put(['add_force',[force, other],self])
class Armor:
    def __init__(self, player = None, action=[0,0,0], impact=[0,0,0]):
        self.action = action
        self.impact = impact

    def make_impact(self, magic):       
        return [mg*(1-imp/100) for mg,imp in zip(magic, self.impact)]
    
    def make_action(self, magic):
        #return sum([200/frc * mg for frc, mg in zip(self.action ,magic)])
        return [(1+abs(act)/100)*(lambda x: -1 if x<0 else 1)(act) * mag for act, mag in zip(self.action, magic)]
      
