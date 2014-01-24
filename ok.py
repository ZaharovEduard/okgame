import threading
import time
import random
import math
from pymunk.vec2d import Vec2d as vec
from functools import reduce

FIREBALL_GAP = 20
INTERACTION_DIST = 1000
COLLISION_DIST = 0.1
MIN_MAGIC = 1
class Server:
    def __init__(self, size=(800,600), step=0.01):
        self.step = step
        self.items = []
        self.field_size = size

        self.running = False
        self.worker_messages = []
        self.data = 0

    def run(self):
        self.running = True
        self.workthread = threading.Thread(target=self.work)
        print('Worker thread started')
        self.workthread.start()

    def stop(self):
        self.running = False
        self.workthread.join()
    
    def work(self):
            while self.running:
                start_time = time.time()
#---------------Message processing--------                
                to_remove = []                
                for mess in self.worker_messages:
        
                    self.proceed_mess(mess)

                    to_remove.append(mess)
                self.worker_messages = [x for x in self.worker_messages if x not in to_remove] 
                 
#-----------------------------------------
                rem_items = set([]) 
                for item in self.items:
                    ls = item.life_space
                    mg = item.magic                    
                     
                    if not    (ls[0][0] < mg[0] < ls[0][1] and ls[1][0] < mg[1] <ls[1][1] and ls[2][0] < mg[2] < ls[2][1]) \
                           or (reduce(lambda x,y: x*y, [abs(check) < MIN_MAGIC for check in mg])):
       
                        print('wwwoo')                        
                        rem_items.add(item)                        
                    
                    vx, vy = item.vel.x + item.force.x/item.inertia, item.vel.y + item.force.y/item.inertia
                    dx,dy = vx * self.step, vy * self.step
                    x = item.coord[0]
                    y = item.coord[1]      
                    x += dx
                    y += dy
                    setvel = False
                    if x < item.radius:
                        x = item.radius
                        setvel = True
                    elif x > self.field_size[0]-item.radius:
                        x = self.field_size[0]-item.radius
                        setvel = True
                    if y < item.radius:
                        y = item.radius
                        setvel = True
                    elif y > self.field_size[1]-item.radius:
                        y = self.field_size[1]-item.radius
                        setvel = True
                    
                    item.coord = [x,y]
                    #item.vel = [vx,vy]
                    if isinstance(item, Fireball):
                        if     self.field_size[0] - item.radius - 1 < x or x < item.radius + 1 \
                            or self.field_size[1] - item.radius - 1 < y or y < item.radius + 1:
                            
                            #self.items.remove(item)
                            rem_items.add(item)
                    for other in self.items[::-1]:
                        if other == item:
                            break           
                        else:
                            dist = self.distance(item, other)
                            if dist < INTERACTION_DIST:    
                                if dist < COLLISION_DIST:
                                    item.collide_with(other)  
                                    other.collide_with(item)                                                     
                                else:
                                    item.interact_with(other,dist)
                                    other.interact_with(item,dist)
                    if setvel:
                        item.vel = vec(0,0)

                for rem in rem_items:
                    if rem in self.items:
                        self.items.remove(rem)            
                time_passed = time.time() - start_time
                print(time_passed)
                if time_passed < self.step:
                    time.sleep( self.step - time_passed)
            print('work stopped')
    
    def send(self,message):
        if len(message) == 2 and isinstance(message[0], str) and isinstance(message[1], list):
            self.worker_messages.append(message)

    def proceed_mess(self, message):
