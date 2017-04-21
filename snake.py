"""
Программа "Змейка" - запускаемый файл
"""
from snakecommon import *
from snakeclient import *

import asyncore
import copy
import getpass
import ipaddress
import multiprocessing
import os
import pickle
import threading
import time
import socket
import sys

options = {
  'IP':'10.44.15.13',
  'port':1003,
  'player name':getpass.getuser()[:8]
}

gameStart=False
gameOver=False
speed = 3
interval = 500
maxPlayers = 9
fns=None

def setSpeed(newSpeed):
  """
  Установка скорости. Допускаются значения от 1 до 9
  Возвращает истину, если изменение успешно и нужно сообщить клиентам
  """
  global speed
  global interval
  ispeed=int(newSpeed)
  if ispeed<1 or ispeed>9: return False
  speed = ispeed
  interval = 2000 // (1 + ispeed)
  return True
#####################
# end of setSpeed() #
#####################

class PlayerData:
 def __init__(self):
  self.number = None
  self.socketSend = None
  self.socketRecv = None
  self.thread = None
  self.ready = False
  self.isAdmin = False
pd={}

def sendPlayerData(player=None):
  """
  Рассылка статуса игроков игрокам
  """
  #print('sendPlayerData(), number of players:'+ str(len(pd)))
  #Создаём копию словаря и удаляем несериализуемые объекты:  сокеты, потоки
  data={}
  for p in pd:
    data[p] = PlayerData()
    data[p].ready = pd[p].ready
    data[p].isAdmin = pd[p].isAdmin
  #Собственно рассылаем
  msg=pickle.dumps(('PLAYERS',data))+PACKET_END

  if player:  #если задан получатель, то только ему
    if pd[player].socketSend != None:
      pd[player].socketSend.send(msg)
    return

  for p in pd:  #иначе всем
    if pd[p].socketSend != None:
      pd[p].socketSend.send(msg)

def sendMessage(text, player=None):
  """
  Рассылка клиентам сообщения
  """
  msg=pickle.dumps(('MESSAGE',text))+PACKET_END

  if player:  #если задан получатель, то только ему
    if pd[player].socketSend != None:
      pd[player].socketSend.send(msg)
    return

  for p in pd:  #иначе всем
    if pd[p].socketSend != None:
      pd[p].socketSend.send(msg)


def sendFnsData(fns, player=None):
  """
  Рассылка клиентам данных о поле
  """
  msg=pickle.dumps(('FNS', fns))+PACKET_END

  if player:  #если задан получатель, то только ему
    if pd[player].socketSend != None:
      pd[player].socketSend.send(msg)
    return

  for p in pd:  #иначе всем
    if pd[p].socketSend != None:
      pd[p].socketSend.send(msg)


def serverThreadFunction( pname ):
  """
  Обработка файлов от клиентов
  isAdmin: клиент - администратор и имеет дополнительные права
  """
  sock = pd[pname].socketRecv
  sock.settimeout(1)
  buffer=b''
  while not gameOver:
    try:
     #print('SERVER reading data from {0}'.format(pname))
     block=sock.recv(1024)
     #print('SERVER received {0} bytes from {1}'.format(len(block),pname))
     if not block:
       del pd[pname]
       print('SERVER: player {0} disconnected * (socket {1})'.format(pname, sock))
       print('SERVER: {0} players remaining'.format(len(pd)) )
       return
     buffer += block
     index=buffer.find(PACKET_END)

     
     while index>=0:
      msg=buffer[0:index]
      buffer=buffer[index+len(PACKET_END):]
      index=buffer.find(PACKET_END)

      data=pickle.loads(msg) 
      if data[0]=='DISCONNECT':
        del pd[pname]
        print('SERVER: player {0} disconnected ** (socket {1})'.format(pname, sock))
        print('SERVER: {0} players remaining'.format(len(pd)) )
        return
      elif data[0]=='READY':
        pd[pname].ready=True
        sendPlayerData()
        continue
      elif data[0]=='direction':
        if not gameStart: continue
        if pd[pname].number < len(fns.snakes):
          if data[1]=='L':
            if fns.snakes[pd[pname].number].direction != (1,0):
              fns.snakes[pd[pname].number].direction=(-1,0)
          elif data[1]=='R':
            if fns.snakes[pd[pname].number].direction != (-1,0):
              fns.snakes[pd[pname].number].direction=(1,0)
          elif data[1]=='U':
            if fns.snakes[pd[pname].number].direction != (0,1):
              fns.snakes[pd[pname].number].direction=(0,-1)
          elif data[1]=='D':
            if fns.snakes[pd[pname].number].direction != (0,-1):
              fns.snakes[pd[pname].number].direction=(0,1)
      elif data[0]=='speed' and pd[pname].isAdmin:
        if not gameStart: continue
        if setSpeed(speed+data[1]):
          sendMessage('SPEED '+str(speed))
     # end while index>0
    except ConnectionResetError:
      del pd[pname]
      print('SERVER: player {0} disconnected *** (socket {1})'.format(pname, sock))
      print('SERVER: {0} players remaining'.format(len(pd)) )
      return
    except socket.timeout as exc:
      err = exc.args[0]
      if err == 'timed out':
        continue
      else:
        raise exc
    #print('SERVER ****')
  return

