import pygcurse.pygcurse as pygcurse
import pygame
from pygame.locals import *
import random
import threading
import time
import sys

maxCherries = 3
cherryDuration = 50
cherryDurationWarning = 10

speed = 3
interval = 500

emptySpaceSymbol='.'
cherrySymbol='q'
snakeSymbol='0'
snakeHeadSymbol='@'

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
          fns.snakes[0].direction=(-1,0)
        elif event.key == K_d:
          fns.snakes[0].direction=(1,0)
        elif event.key == K_w:
          fns.snakes[0].direction=(0,-1)
        elif event.key == K_s:
          fns.snakes[0].direction=(0,1)
        elif event.key == K_LEFT:
          fns.snakes[1].direction=(-1,0)
        elif event.key == K_RIGHT:
          fns.snakes[1].direction=(1,0)
        elif event.key == K_UP:
          fns.snakes[1].direction=(0,-1)
        elif event.key == K_DOWN:
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
  
class Snake:
 """
 Класс Змейка
 """
 def __init__(self):
   self.dead=False

 def determineDirection(self):
   #Вычисление направления движения (поле объекта)
   self.direction=(self.coords[0][0]-self.coords[1][0],self.coords[0][1]-self.coords[1][1])


class FieldAndSnakes:
 """
 Класс Поле, содержащий информацию о поле, змейках и вишенках
 """
 fieldWidthMin=10
 fieldHeightMin=10
 snakeLengthMin=3

 #def fieldFromFile(file):
 def __init__(self, file):
  """
  Чтение игрового поля из файла
  """
  self.field=list(list(line.strip()) for line in file if len(line.strip())>0)
  file.close()
  #Проверка высоты
  H=len(self.field)
  assert H>=self.fieldHeightMin, 'Field height too small ({0}<{1})'.format(H,self.fieldHeightMin)
  #Проверка ширины
  wd=list(map(len,self.field))
  minW=min(wd) 
  maxW=max(wd)
  assert minW==maxW, 'Inconsistent field width ({0} to {1})'.format(minW,maxW)
  W=minW
  assert W>=self.fieldWidthMin, 'Field width too small ({0}<{1})'.format(W,self.fieldWidthMin)

  #Считывание начальных положений змеек
  self.snakes=[]
  for headSymbol in ('1', '2'):
    #Поиск головы
    for y in range(H):
      try:
        x=self.field[y].index(headSymbol)
      except ValueError:
        continue
      #Нашли голову
      snake=[(x,y)]
      self.field[y][x]=emptySpaceSymbol
      while True:
        neighbors=[]
        if x-1>=0 and self.field[y][x-1]==snakeSymbol: neighbors.append((x-1,y))
        if x+1< W and self.field[y][x+1]==snakeSymbol: neighbors.append((x+1,y))
        if y-1>=0 and self.field[y-1][x]==snakeSymbol: neighbors.append((x,y-1))
        if y+1< H and self.field[y+1][x]==snakeSymbol: neighbors.append((x,y+1))
        if len(neighbors)==0: 
          #Конец змейки
          break
        elif len(neighbors)==1:
          #Продолжение змейки  
          snake.append(neighbors[0])  #или extend(neighbors)
          (x,y)=neighbors[0]
          self.field[y][x]=emptySpaceSymbol
        else:
          #Несколько вариантов продолжения - недопустимо
          assert False, 'Incorrect initial snake position at x={0}, y={1}'.format(x,y)
          break 
      assert len(snake)>=self.snakeLengthMin, "Snake '"+headSymbol+"' too short ({0}<{1})".format(len(snake),self.snakeLengthMin)
      sn=Snake()
      sn.coords=snake
      sn.determineDirection()
      self.snakes.append(sn)
      print("Snake '"+headSymbol+"' found at ({0}, {1})".format(*snake[0]))
      break
    else:
      print("Snake '"+headSymbol+"' not found")

  assert len(self.snakes)>=2, 'Two snakes not found (just {0})'.format(len(self.snakes))
   

  print('Field loaded successfully! H={0} W={1}'.format(H, W))  
  print('{0} snakes'.format(len(self.snakes)))  
  self.H=H
  self.W=W
  for line in self.field: print(*line)

  self.cherries=[]
  for i in range(maxCherries):
    self.placeCherry()


 def placeCherry(self):
   """
   Добавление на поле одной вишенки
   """
   validPlace=False
   while not validPlace:
     validPlace=True
     x=random.randint(0,self.W-1)
     y=random.randint(0,self.H-1)
     #Проверка на совпадение с другой вишенкой
     if (x,y) in self.cherries:
       validPlace=False
       continue
     #Проверка на препятствие на поле
     if self.field[y][x] != emptySpaceSymbol:
       validPlace=False
       continue
     #Проверка на змейку
     for snake in self.snakes:
       if snake.dead: continue
       if (x,y) in snake.coords:
         validPlace=False
         break
   self.cherries.append((x,y))

 def step(self):
  """
  Продвижение на 1 шаг
  """
  cherriesEaten=0

  for snake in self.snakes:
    if snake.dead: continue
    (newx,newy)=(snake.coords[0][0]+snake.direction[0], snake.coords[0][1]+snake.direction[1])

    if (newx,newy) in snake.coords:
      #Врезались сами в себя
      snake.dead=True
      continue
    if newx<0 or newx>=self.W or newy<0 or newy>=self.H:
      #Врезались в стенку
      snake.dead=True
      continue

    snake.coords.insert(0,(newx,newy))
    if (newx,newy) in fns.cherries:
      #вишенка съедена
      cherriesEaten+=1
      self.cherries.remove((newx,newy))
    elif self.field[newy][newx]==emptySpaceSymbol:
      #не съедена
      snake.coords.pop()
    else:
      #столкновение с препятствием
      snake.coords.pop()
      snake.dead=True

    #Проверка на столкновение с другими
    for snake2 in self.snakes:
      if not snake2.dead and snake!=snake2 and (newx,newy) in snake2.coords:
        snake.dead=True
        #Проверка на взаимность столкновения: тогда умерли обе!
        if snake2.coords[0] in snake.coords:
          snake2.dead=True

  #Подсчёт оставшихся в живых
  alive=0
  for snake in self.snakes:
    if not snake.dead:
      alive += 1
  if alive <=1:
    global gameOver
    gameOver = True
 

  # Создание вишенок взамен съеденных
  for i in range(cherriesEaten):
    self.placeCherry()
    

if __name__=='__main__':
  #Чтение из файла поля с позициями змеек
  fns=FieldAndSnakes(open('./fields/foursquares-12x12.field'))
  #Присвоение цветов змейкам
  snakeColors=['red','aqua','yellow','lime']
  for s in range(len(fns.snakes)):
    fns.snakes[s].color=snakeColors[s]
  #Запуск потока вывода/ввода
  drawThread=threading.Thread(target=drawThreadFunction, args=(fns,))
  drawThread.start()

  #Останов потока вывода/ввода
  drawThread.join()
  print('Thanks for playing!')
