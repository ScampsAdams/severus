"""
Программа "Змейка" - константы, определения...
"""
import random

maxCherries = 3
cherryDuration = 50 #не используется
cherryDurationWarning = 10 #не используется

speed = 3
interval = 500

fieldWidthMin=10
fieldHeightMin=10
snakeLengthMin=3
emptySpaceSymbol='.'
cherrySymbol='q'
snakeSymbol='0'
snakeHeadSymbol='@'
snakeColors=['red','aqua','yellow','lime']
maxSnakes=1

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

 #def fieldFromFile(file):
 def __init__(self, file, debugOutput=False):
  """
  Чтение игрового поля из файла
  """
  self.field=list(list(line.strip()) for line in file if len(line.strip())>0)
  file.close()
  #Проверка высоты
  H=len(self.field)
  assert H>=fieldHeightMin, 'Field height too small ({0}<{1})'.format(H,fieldHeightMin)
  #Проверка ширины
  wd=list(map(len,self.field))
  minW=min(wd) 
  maxW=max(wd)
  assert minW==maxW, 'Inconsistent field width ({0} to {1})'.format(minW,maxW)
  W=minW
  assert W>=fieldWidthMin, 'Field width too small ({0}<{1})'.format(W,fieldWidthMin)

  #Считывание начальных положений змеек
  self.snakes=[]
  for headSymbol in ('1','2','3','4','5','6','7','8','9'):
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
      assert len(snake)>=snakeLengthMin, "Snake '"+headSymbol+"' too short ({0}<{1})".format(len(snake),snakeLengthMin)
      sn=Snake()
      sn.coords=snake
      sn.determineDirection()
      self.snakes.append(sn)
      if debugOutput: print("Snake '"+headSymbol+"' found at ({0}, {1})".format(*snake[0]))
      break
    else:
      if debugOutput: print("Snake '"+headSymbol+"' not found")
  #Удаляем лишних змеек, если есть ограничение через константу
  del self.snakes[maxSnakes:]
  assert len(self.snakes)>=1, 'Found less than 1 snake (only {0})'.format(len(self.snakes))
  #Присвоение цветов змейкам
  for s in range(len(self.snakes)):
    self.snakes[s].color=snakeColors[s]
   

  if debugOutput: 
    print('Field loaded successfully! H={0} W={1}'.format(H, W))  
    print('{0} snakes'.format(len(self.snakes)))  
    for line in self.field: 
      print(*line)
  self.H=H
  self.W=W

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
  if alive <1:   
    global gameOver
    gameOver = True
 

  # Создание вишенок взамен съеденных
  for i in range(cherriesEaten):
    self.placeCherry()
    
