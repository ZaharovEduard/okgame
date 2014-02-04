import threading
import time
import math
from pymunk.vec2d import Vec2d as vec
#from main_objects import *
from phys import *
from net import *
import queue

class Server(threading.Thread):
    def __init__(self, port, max_users):
        super(Server, self).__init__()
        self.game = None
        self.all_players = {}
        self.gameitems =[]
        
        self.mess_queue = queue.Queue()
        self.messenger = Messenger(self.mess_queue, port, max_users)
        #all_players = { name: [password, bool-Online?, player]}
        self.gameque = queue.Queue()

    def run(self):        
        #print('server work started')
        self.running = True
        self.game = Physics_server(qmes=self.gameque, owner=self)     
        self.game.start()        
        self.messenger.start()
        self.work()
        self.messenger.runn = False
        self.game.running = False

    def work(self):
        while self.running:
            while not self.mess_queue.empty():
                r_msg = self.mess_queue.get() 
                self.proceed_mess(r_msg)
        #print('server work stopped')
                
        
    def proceed_mess(self, message):
        #print('proceed_mess')
        # message = ['name', 'password', 'comand', 'arguments']
        if message[2] == 'register':
            #print('register')
            # ['name', 'password', 'register']
            name, password = message[0], message[1]
            if not name in self.all_players:
                self.all_players[name] = [password, False , Player(coord = (random.randrange(200),random.randrange(100)))] #repair here
            #else:
                #print('Player name is already taken')
        else:
             player_instance = self.check_login( message[0], message[1])  
             if player_instance:
                self.exec_mess(player_instance, message[2:])
    
    def check_login(self, name, password): 
        if name in self.all_players:
            player = self.all_players[name]
            if player[0] == password:
                return name, player
            else:
                return False
        else:
            return False


    def exec_mess(self, name_and_player, message):
        name, [_, _,player] = name_and_player
        #print(player, message)
        if message[0] == 'join_game':
            #message = ['join_game']
            self.all_players[name][1] = True                                    
            self.gameque.put(['add_item', player])  
      
        elif message[0] == 'leave_game':
            #message = ['leave_game']
            self.all_players[name][1] = False            
            self.gameque.put(['remove_item', player]) 
      
        
        elif message[0] == 'alive':
            #message = ['alive']
            [x,y] = player.coord
            [m1, m2, m3] = player.magic
            player_info = [str(x),str(y),str(m1),str(m2),str(m3)]
            send_message_to(self.messenger, name, player_info + self.gameitems)

        elif message[0] == 'move_to':
            #message = ['move_to', 'x', 'y']
            direction = [float(message[1]), float(message[2])]
            player.move_to( direction )

        elif message[0] =='throw_fireball':
            #message = ['throw_fireball', 'mag1', 'mag2' mag3', 'x', 'y']
            magic = [ int(message[1]), int(message[2]), int(message[3])]
            direction = [ float(message[4]), float(message[5]) ]
            player.throw_fireball(magic, direction)

        elif message[0] == 'to_game':
            #['to_game, [to game message]]
            #self.gameque.put(message+[player])
            print(message)
