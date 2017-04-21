"""
Программа "Змейка" - клиентский модуль
Чтобы убедиться, что данные приходят по сети, 
а не берутся из глобальных переменных
"""
from snakecommon import *
import threading
import os
import pickle
import socket
import sys
import time
import pygcurse.pygcurse as pygcurse
import pygame
from pygame.locals import *

def clientProcessFunction(options):

  fieldAreaX=1
  fieldAreaY=1
  fieldH = fieldHeightMax+2
  fieldW = fieldWidthMax+2
  playersAreaW = 13
  playersAreaX = fieldW
  playersAreaY = 1
  statAreaH = 3
  statAreaW = 12
  statAreaX = 1
  statAreaY = fieldH
  windowW = fieldW + playersAreaW
  windowH = fieldH + statAreaH

  gameOver=False
  fns=None
  players=None
  message=''

  def draw(drawBorder=False, drawFns=False, drawPlayers=False, drawMessage=False):
    """
    Рисование всего
    """

    win.fgcolor = 'gray'
    #Вывод списка игроков
    if drawPlayers and players:
      #TODO: сортировка игроков, пока криво
      p=0
      for player in players:
        string = 'X' if fns.snakes[p].dead else ('+' if players[player].ready else ' ')
        string += '*' if players[player].isAdmin else ' '
        string += str(p+1) + ' ' + player
        win.putchars(string, x=playersAreaX, y=playersAreaY+p, fgcolor=snakeColors[p])
        p += 1
      for p in range(len(players),len(fns.snakes)):
        string = '  ' +str(p+1)+'<waiting>'
        win.putchars(string, x=playersAreaX, y=playersAreaY+p, fgcolor=snakeColors[p])
    #Вывод сообщения
    if drawMessage:
      win.fill(' ', region=(statAreaX, statAreaY, windowW, statAreaH)) #statAreaW
      win.putchars(message, x=(windowW-len(message))//2, y=statAreaY+statAreaH//2, fgcolor='white') 
    #Рисование границ поля
    if drawBorder:
      win.fill('X', region=(0,0,fieldW, fieldH))
    #Рисование поля
    if drawFns and fns:
      for y in range(fns.H):
        win.cursor=(1, y+1)
        win.write(fns.field[y])
      #Рисование вишенок
      for cherry in fns.cherries:
        (x,y)=cherry
        win.putchars(cherrySymbol, x=x+1, y=y+1, fgcolor='maroon')
      #Если змея мертвая,оставить след
      #лучший способ чем два цикла?
      for snake in fns.snakes: 
        if not snake.dead: continue
        for segment in snake.coords:
          (x,y)=segment
          win.putchars(fns.field[y][x], x=x+1, y=y+1, fgcolor=snake.color)
      #Рисование живых змей
      for snake in fns.snakes: 
        if snake.dead: continue
        #Голова змеи
        segment = snake.coords[0]
        (x,y)=segment
        win.putchars(snakeHeadSymbol, x=x+1, y=y+1, fgcolor=snake.color)
        #Тело змеи
        for segment in snake.coords[1:]:
          (x,y)=segment
          win.putchars(snakeSymbol, x=x+1, y=y+1, fgcolor=snake.color)
  ##############################
  # end of draw()
  ##############################

  
  win = pygcurse.PygcurseWindow(windowW, windowH, 'Snakes' ) 
                                    #font=pygcurse.pygame.font.Font(None, 32)
  cname=options['player name']

  """ При устанвке соединения последовательно открываются два сокета:
  первый - для записи,  второй - для чтения.
  Каждый отправляет свой режим работы и имя игрока
  """
  sockRecv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  try:
    sockRecv.connect((options['IP'],options['port']))
  except ConnectionRefusedError:
    print('Connection refused by server')
    sockSend.close()
    return
  msg=pickle.dumps(('RECV',cname))  #+PACKET_END  на авось :)
  sockRecv.send(msg) 

  sockSend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  try:
    sockSend.connect((options['IP'],options['port']))
  except ConnectionRefusedError:
    print('Connection refused by server')
    return
  msg=pickle.dumps(('SEND',cname))  #+PACKET_END  на авось :)
  sockSend.send(msg) 

  print("CLIENT {0} PID={1}".format(cname,os.getpid()) )


  def send(string,data=''):
    msg=pickle.dumps((string,data))+PACKET_END
    try:
      sockSend.send(msg)
      #print("CLIENT {0} sent {1} bytes".format(cname,len(msg) ) )
    except ConnectionResetError:
      print('CLIENT: Connection reset by server')
      exit()

  def clientListenFunction():
   """
   Обрабатывает информацию от сервера
   """
   #print('CLIENT '+cname+' listening...')
   nonlocal gameOver
   nonlocal fns
   nonlocal players
   nonlocal message

   buffer=b''
   while not gameOver:
    try:
     block = sockRecv.recv(1024)
     if not block:
       return
     buffer += block
     #print('CLIENT '+cname+' received {0} bytes'.format(len(block)))

     index=buffer.find(PACKET_END)
     
     while index>=0:
       msg=buffer[0:index]
       data=pickle.loads(msg)
       if data[0]=='FNS':
         fns=data[1]
         #print('CLIENT '+cname+' received FNS data')
         draw(drawFns=True)
       elif data[0]=='PLAYERS':
         #print('CLIENT '+cname+' received PLAYERS data')
         players=data[1]
         draw(drawPlayers=True)
       elif data[0]=='MESSAGE':
         #print('CLIENT '+cname+' received MESSAGE '+data[1])
         message=data[1]
         draw(drawMessage=True)
       elif data[0]=='GG':
         gameOver=True

       buffer=buffer[index+len(PACKET_END):]
       index=buffer.find(PACKET_END)
     # end of while index>=0 #
     #########################
    except ConnectionResetError:
      print('Connection terminated by server')
      return
  #################################
  # end of clientListenFunction() #
  #################################

  draw(drawBorder=True)
  thr = threading.Thread(target=clientListenFunction)
  thr.daemon = True
  thr.start()
  #Основной цикл
  while not gameOver:
    time.sleep(0.1)
    for event in pygame.event.get():
      if event.type == QUIT:
        gameOver=True #Избыточно
        send('DISCONNECT','')
        pygame.quit()
        sys.exit()
      elif event.type == KEYDOWN: 
        if event.key == K_F4 and (event.mod & KMOD_LALT or event.mod & KMOD_RALT):
          send('DISCONNECT','')
          gameOver=True #Избыточно
          pygame.quit()
          sys.exit()
        elif event.key == K_SPACE:
          send('READY','')
        elif event.key in (K_a, K_LEFT):
          send('direction','L')
        elif event.key in (K_d, K_RIGHT):
          send('direction','R')
        elif event.key in (K_w, K_UP):
          send('direction','U')
        elif event.key in (K_a, K_DOWN):
          send('direction','D')
        elif event.key == K_KP_PLUS:
          send('speed',1)
        elif event.key == K_KP_MINUS:
          send('speed',-1)
    
  #КОНЕЦ ИГРЫ
  #Закрытие сокетов
  print("CLIENT " + cname + " closing")
  sockRecv.close()
  send('DISCONNECT','')
  sockSend.close()
  #Игнорирование оставшихся событий 
  for event in pygame.event.get():
    pass
  #Ожидание нажатия клавиши по окончанию игры
  pygcurse.waitforkeypress()
  print("CLIENT " + cname + " closed")
