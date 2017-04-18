"""
Программа "Змейка" - клиентский модуль
Чтобы убедиться, что данные приходят по сети, 
а не берутся из глобальных переменных
"""
from snakecommon import *

import socket

def clientProcessFunction(fns, options):
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.connect((options['IP'],options['port']))
  msg='player name='+options['player name']
  sock.send(msg.encode('ascii')) 
  sock.close()
  print("CLIENT closing")