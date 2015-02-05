# -*- coding: iso-8859-15 -*-
#*******************************************************************************
#Fábio Reis - 2013, Dec
#fabio.reis -at- ist.utl.pt
#HDA - Auditbox
#*******************************************************************************
# Display Link USB Protocol Hexadecimal parser

def afe0(stream, index):
  idx = index
  result = ['afe0']
  
  magicBits = ''.join(stream[idx:idx+8])
  idx += 8
  result.append(magicBits)
  
  lines = 0
  while lines < 512:
    try:
      line = ''.join(stream[idx:idx+9])
      result.append(line)
      lines += 1
      idx += 9
    except:
      print "Error, not enough length to process AFE0 command"
      return -1    
  
  del commands['afe0']
  return result, idx

def afa0(stream, index):
  return ['afa0'], index

def af20(stream, index):
  idx = index
  try:
    result = ['af20', stream[idx], stream[idx+1]]
    idx += 2
  except:
    print "Error, not enough length to process AF20 command"
    return -1
  
  return result, idx

def af60(stream, index):
  idx = index
  result = ['af60']
  try:
    result.append(''.join(stream[idx:(idx+3)]))
    idx += 3
    
    length = ''.join(stream[idx:(idx+1)])
    result.append(length)
    idx += 1
    
    length = int(length, 16)
    result.append(''.join(stream[idx:(idx+length*1)]))
    idx += length*1    
  except:
    print "Error, not enough length to process AF60 command"
    return -1
  
  return result, idx

def af68(stream, index):
  idx = index
  result = ['af68']
  try:
    result.append(''.join(stream[idx:(idx+3)]))
    idx += 3
    
    length = ''.join(stream[idx:(idx+1)])
    result.append(length)
    idx += 1
    
    length = int(length, 16)
    result.append(''.join(stream[idx:(idx+length*2)]))
    idx += length*2    
  except:
    print "Error, not enough length to process AF68 command"
    return -1
  
  return result, idx

def af61(stream, index):
  idx = index
  result = ['af61']
  
  try:
    result.append(''.join(stream[idx:(idx+3)]))
    idx += 3
    
    length = ''.join(stream[idx:(idx+1)])
    result.append(length)
    idx += 1
    
    length = int(length, 16)
    if length == 0:
      length = 256
      
    count = 0
    while count < length:
      lengthAux = ''.join(stream[idx:(idx+1)])
      result.append(lengthAux)
      idx += 1
      
      data = ''.join(stream[idx:(idx+1)])
      result.append(data)
      idx += 1
      
      lengthAux = int(lengthAux, 16)
      if lengthAux == 0:
	lengthAux = 256
      count += lengthAux
  except:
    print "Error, not enough length to process AF61 command"
    return -1
    
  return result, idx

def af69(stream, index):
  idx = index
  result = ['af69']
  
  try:
    result.append(''.join(stream[idx:(idx+3)]))
    idx += 3
    
    length = ''.join(stream[idx:(idx+1)])
    result.append(length)
    idx += 1
    
    length = int(length, 16)
    if length == 0:
      length = 256
      
    count = 0
    while count < length:
      lengthAux = ''.join(stream[idx:(idx+1)])
      result.append(lengthAux)
      idx += 1
      
      data = ''.join(stream[idx:(idx+2)])
      result.append(data)
      idx += 2
      
      lengthAux = int(lengthAux, 16)
      if lengthAux == 0:
	lengthAux = 256
      count += lengthAux
  except:
    print "Error, not enough length to process AF69 command"
    return -1
    
  return result, idx

def af62(stream, index):
  idx = index
  result = ['af62']
  
  try:
    result.append(''.join(stream[idx:idx+3]))
    idx += 3
    
    result.append(''.join(stream[idx:idx+1]))
    idx += 1
    
    result.append(''.join(stream[idx:idx+3]))
    idx += 3
  except:
    print "Error, not enough length to process AF62 command"
    return -1
  
  return result, idx

def af6a(stream, index):
  idx = index
  result = ['af6a']
  
  try:
    result.append(''.join(stream[idx:idx+3]))
    idx += 3
    
    result.append(''.join(stream[idx:idx+1]))
    idx += 1
    
    result.append(''.join(stream[idx:idx+3]))
    idx += 3
  except:
    print "Error, not enough length to process AF6A command"
    return -1
  
  return result, idx

def af70(stream, index):
  idx = index
  result = ['af70']
  
  try:
    result.append(''.join(stream[idx:idx+3]))
    idx += 3
    
    length = ''.join(stream[idx:idx+1])
    result.append(length)
    idx += 1
    
    cmd = stream[idx:idx+2]
    idx += 2
    
    idInit = idx - 2
    done = False
    while not done:
      if commands.get(''.join(cmd), -1) == -1:
	cmd[0] = cmd[1]
	cmd[1] = stream[idx]
	idx += 1
      else:
	done = True
	idx -= 2
      
    result.append(''.join(stream[idInit:idx]))
  except:
    print "Error, not enough length to process AF70 command"
    return -1
  
  return result, idx

def af78(stream, index):
  idx = index
  result = ['af78']
  
  try:
    result.append(''.join(stream[idx:idx+3]))
    idx += 3
    
    length = ''.join(stream[idx:idx+1])
    result.append(length)
    idx += 1
    
    cmd = stream[idx:idx+2]
    idx += 2
    
    idInit = idx - 2
    done = False
    while not done:
      if commands.get(''.join(cmd), -1) == -1:
	cmd[0] = cmd[1]
	cmd[1] = stream[idx]
	idx += 1
      else:
	done = True
	idx -= 2
      
    result.append(stream[idInit:idx])
  except:
    print "Error, not enough length to process AF78 command"
    return -1
  
  return result, idx

commands = {'afe0': afe0, 'afa0': afa0, 
	    'af20': af20,# 'af40': None,
	    'af60': af60, 'af68': af68,
	    'af61': af61, 'af69': af69,
	    'af62': af62, 'af6a': af6a,
#		'af63': None, 'af6b': None,
#		'af67': None, 'af6e': None,
	    'af70': af70, 'af78': af78
	    }

class DisplayLinkParser:
  def parse(self, stream):
    '''I expect a stream with ['xx', 'aa', ...] hexadecimals
    '''
    
    result = []
    current = []
    
    newCMD = ['', '']
    
    pos = 0
    start = False
    hexaIndex = 0
    startIdx = 0
    endIdx = 0
    while hexaIndex < len(stream):
      hexa = stream[hexaIndex]
      
      newCMD[0] = newCMD[1]
      newCMD[1] = hexa
      hexaIndex += 1
      
      # This is just for the first command
      if not start and newCMD[0] != '':
	start = True
      
      # This will run allways after the first two hexadecimals
      if start:
	cmd = commands.get(''.join(newCMD), -1)
	
	if cmd != -1:
	  try:
	    current, hexaIndex = cmd(stream, hexaIndex)
	    result.append(current)
	  except:
	    return result
      
    return result
