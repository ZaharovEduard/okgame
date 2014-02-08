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
        self.logged_players = {}
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
        
    def proceed_mess(self, message):
        # message = ['comand', 'name', 'arguments']
        if message[0] == 'join_game':
            name, password = message[1], message[2]       
            if name in self.all_players:
                if password == self.all_players[name][0]:
                    self.logged_players[name] = self.all_players[name][1]
                    self.game.spawner.spawn(self.logged_players[name])
                    game_info = [str(self.game.field_size[0]), str(self.game.field_size[1])]
                    send_message_to(self.messenger, name, game_info)
            else:
                self.all_players[name] = [password, Player()]
                self.logged_players[name] = self.all_players[name][1]
                self.game.spawner.spawn(self.logged_players[name])
                game_info = [str(self.game.field_size[0]), str(self.game.field_size[1])]
                send_message_to(self.messenger, name, game_info)
        else:
            if message[1] in self.logged_players:
                self.exec_mess(self.logged_players[message[1]], message)
            else:
                send_message_to(self.messenger, message[1], ['not_logged'])


    def exec_mess(self, player, message):
        if message[0] == 'alive':
            #message = ['alive', 'name']
            [x,y] = player.coord
            [m1, m2, m3] = player.magic
            player_info = [str(round(x)),str(round(y)),str(m1),str(m2),str(m3)]
            send_message_to(self.messenger, message[1], player_info + self.gameitems)

        elif message[0] == 'move_to':
            #message = ['move_to', 'name', 'x', 'y']
            direction = [float(message[2]), float(message[3])]
            player.move_to( direction )

        elif message[0] =='throw_fireball':
            #message = ['throw_fireball', 'name', 'mag1', 'mag2' mag3', 'x', 'y']
            magic = [ int(message[2]), int(message[3]), int(message[4])]
            direction = [ float(message[5]), float(message[6]) ]
            player.throw_fireball(magic, direction)

        elif message[0] == 'pick_up':
            #message = ['pick_up', name]
            player.pick_up()

        elif message[0] == 'leave_game':
            #message = ['leave_game', 'name']         
            self.gameque.put(['remove_item', player])
            del self.logged_players[message[1]]
      
        else:
            pass