#--message = ['action_name',[args]]
        if message[0] == 'add_player':
            if isinstance(message[1][0], Player):
                self.items.append(message[1][0])
                message[1][0].owner = self
        if message[0] == 'add_env':
            if isinstance(message[1][0], Game_obj) and not isinstance(message[1][0], Player):
                self.items.append(message[1][0])
                message[1][0].owner = self
        if message[0] == 'throw_fireball':
            print('throw_fb_bef')
            # message = ['throw_fireball', [ player, magic, direction]]
            [pl, magic, direction ]= message[1]
            if isinstance(pl, Player):
                direc = vec((direction[0], direction[1])).normalized()
                x = pl.coord[0] + direc.x * pl.radius + direc.x*FIREBALL_GAP 
                y = pl.coord[1] + direc.y * pl.radius + direc.y*FIREBALL_GAP               
                fireball = Fireball([x,y],[pl.strength * direc.x + pl.vel.x, pl.strength * direc.y + pl.vel.y], magic)
                self.send(['add_env',[fireball]])     
                print('throw_fb_aft')
        if message[0] == 'move_to':
            #message = ['move_to', direction, player]     
            [player, direction] = message[1]            
            direc = vec((direction[0], direction[1])).normalized()
            player.vel = direc * player.strength*1.5

        if message[0] == 'stop':
            [player] = message[1]
            player.vel = vel(0,0)

    def distance(self, A, B):
        return math.sqrt((A.coord[0] - B.coord[0])**2 + (A.coord[1] - B.coord[1])**2) - A.radius - B.radius
    
    def calc_collision(self, A, B):
        
        if isinstance(A, Fireball):        
            for i in range(0, 3):
                B.magic[i] += A.magic[i]
            A.magic = [0, 0, 0]
        elif isinstance(B, Fireball):
            for i in range(0,3):
                A.magic[i] += B.magic[i]
            B.magic = [0,0,0]
        #else:
        #    A.vel = vec(0,0)
        #    B.vel = vec(0,0)
        #forA.vel = vel(0,0)

    def calc_force(self, item, other, dist, direct_vec):
        
        mg1, mg2 = item.magic, other.magic
        def_force = sum([(mg1[0]+mg2[0]) / dist, mg1[1]+mg2[1] / dist, (mg1[0]+mg2[0]) / dist])                
        if  isinstance(item, Fireball):
            if isinstance(other, Fireball):
                item.force += -def_force * direct_vec
                other.force += def_force * direct_vec
            elif isinstance(other, Player):
                item.force += -other.armor.armor_effect(item.magic, dist) * direct_vec
        
        if isinstance(item, Player) and isinstance(other, Fireball):
                       # -other.effect('Player',item.magic, dist) * direct_vec
            other.force += item.armor.armor_effect(other.magic, dist ) * direct_vec

    def __str__(self):
        return "Server with "+str(len(self.items))+ " items"       

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
         vec_btw = vec(other.coord[0] - self.coord[0], other.coord[1] - self.coord[1])
         direct_vec=vec_btw.normalized()
         dist = vec_btw.length
         overlay = self.radius + other.radius - dist
         #print(dist,overlay)
         v1_direc = self.vel.convert_to_basis(direct_vec, direct_vec.perpendicular_normal())
         #v2_direc = other.vel.convert_to_basis(direct_vec, direct_vec.perpendicular_normal())
         if  (-math.pi/2 < v1_direc.angle < math.pi/2): 
         #'''and   (math.pi/2 < v1_direct < 3*math.pi/4):'''  
              self.coord[0] -= direct_vec.x * (lambda x:  x if x < 2   else  x**2)( overlay) #100 / dist - 20 * self.force.x
              self.coord[1] -= direct_vec.y *  (lambda x:  x if x < 2   else  x**2)( overlay) #* self.force.y
              other.force += self.vel#/ other.inertia
              self.vel = vec(0,0)
              #other.vel = vec(0,0)
    def interact_with(self, other, dist):    
        #other.force+=vec(30,30)
        pass
    def effect(self, obj_type, magic, dist):
        if obj_type == 'Fireball':
            #return sum(x[0] * x[1] for x in zip(magic, self.magic)) / dist
            return sum([magic[0]*dist/20, magic[1], magic[2] / 20*dist])            
        if obj_type == 'Player':
            return 
class Player(Game_obj):
    def __init__(self, coord=[100, 100] , vel=[0,0], magic=[10,10,10]):
        super(Player, self).__init__(coord, vel, magic)
        self.radius = 15
        self.strength = 120        
        self.life_space = ([1,1000], [1,1000], [1,1000])
        self.armor = Armor(self)

    def throw_fireball(self, magic, direction ):
        if self.owner:
            self.owner.send(['throw_fireball',[self, magic, direction]])
    
    def move_to(self, direction):
        if self.owner:
            self.owner.send(['move_to',[self, direction]])

class Fireball(Game_obj):
    def __init__(self, coord=[100, 100] , vel=[0,0], magic=[ 1, 1, 1]):
        super(Fireball, self).__init__(coord, vel, magic)
        self.radius = 5

class Armor:
    def __init__(self, player, effect = None):
        self.owner = player
        self.effect = effect
        #player.magic =[x*10 for x in player.magic]
    
    def armor_effect(self, magic, dist):
        if self.effect:
            return self.effect( magic, dist)        
        else:
            return 0


      
