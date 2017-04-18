"""
Программа "Змейка" - запускаемый файл
"""
from snakecommon import *
from snakeclient import *

import pygcurse.pygcurse as pygcurse
import pygame
from pygame.locals import *
import getpass
import ipaddress
import multiprocessing
import threading
import time
import socket
import sys

options = {
  'IP':'10.44.15.13',
  'port':1003,
  'player name':getpass.getuser()[:8]
}

gameOver=False

def setSpeed(newSpeed):
  """
  Установка скорости. Допускаются значения от 1 до 9
  Возвращает истину, если изменение успешно и нужно перезапустить таймер
  """
  ispeed=int(newSpeed)
  if ispeed<1 or ispeed>9: return False
  global speed
  global interval
  speed = ispeed
  interval = 2000 // (1 + ispeed)
  return True

def serverProcessFunction(fns, options):
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.bind(('',options['port']))
  sock.listen(10)  #TODO: должно зависеть от допустимого числа игроков?
  print('SERVER listening at port ' +str(options['port']))
  while True:
    (client,addr) = sock.accept()
    print('SERVER accepted connection from '+str(addr))
    msg = client.recv(1024) #TODO: нормально определить размер
    print('SERVER received message: '+ msg.decode('ascii'))
    client.close()

def drawThreadFunction(fns):
  """
  Потоковая функция прорисовки поля
  """
  borderWidth = 1
  statAreaH = 6
  statAreaW = 12
  statAreaX = 1
  statAreaY = fns.H+borderWidth*2
  windowW = max(fns.W+borderWidth*2, statAreaW)
  windowH = fns.H+borderWidth*2 + statAreaH
  
  win = pygcurse.PygcurseWindow(windowW, windowH, 'Snakes' ) 
                                    #font=pygcurse.pygame.font.Font(None, 32)

  def draw(drawBorder=False):
    """
    Рисование всего
    """
    win.fgcolor = 'gray'
    #Рисование границ поля
    if drawBorder:
      win.fill('X', region=(0,0,fns.W+borderWidth*2, fns.H+borderWidth*2))
    #Рисование поля
    for y in range(fns.H):
      win.cursor=(borderWidth, y+borderWidth)
      win.write(fns.field[y])
    #Рисование вишенок
    for cherry in fns.cherries:
      (x,y)=cherry
      win.putchars(cherrySymbol, x=x+borderWidth, y=y+borderWidth, fgcolor='maroon')
    #Если змея мертвая,оставить след
    #лучший способ чем два цикла?
    for snake in fns.snakes: 
      if not snake.dead: continue
      for segment in snake.coords:
        (x,y)=segment
        win.putchars(fns.field[y][x], x=x+borderWidth, y=y+borderWidth, fgcolor=snake.color)
    #Рисование живых змей
    for snake in fns.snakes: 
      if snake.dead: continue
      #Голова змеи
      segment = snake.coords[0]
      (x,y)=segment
      win.putchars(snakeHeadSymbol, x=x+borderWidth, y=y+borderWidth, fgcolor=snake.color)
      #Тело змеи
      for segment in snake.coords[1:]:
        (x,y)=segment
        win.putchars(snakeSymbol, x=x+borderWidth, y=y+borderWidth, fgcolor=snake.color)
    #Вывод скорости
    win.putchars('SPEED {0}'.format(speed), x=statAreaX, y=statAreaY, fgcolor='white')
    #Вывод сообщения GAME OVER
    if gameOver:
      mess=' GAME OVER '
      win.putchars(mess, x=(windowW-len(mess))//2, y=statAreaY+statAreaH//2, fgcolor='yellow') 

  setSpeed(3)
  draw(True)
  pygame.time.set_timer(USEREVENT,interval)
  speedChanged=False
  #Основной цикл
  while not gameOver:
    for event in pygame.event.get():
      if event.type == QUIT:
        pygame.quit()
        sys.exit()
      elif event.type == KEYDOWN: 
        if event.key == K_F4 and (event.mod & KMOD_LALT or event.mod & KMOD_RALT):
          pygame.quit()
          #sys.exit()
          return
        elif event.key == K_a:
          if fns.snakes[0].direction!=(1,0):
            fns.snakes[0].direction=(-1,0)
        elif event.key == K_d:
          if fns.snakes[0].direction!=(-1,0):
            fns.snakes[0].direction=(1,0)
        elif event.key == K_w:
          if fns.snakes[0].direction!=(0,1):
            fns.snakes[0].direction=(0,-1)
        elif event.key == K_s:
          if fns.snakes[0].direction!=(0,-1):
            fns.snakes[0].direction=(0,1)
        elif event.key == K_LEFT:
          if fns.snakes[1].direction!=(1,0):
            fns.snakes[1].direction=(-1,0)
        elif event.key == K_RIGHT:
          if fns.snakes[1].direction!=(-1,0):
            fns.snakes[1].direction=(1,0)
        elif event.key == K_UP:
          if fns.snakes[1].direction!=(0,1):
            fns.snakes[1].direction=(0,-1)
        elif event.key == K_DOWN:
          if fns.snakes[1].direction!=(0,-1):
            fns.snakes[1].direction=(0,1)
        elif event.key == K_KP_PLUS:
          if setSpeed(speed+1):
            speedChanged = True
        elif event.key == K_KP_MINUS:
          if setSpeed(speed-1):
            speedChanged = True
      elif event.type == USEREVENT:  
        #Событие от таймера. Перерисовка  
        fns.step()
        if speedChanged:
          pygame.time.set_timer(USEREVENT,interval)
        draw()

  #КОНЕЦ ИГРЫ
  #Остановка таймера
  pygame.time.set_timer(USEREVENT,0)
  time.sleep(2)
  #Игнорирование оставшихся событий 
  for event in pygame.event.get():
    pass
  #Ожидание нажатия клавиши по окончанию игры
  pygcurse.waitforkeypress()
  

if __name__=='__main__':
  #Чтение файла с настройками, если таковой существует
  try:
    f=open('snake.ini')
    for line in f:
      ss = line.split('=')
      (ss[0],ss[1])=(ss[0].strip(),ss[1].strip())
      if len(ss)<2: continue
      if ss[0] == 'ip':
        options['ip'] = ss[1]
      elif ss[0] == 'player name':
        options['player name'] = ss[1]
      elif ss[0] == 'port':
        try:
          options['port'] = int(ss[1])
        except ValueError:
          pass
    f.close()
  except FileNotFoundError:
    pass

  isServer=None
  #Уточнение настроек вручную
  print("Welcome to Snake alpha!    Developed by da.volkov")
  #Имя
  print("Enter player name, 8 symbols max [" + options['player name'] + "]:", end=' ')
  res=input().strip()[:8]
  if len(res)>0:
    options['player name']=res
  #Сервер
  res=' '
  while res not in ('s', 'c'):
    print('Are you (s)erver or (c)lient?', end=' ')
    res=input().strip().lower()
  if res=='s':
    isServer=True
  else:
    isServer=False
  #IP адрес
  address=None
  if not isServer:
    while address==None:
      print('Enter server IP [' + options['IP'] + ']', end=' ')
      res=input().strip().lower()
      if len(res)==0: 
        address=ipaddress.ip_address(options['IP'])
        break
      try:
        address=ipaddress.ip_address(res)
        options['IP']=res
      except ValueError:
        pass
  port=None
  #Порт
  while port==None:
    print('Enter port ['+str(options['port'])+']', end=' ')
    res=input().strip()
    if len(res)==0:
      port=options['port']
      break
    try:
      port=options['port']=int(res)
    except ValueError:
      pass
  #Запись последних введённых значений в файл
  f=open('snake.ini','w')
  f.write('IP = '+options['IP']+'\n')
  f.write('port = '+str(options['port'])+'\n')
  f.write('player name = '+options['player name']+'\n')
  f.close()

  #Чтение из файла поля с позициями змеек
  fns=FieldAndSnakes(open('./fields/foursquares-12x12.field'))
  #Присвоение цветов змейкам
  for s in range(len(fns.snakes)):
    fns.snakes[s].color=snakeColors[s]

  #Запуск сервера
  if isServer:
    srvProc = multiprocessing.Process(target=serverProcessFunction, args=(fns,options))
    srvProc.start()

  #Клиентская часть
  try:
    clientProcessFunction(fns,options)
  except Exception as exc:  
    srvProc.terminate()
    srvProc.join()
    raise exc
    exit()

  #Завершение работы
  print("Press any key to close")
  input()
  srvProc.terminate()
  srvProc.join()
  exit()

  #Запуск потока вывода/ввода
  drawThread=threading.Thread(target=drawThreadFunction, args=(fns,))
  drawThread.start()

  #Останов потока вывода/ввода
  drawThread.join()
  print('Thanks for playing!')
