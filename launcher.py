import tkinter as tk
import server
import client

DEFAULT_PORT = 9044
MAX_PLAYERS = 20

class App:
    def __init__(self):
        self.window = tk.Tk()
        self.window.geometry = ('320x320')
        self.window.resizable(1,1)
        self.game_name = tk.Label(self.window, text="Super launcher 9000").grid(row=0,column=0)
        self.addr_label = tk.Label(self.window, text='Ip:').grid(row=1,column=0)
        self.addr_entr = tk.Entry(self.window,width=21)
        self.addr_entr.grid(row=1,column=1)
        self.name_label = tk.Label(self.window, text='Name:').grid(row=2,column=0)
        self.name_entr = tk.Entry(self.window,width=21)
        self.name_entr.grid(row=2,column=1)
        self.pass_label = tk.Label(self.window, text='Password:').grid(row=3,column=0)
        self.password_entr = tk.Entry(self.window,width=21)
        self.password_entr.grid(row=3,column=1)
        self.join_button = tk.Button(self.window, text='Join', command = self.join_game)
        self.join_button.grid(row=4,column=0)
        self.server_change = tk.Button(self.window, text='Run server', command = self.change_server_state)
        self.server_change.grid(row=4,column=1)
        self.run_state = True
    
    def join_game(self):
        address = self.addr_entr.get()
        name = self.name_entr.get()
        password = self.password_entr.get()
        client.game(address, DEFAULT_PORT, name, password)
    
    '''def stop_server(self):
        try:
            self.server.running = False
        except AttributeError:
            pass
        finally:
            
            self.start_button.config(state=tk.NORMAL)'''

    def change_server_state(self):
        if self.run_state:
            self.server = server.Server(DEFAULT_PORT, MAX_PLAYERS)
            self.server.start() 
            self.server_change.config(text='Stop server')
            self.run_state = False
        else:
            try:
                self.server.running = False
            except AttributeError:
                pass
            finally:
                self.server_change.config(text='Start server')
                self.run_state = True     

    def run_server(self):
        self.server = server.Server(DEFAULT_PORT, MAX_PLAYERS)
        self.server.start()
        self.start_button.config(state=tk.DISABLED)
    
    def close_launcher(self):
        try:
            self.server.running = False
        except AttributeError:
            pass
        finally:
            self.window.destroy()

    def start(self):
        self.window.protocol('WM_DELETE_WINDOW', self.close_launcher)
        self.window.mainloop()

if __name__ == '__main__':
    app = App()
    app.start()
