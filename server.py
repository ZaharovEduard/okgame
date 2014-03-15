import threading
import time
import math
from pymunk.vec2d import Vec2d as vec
#from main_objects import *
from phys import *
from net import *
import queue

REFRESH_TIME = 0.02
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
        def sr(x):
            return str(round(x))
        while self.running:
            start_time = time.time()
            while not self.mess_queue.empty():
                r_msg = self.mess_queue.get() 
                self.proceed_mess(r_msg)
            for player_name, player in self.logged_players.items():
                [x,y] = player.coord
                [m1, m2, m3] = player.magic
                invent = []
                for item in player.inventory:
                    if item.obj_type == 'armor':
                        invent += ['armor'] + [sr(x) for x in item.action] + [sr(x) for x in item.impact]
                    else:
                        invent += [item.obj_type] + [sr(x) for x in item.magic]
                player_info = [sr(item) for item in (x,y,m1,m2,m3)] + invent
                send_message_to(self.messenger, player_name, player_info +['lim'] +self.gameitems)
            passed_time = time.time() - start_time
            if passed_time < REFRESH_TIME:
                time.sleep(REFRESH_TIME - passed_time)
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
            if message[0] in self.logged_players:
                self.exec_mess(self.logged_players[message[0]], message)
            else:
                send_message_to(self.messenger, message[0], ['not_logged'])


    def exec_mess(self, player, message):
        '''if message[1] == 'alive':
            #message = ['name','alive']
            [x,y] = player.coord
            [m1, m2, m3] = player.magic
            invent = []
            def sr(x):
                return str(round(x))
            for item in player.inventory:
                if item.obj_type == 'armor':
                    invent += ['armor'] + [sr(x) for x in item.action] + [sr(x) for x in item.impact]
                else:
                    invent += [item.obj_type] + [sr(x) for x in item.magic]
            player_info = [sr(x),sr(y),sr(m1),sr(m2),sr(m3)] + invent
            send_message_to(self.messenger, message[0], player_info)
            send_message_to(self.messenger, message[0], self.gameitems)'''

        if message[1] == 'move_to':
            #message = ['name','move_to', 'x', 'y']
            try:
                direction = [float(drct) for drct in message[2:4]]
            except:
                return
            player.move_to( direction )

        elif message[1] =='throw_fireball':
            #message = ['name', 'throw_fireball', 'mag1', 'mag2' mag3', 'x', 'y']
            try:
                magic = [ int(mg) for mg in message[2:5]]
                direction = [ float(drct) for drct in message[5:7]]
            except:
                return            
            player.throw_fireball(magic, direction)

        elif message[1] == 'pick_up':
            #message = ['name', 'pick_up']
            player.pick_up()
    
        elif message[1] == 'drop_item':
            #message = ['name' 'drop_item', 'index']
            try:            
                index = int(message[2])
            except:
                return
            player.drop_item(index)
        
        elif message[1] == 'put_on':
            #message = ['name','put_on',  'index']
            try: 
                num = int(message[2]) 
            except:
                return
            player.put_on(num)

        elif message[1] == 'leave_game':
            #message = ['name', 'leave_game']         
            self.gameque.put(['remove_item', player])
            del self.logged_players[message[0]]
      
        else:
            return
