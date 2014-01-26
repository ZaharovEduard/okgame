import threading
import time
import math
from pymunk.vec2d import Vec2d as vec
#from main_objects import *
from ok import *
import queue
class Wires():
    def __init__(self): 
        self.data = {}
        self.input = []
        self.output = []

    def read(self, port):
        if port in self.data:
            dat = self.data[port]
            #if dat == []:
            #    return []
            #else:
            #    out = self.data[port][0]
            #    self.data[port] = self.data[port][1:]
            self.data[port] = []            
            return dat
        else:
            return []

    def write(self, port, write_data):
        if not port in self.data:
            self.data[port] = []
        self.data[port].append(write_data)
#////////////////////////////////////////////////////////////////////////////

class Server(threading.Thread):
    def __init__(self, inq, outq, gameq):
        super(Server, self).__init__()
        self.inq = inq
        self.outq =outq
        self.game = None
        self.gameque = gameq   
        self.all_players = {}
        self.ud = -random.randrange(1000)
        #all_players = { name: [password, bool-Online?, player]}

    def run(self):
        self.running = True
        print(11)
        #self.gameque = queue.Queue()
        self.game = Cust_Physics_server(qmes=self.gameque, owner=self.ud)
        print(12)        
        self.game.start()
        print(13)
        self.work()
    def work(self):
        print('server work started')
        while self.running:
           rmsg = self.inq.get()
           self.proceed_mess(rmsg)
        print('server wokr stopped')
    def proceed_mess(self, message):
        # message = [comand, [args]]
        if message[0] == 'register':
            # ['register' , [name, password]]
            name, password = message[1][0], message[1][1]
            if not name in self.all_players:
                self.all_players[name] = [password, False , Player(coord = (random.randrange(200),random.randrange(100)))]
        

        elif message[0] == 'join_game':
            #['join_game', [name, password]]
            name , password = message[1][0], message[1][1]
            if name in self.all_players and password == self.all_players[name][0] and not self.all_players[name][1]:
                    self.all_players[name][1] = True                    
                    self.gameque.put(['add_player', [self.all_players[name][2]], self])        
        elif message[0] == 'leave_game':
            #['leave_game', [name, password]]
            name , password = message[1][0], message[1][1]
            if name in self.all_players and password == self.all_players[name][0]:
                self.all_players[message[1][0]][1] = False
                self.gameque.put(['remove', self.all_players[name],self])     
        
        elif message[0] == 'to_game':
            #['to_game, [to game message]]
            if self.game:
                if isinstance(message[1]): 
                    self.game.send(message[1])        
        elif message[0] == 'exit':
            #self.gameque.put(['exit']) 
            self.game.running = False           
            self.running = False

    def listen(self):
        pass    
    def give_data(self):    
        pass
    def set_game_settings(self):
        pass
    def startgame(self):
        pass