def serverProcessFunction(options):
  """
  Процесс сервера: ожидание подключений
  """
  #Чтение из файла поля с позициями змеек
  global fns
  fns=FieldAndSnakes(open('./fields/foursquares-12x12.field'))

  admin = options['player name']


  def serverAcceptThread():
   """
   accept() отказывается работать асинхронно,
   поэтому в отдельный поток его
   """
   sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
   sock.bind(('',options['port']))
   sock.listen(5)
   print('SERVER: listening at port ' +str(options['port']))

   global gameStart
   global pd
   message="нажмите ПРОБЕЛ для подтверждения готовности"
   while True:
    #time.sleep(0.1)
    #try:
    (client,addr) = sock.accept()
    #print('SERVER: accepted connection from '+str(addr))
    msg = client.recv(1024)
    #print('SERVER: received '+str(len(msg))+' bytes from '+str(addr))
    (mode,pname)=pickle.loads(msg)
    
    if mode=='RECV':
      #Это первое ожидаемое соединение от игрока.
      if pname in pd:
        #Если есть соединение с таким именем игрока - закрываем
        if pd[pname].socketRecv: pd[pname].socketRecv.close()
        if pd[pname].socketSend: pd[pname].socketSend.close()
        #и очищаем информацию по игроку в словаре
        del pd[pname]
        if pd[pname].thread:
          #TODO: прибить поток-обработчик
          #или прибьётся сам с закрытием сокета? 
          pass
      if len(pd)>=maxPlayers:
        #Слишком много игроков
        client.close()
        continue
      pd[pname]=PlayerData()
      pd[pname].number=0
      pd[pname].isAdmin = (pname == admin)
      pd[pname].socketSend=client
    elif mode=='SEND':
      #Это второе ожидаемое соединение от игрока.
      #Если нет записи в словаре (нет первого соединения) - отключаем
      if pname not in pd:
        client.close()
        continue
      pd[pname].socketRecv=client
      pd[pname].ready=False
      thr=threading.Thread(target=serverThreadFunction, args=(pname,))
      thr.start()
      pd[pname].thread=thr
      
      time.sleep(0.5)
      sendFnsData(fns, pname)
      sendMessage(message,pname)
      sendPlayerData()
      print('SERVER: player '+pname+' joined')
      #thr.daemon = True
    #except socket.timeout as exc:
    #  err = exc.args[0]
    #  if err == 'timed out':
    #    continue
    #  else:
    #    raise exc

    if len(pd)==0:
      print('SERVER: closing, all players disconnected')
      return
   # end while not gameStart
   #########################
  ###########################
  # end while not gameStart #
  ###########################
  
  thrAcc=threading.Thread(target=serverAcceptThread)
  thrAcc.daemon = True
  thrAcc.start()

  global gameStart
  print('SERVER: waiting for start '+admin)
  while not gameStart:
    time.sleep(1)
    gameStart = pd[admin].ready
    if len(pd)==0:
      print('SERVER: closing, all players disconnected')
      return

  #Окончательное присвоение змеек игрокам
  p = 0
  for player in pd:
    pd[player].number=p
    p += 1
  del fns.snakes[p:]
    
  print('SERVER: game started with {0} players'.format(len(pd)))

  global speed
  global interval
  setSpeed(3)
  sendMessage('SPEED '+str(speed))
  #Основной цикл
  global gameOver
  while not gameOver:
    time.sleep(interval*0.001)
    gameOver = fns.step()
    sendFnsData(fns)
    if len(pd)==0:
      print('SERVER: closing, all players disconnected')
      exit()
      return

  #КОНЕЦ ИГРЫ
  sendMessage('GAME OVER')
  print('SERVER: game ended')
  msg=pickle.dumps(('GG',None))
  for player in pd:
    if pd[player].socketSend != None:
      pd[player].socketSend.send(msg)
  print('SERVER: about to close')
  return
#################################
# end ofserverProcessFunction() #
#################################  

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


  #Запуск сервера
  if isServer:
    srvProc = multiprocessing.Process(target=serverProcessFunction, args=(options,))
    srvProc.start()
    print ('SERVER PID='+str(srvProc.pid) )

  #Клиентская часть
  clientProcessFunction(options)
  print("Client closed")
  """
  #try:
  #  clientProcessFunction(options)
  #except Exception as exc:  
  #  if isServer:
  #    print("Exception on client, termniating server")
  #    srvProc.terminate()
  #    srvProc.join()
  #  raise exc
  #  exit()
  """

  if isServer:
    print("Client closed, termniating server")
    srvProc.terminate()
    srvProc.join()
  exit()
