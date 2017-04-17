

fieldWidthMin=10
fieldHeightMin=10
snakeLengthMin=3

snakeSymbol='0'


def fieldFromFile(file):
  """
  Чтение игрового поля из файла
  """
  field=list(list(line.strip()) for line in file if len(line.strip())>0)
  file.close()
  #Проверка высоты
  H=len(field)
  assert H>=fieldHeightMin, 'Field height too small ({0}<{1})'.format(H,fieldHeightMin)
  #Проверка ширины
  wd=list(map(len,field))
  minW=min(wd) 
  maxW=max(wd)
  assert minW==maxW, 'Inconsistent field width ({0} to {1})'.format(minW,maxW)
  W=minW
  assert W>=fieldWidthMin, 'Field width too small ({0}<{1})'.format(W,fieldWidthMin)

  #Считывание начальных положений змеек
  snakes=[]
  for headSymbol in ('1', '2'):
    #Поиск головы
    for y in range(H):
      try:
        x=field[y].index(headSymbol)
      except ValueError:
        continue
      #Нашли голову
      snake=[(x,y)]
      field[y][x]='.'
      while True:
        neighbors=[]
        if x-1>=0 and field[y][x-1]==snakeSymbol: neighbors.append((x-1,y))
        if x+1< W and field[y][x+1]==snakeSymbol: neighbors.append((x+1,y))
        if y-1>=0 and field[y-1][x]==snakeSymbol: neighbors.append((x,y-1))
        if y+1< H and field[y+1][x]==snakeSymbol: neighbors.append((x,y+1))
        if len(neighbors)==0: 
          #Конец змейки
          break
        elif len(neighbors)==1:
          #Продолжение змейки  
          snake.append(neighbors[0])  #или extend(neighbors)
          (x,y)=neighbors[0]
          field[y][x]='.'
        else:
          #Несколько вариантов продолжения - недопустимо
          assert False, 'Incorrect initial snake position at x={0}, y={1}'.format(x,y)
          break 
      assert len(snake)>=snakeLengthMin, "Snake '"+headSymbol+"' too short ({0}<{1})".format(len(snake),snakeLengthMin)
      snakes.append(snake)
      print("Snake '"+headSymbol+"' found at ({0}, {1})".format(*snake[0]))
      break
    else:
      print("Snake '"+headSymbol+"' not found")

  assert len(snakes)>=2, 'Two snakes not found (just {0})'.format(len(snakes))
   

  print('Field loaded successfully! H={0} W={1}'.format(H, W))  
  print('{0} snakes'.format(len(snakes)))  
  for line in field: print(*line)


if __name__=='__main__':
  fieldFromFile(open('./fields/foursquares-12x12.field'))
