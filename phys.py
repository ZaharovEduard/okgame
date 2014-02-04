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

class Physics_server(threading.Thread):

    def __init__(self, qmes, owner, size=(800,600), step=0.01):
        super(Physics_server, self).__init__()
        self.step = step
        self.items = []
        self.field_size = size
        self.owner = owner
        self.running = False
        self.qmes = qmes

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
                    for i in range(0, mess_size):
                        
                        mess = self.qmes.get()            
                        self.proceed_mess(mess)
#----------------All interactions---------
                rem_items = set([])
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
                
                for rem in rem_items:
                    if rem in self.items:
                        self.items.remove(rem)

                items_str = []
                for item in self.items:
                    items_str += [ str(round(item.coord[0])), str(round(item.coord[1])), str(round(item.radius))]
                self.owner.gameitems = items_str

                time_passed = time.time() - start_time    
                #print(time_passed)
                if time_passed < self.step:
                    time.sleep( self.step - time_passed)
#-------------------------------------------
            #print('game work stopped')
    
    def distance(self, A, B):
        return math.sqrt((A.coord[0] - B.coord[0])**2 + (A.coord[1] - B.coord[1])**2) - A.radius - B.radius
    
    def proceed_mess(self, message):
        '''message = ['action_name',args]
        
        if message[0] == 'add_player':
            # message = ['add_player', player]
            player = message[1]
            if isinstance(player, Player):
                self.items.append(player)
                player.owner = self
        '''
        
        #print(message)
        if message[0] == 'add_item':
            # message = ['add_item', item]
            item = message[1]
            canadd = True
            for other in self.items:
                if self.distance(item, other) < COLLISION_DIST:              
                    canadd = False                
            if canadd:            
                self.items.append(item)
                item.owner = self            

        elif message[0] == 'remove_item':
            #message = ['remove_item',item]
            item=message[1]
            if item in self.items:                    
                self.items.remove(item)

        elif message[0] == 'hit_item':
            #message = ['hit', magic1, magic2, magic3, item]
            [mag1, mag2, mag3, item] = message[1:]
            if item in self.items:
                    item.magic = [round(m+dm) for m, dm in zip(item.magic, [mag1,mag2,mag3])]

        elif message[0] == 'add_force':
            #message = ['add_force', fx, fy , item]
            [fx, fy, item] = message[1:]           
            if item in self.items:
                item.force += vec(fx, fy)
        
        elif message[0] == 'add_vel':
            #message = ['add_vel', vx, vy, item]
            [vx, vy, item] = message[1:]
            if item in self.items:
                item.vel += vec(vx,vy)       

        elif message[0] == 'add_coord':
            #message = ['add_coord', x, y, item]
            [x, y, item] = message[1:]
            if item in self.items:
                item.coord[0] += x
                item.coord[1] += y
        
        elif message[0] == 'set_force':
            #message = ['set_force', fx,fy, item]    
            [fx,fy, item] = message[1:]
            if item in self.items:
                item.force = vec(fx,fy)
        elif message[0] == 'set_vel':
            #message=['set_vel', vx, vy, item]
            [vx, vy, item] = message[1:]
            if item in self.items:
                item.vel = vec(vx,vy)
        elif message[0] == 'set_coord':
            #message = ['set_coord', x, y, item]
            [x,y, item] = message[1:]
            if item in self.items:
                item.coord = coor
        #elif message[0] == 'get_items':
            #message = ['get_items']
        #    items_shell = [(it.coord, it.radius) for it in self.items]
        #    self.out_itemsq.put(items_shell)
          
    
    def __str__(self):
        return "Server with "+str(len(self.items))+ " items"       

class Cust_Physics_server(Physics_server):
    def __init__(self, qmes, owner, size=(800,600), step=0.01):
        super(Cust_Physics_server, self).__init__(qmes, owner, size=(800,600), step=0.01)
                
        self.items = [Player([300,400],[0, 0], [100,100,100]),
    Player([400,300],[10,0], [100,100,100]),
     Player([30,500],[0,0], [100,100,100]),
    Player([700,300],[0,0], [100,100,100])]

