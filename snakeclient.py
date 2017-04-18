"""
Программа "Змейка" - клиентский модуль
Чтобы убедиться, что данные приходят по сети, 
а не берутся из глобальных переменных
"""
from snakecommon import *

import pickle
import socket

def clientProcessFunction(options):
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.connect((options['IP'],options['port']))
  msg='player name='+options['player name']
  sock.send(msg.encode('ascii')) 
  msg=sock.recv(102400)
  fns=pickle.loads(msg)
  print("CLIENT received fns=" + str(fns))
  print("CLIENT nSnakes={0}, nCherries={1}, field[0][0]={2} ".format(len(fns.snakes),len(fns.cherries),fns.field[0][0]))
  sock.close()
  print("CLIENT closing")