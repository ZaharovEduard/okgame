import threading
import time
import random
import math
import multiprocessing 
from pymunk.vec2d import Vec2d as vec
from functools import reduce
from main_objects import *
from server import *
import queue
from queue import Full, Empty
FIREBALL_GAP = 20
INTERACTION_DIST = 200
COLLISION_DIST = 0.1
MIN_MAGIC = 1

lock = threading.Lock()


class Physics_server(threading.Thread):

    def __init__(self, qmes, owner=None, size=(800,600), step=0.01):
        super(Physics_server, self).__init__()
        self.step = step
        self.items = []
        self.field_size = size
        self.owner = owner
        self.running = False
        self.qmes = qmes
        self.data = 0
        self.messages = []
        self.isalive = True
        self.ud = random.randrange(1000)

    def run(self):
        self.running = True
        self.work()
    def work(self):
            print('game work started')
            while self.running:
                start_time = time.time()
#---------------Message processing--------                
                mess_size = self.qmes.qsize() 
                if mess_size != 0:
                    for i in range(1, mess_size):
                        
                        mess = self.qmes.get()            
                        self.proceed_mess(mess)
#----------------All interactions---------
                rem_items = set([]) 
                if self.running:
                  for item in self.items:
                    ls = item.life_space
                    mg = item.magic                    
                     
                    if not    (ls[0][0] < mg[0] < ls[0][1] and ls[1][0] < mg[1] <ls[1][1] and ls[2][0] < mg[2] < ls[2][1]) \
                                or (reduce(lambda x,y: x*y, [abs(check) < MIN_MAGIC for check in mg])):                        
                        rem_items.add(item)                        
                    
                    vx, vy = item.vel.x + item.force.x/item.inertia, item.vel.y + item.force.y/item.inertia
                    dx,dy = vx * self.step, vy * self.step
                    x = item.coord[0]+dx
                    y = item.coord[1]+dy 
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
                    if isinstance(item, Fireball):
                        if     self.field_size[0] - item.radius - 1 < x or x < item.radius + 1 \
                            or self.field_size[1] - item.radius - 1 < y or y < item.radius + 1:
                            rem_items.add(item)
                    for other in self.items[::-1]:
                        if other == item:
                            break     
                        otmag = other.magic
                        ls = other.life_space
                        if not    (ls[0][0] < otmag[0] < ls[0][1] and ls[1][0] < otmag[1] <ls[1][1] and ls[2][0] < otmag[2] < ls[2][1]) \
                           or (reduce(lambda x,y: x*y, [abs(check) < MIN_MAGIC for check in mg])):                   
                            rem_items.add(other)      
                        else:
                            dist = self.distance(item, other)
                            if dist < INTERACTION_DIST:    
                                if dist < COLLISION_DIST:
                                    item.collide_with(other)  
                                    other.collide_with(item)                                                     
                                else:
                                    item.interact_with(other)
                                    other.interact_with(item)
                    
                    if setvel:
                        item.vel = vec(0,0)           
                time_passed = time.time() - start_time
                for rem in rem_items:
                    if rem in self.items:
                        self.items.remove(rem)                
                if time_passed < self.step:
                    time.sleep( self.step - time_passed)
#-------------------------------------------
            print('game work stopped')
    
    def proceed_mess(self, message):
#--message = ['action_name',[args]]
        
        if message[0] == 'add_player':
            # message = ['add_player', [player], sender]
            player, sender = message[1][0], message[2]
            #if sender == self.owner:
            if isinstance(player, Player):
                    self.items.append(player)
                    player.owner = self

        elif message[0] == 'add_env':
            # message = ['add_env', [item], sender]
            #if isinstance(message[2][0], Player) and isinstance(message[1][0], Fireball) or \
             #  isinstance(message[1][0], Game_obj) and not isinstance(message[1][0], Player) :
                self.items.append(message[1][0])
                message[1][0].owner = self

        elif message[0] == 'remove':
            #message = ['remove',[item], sender]
            if message[1][0] in self.items:                    
                self.items.remove(message[1][0])
        
        elif message[0] == 'throw_fireball':
            # message = ['throw_fireball', [ magic, direction], sender]
            magic, direction = message[1][0],message[1][1]
            pl = message[2]
            if pl in self.items and isinstance(pl, Player) :
                
                direc = vec((direction[0], direction[1])).normalized()
                x = pl.coord[0] + direc.x * pl.radius + direc.x*FIREBALL_GAP 
                y = pl.coord[1] + direc.y * pl.radius + direc.y*FIREBALL_GAP             
                fireball = Fireball([x,y],[pl.strength * direc.x + pl.vel.x, pl.strength * direc.y + pl.vel.y], magic)
                can_throw = True                
                for item in self.items:
                    if can_throw:
                        if vec(x - item.coord[0], y - item.coord[1]).length < item.radius + fireball.radius + 1:
                            can_throw = False
                    else:
                        break
                if can_throw: 
                    
                    self.proceed_mess(['add_env',[fireball], message[2]])     
        elif message[0] == 'move_to':
            #message = ['move_to', [direction], sender]]
            player, direction = message[2], message[1][0] 
            if player in self.items:
               
                direc = vec((direction[0], direction[1])).normalized()
                player.vel = direc * player.strength*1.5

        elif message[0] == 'stop':
            #message = ['stop', sender]]
            item = message[1]
            if item in self.items:
                item.vel = vel(0,0)

        elif message[0] == 'hit':
            #message = ['hit',[magic, item], sender]
            mag = message[1][0]
            item = message[1][1]
            if item in self.items:
                #if isinstance(item, Player):
                #    item.magic = [m+dm for m, dm in zip(item.magic, item.armor.make_impact(mag))]
                #else:
                    item.magic = [round(m+dm) for m, dm in zip(item.magic, mag)]

        elif message[0] == 'add_force':
            #message = ['add_force', [force,item],sender]
  
            item = message[1][1]            
            if item in self.items:
                force = message[1][0]
                item.force+=force

        elif message[0] == 'add_coord':
            #message = ['add_coord', [add_coor, item], sender]
            item = message[1][1]
            add_coor = message[1][0]
            if item in self.items:
                item.coord[0] +=add_coor[0]
                item.coord[1] +=add_coor[1]

        elif message[0] == 'set_vel':
            #message=['set_vel',[vec,item], sender]
            if message[1][1] in self.items:
                message[1][1].vel = message[1][0]
        elif message[0] == 'exit':# and message[1] == self.owner:
            self.running = False
          
    def distance(self, A, B):
        return math.sqrt((A.coord[0] - B.coord[0])**2 + (A.coord[1] - B.coord[1])**2) - A.radius - B.radius
    
    def __str__(self):
        return "Server with "+str(len(self.items))+ " items"       

class Cust_Physics_server(Physics_server):
    def __init__(self, qmes, owner=None, size=(800,600), step=0.01):
        super(Cust_Physics_server, self).__init__(qmes, owner=None, size=(800,600), step=0.01)
                
        self.items = [Player([300,400],[0, 0], [100,100,100]),
    Player([400,300],[10,0], [100,100,100]),
     Player([30,500],[0,0], [100,100,100]),
    Player([700,300],[0,0], [100,100,100])]

