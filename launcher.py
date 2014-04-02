import tkinter as tk
import server
import client

DEFAULT_PORT = 9043
MAX_PLAYERS = 20

def run_serv(server, started):
    if not started:
        started = True   
        server.start()

def join_game(addr, name, password):
    print(addr,name,password)
    if isinstance(addr, str) and isinstance(name, str) and isinstance(password, str):
        client.game(addr, DEFAULT_PORT, name, password)

serv = server.Server(DEFAULT_PORT, MAX_PLAYERS)

window = tk.Tk()
window.geometry('320x120')
window.resizable(0,0)

launcher_name = tk.Label(window, text="Super launcher 9000").grid(row=0,column=0)

addr_label = tk.Label(window, text='Ip:').grid(row=1,column=0)
addr_entr = tk.Entry(window,width=21)
addr_entr.grid(row=1,column=1)

name_label = tk.Label(window, text='Name:').grid(row=2,column=0)
name_entr = tk.Entry(window,width=21)
name_entr.grid(row=2,column=1)

pass_label = tk.Label(window, text='Password:').grid(row=3,column=0)
password_entr = tk.Entry(window,width=21)
password_entr.grid(row=3,column=1)

join_button = tk.Button(window, text='Join', command = lambda: join_game(addr_entr.get(), name_entr.get(), password_entr.get())).grid(row=4,column=0)

started = False
start_button = tk.Button(window, text='Run server', command = lambda: run_serv(serv, started) ).grid(row=4,column=1)


def exit_launcher(server):
    server.running = False
    window.destroy()

window.protocol('WM_DELETE_WINDOW', lambda: exit_launcher(serv))
window.mainloop()


