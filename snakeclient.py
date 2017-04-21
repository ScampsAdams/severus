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
import lib.pygcurse.pygcurse as pygcurse
import pygame
from pygame.locals import *

def clientProcessFunction(options):

  fieldAreaX = 1
  fieldAreaY = 1
  fieldAreaH = fieldHeightMax + 2
  fieldAreaW = fieldWidthMax + 2
  playersAreaW = 5 + PLAYER_NAME_MAX_LEN + 2
  playersAreaH = MAX_PLAYERS + 2
  playersAreaX = fieldAreaW
  playersAreaY = 0
  browserAreaW = playersAreaW
  browserAreaH = max(8, fieldAreaH-playersAreaH)
  browserAreaX = fieldAreaW
  browserAreaY = playersAreaH
  statAreaH = 3
  statAreaW = fieldAreaW + playersAreaW
  statAreaX = 0
  statAreaY = max(fieldAreaH, playersAreaH + browserAreaH)
  windowW = fieldAreaW + playersAreaW
  windowH = max(fieldAreaH, playersAreaH + browserAreaH) + statAreaH

  gameOver=False
  fns=None
  players=None
  message=''
  browser=None

  def draw(drawBorder=False, drawFns=False, drawPlayers=False, drawMessage=False, drawBrowser=False):
    """
    Рисование всего
    """

    win.fgcolor = 'gray'
    #Вывод списка игроков
    if drawPlayers and players:
      #playersList=list(players)
      win.fill(' ', region=(playersAreaX, playersAreaY, playersAreaW, playersAreaH))
      p=0
      for player in players:
        if p<len(fns.snakes):
          string = 'X' if fns.snakes[p].dead else ('+' if players[player].ready else ' ')
          string += ' *' if players[player].isAdmin else '  '
          string += str(p+1) + ' ' + player
          win.putchars(string, x=playersAreaX+1, y=playersAreaY+1+p, fgcolor=snakeColors[p])
        else:
          string = 'spec '+ player
          win.putchars(string, x=playersAreaX+1, y=playersAreaY+1+p, fgcolor='gray')
        p += 1
      for p in range(len(players),len(fns.snakes)):
        string = '   ' +str(p+1)+' <waiting>'
        win.putchars(string, x=playersAreaX+1, y=playersAreaY+1+p, fgcolor=snakeColors[p])
    #Вывод сообщения
    if drawMessage:
      win.fill(' ', region=(statAreaX, statAreaY, statAreaW, statAreaH))
      win.putchars(message, x=statAreaX+(statAreaW-len(message))//2, y=statAreaY+1, fgcolor='white') 
    #Вывод списка полей
    if drawBrowser and browser:
      win.fill(' ', region=(browserAreaX, browserAreaY, browserAreaW, browserAreaH))
      for i in range( min( len(browser.files), browserAreaH ) ):
        string = '>' if browser.selected==i else ' '
        string += browser.files[i].replace('.field','') 
        win.putchars(string, x=browserAreaX+1, y=browserAreaY+i, fgcolor='white')         
    #Рисование границ поля
    if drawBorder:
      win.fill('X', region=(0,0,fieldAreaW, fieldAreaH))
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
  print('CLIENT '+cname+' connecting to ip {0}, port {1} ...'.format(options['ip'],options['port'])) 
  sockRecv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  try:
    sockRecv.connect((options['ip'],options['port']))
  except ConnectionRefusedError:
    print('Connection refused by server')
    return
  except TimeoutError:
    print(' ! Connection timeout. Check address and port and retry.')
    return 
    
  msg=pickle.dumps(('RECV',cname))  #+PACKET_END  на авось :)
  sockRecv.send(msg) 

  sockSend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  try:
    sockSend.connect((options['ip'],options['port']))
  except ConnectionRefusedError:
    print(' ! Connection refused by server')
    sockRecv.close()
    return
  except TimeoutError:
    print(' ! Connection timeout. Check address and port and retry.')
    sockRecv.close()
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
   nonlocal browser

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
         draw(drawFns=True, drawPlayers=True)
       elif data[0]=='PLAYERS':
         #print('CLIENT '+cname+' received PLAYERS data')
         players=data[1]
         draw(drawPlayers=True)
       elif data[0]=='MESSAGE':
         #print('CLIENT '+cname+' received MESSAGE '+data[1])
         message=data[1]
         draw(drawMessage=True)
       elif data[0]=='GG':
         #print('CLIENT '+cname+' received GG')
         gameOver=True
       elif data[0]=='BROWSER':
         #print('CLIENT '+cname+' received MESSAGE '+data[1])
         browser=data[1]
         draw(drawBorder=True, drawFns=True, drawBrowser=True)
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
      if gameOver:
        break
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
  #print("CLIENT " + cname + " closing")
  sockSend.close()
  #Игнорирование оставшихся событий 
  for event in pygame.event.get():
    pass
  #Ожидание нажатия клавиши по окончанию игры
  pygcurse.waitforkeypress()
  print("CLIENT " + cname + " closed")
