

fieldWidthMin=10
fieldHeightMin=10
"""
fieldHeight=30
fieldWidth=30
startingLength=3
"""


def fieldFromFile(file):
  text=list(line.strip() for line in file if len(line.strip())>0)
  H=len(text)
  assert H>=fieldHeightMin, 'Field height too small ({0}<{1})'.format(H,fieldHeightMin)
  wd=list(map(len,text))
  minW=min(wd) 
  maxW=max(wd)
  assert minW==maxW, 'Inconsistent field width ({0} to {1})'.format(minW,maxW)
  print('Field loaded successfully! H={0} W={1}'.format(H, minW))  
  print(text)


if __name__=='__main__':
  fieldFromFile(open('./fields/test.field'))
