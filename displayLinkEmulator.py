#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#*******************************************************************************
#Fábio Reis - 2013, Dec
#fabio.reis -at- ist.utl.pt
#HDA - Auditbox
#*******************************************************************************
# Display Link device emulator class

import sys, time
import numpy as np
import cv2

RED_MASK = 0xF800
GREEN_MASK = 0x07E0
BLUE_MASK = 0x001F

factor5Bit = 255.0 / 31.0
factor6Bit = 255.0 / 63.0

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def transformPixels(pixStream, inv):
  if inv:
    return ''.join([c[::-1] for c in list(chunks(''.join([bin(int(c, 16))[2:].zfill(4) for c in pixStream]), 8))])
  else:
    return ''.join(list(chunks(''.join([bin(int(c, 16))[2:].zfill(4) for c in pixStream]), 8)))

def transformPixelsR(pixStream):
  return ''.join([b[::-1] for b in [bin(int(c, 16))[2:].zfill(8) for c in pixStream]])

class emulator:
  def readHuffmanTable(self, iFile):
    '''Reads the huffman table from file
    '''
    huffFile = open(iFile, 'r')
    huffStream = huffFile.readlines()
    huffFile.close()
    
    huffStream = [ line.rstrip('\n')[1:] for line in huffStream ]
    huffStream = [ (line[29:-4], int(line[6:12])) for line in huffStream if line[0:2] != '//' and line[-1] == ';']
    
    huffman = dict(huffStream)
    
    return huffman
  
  def calcAllBGR565(self):
    self.BGR565 = np.zeros((0x10000, 3), dtype=np.uint8)
    
    for i in range(0x10000):
      self.BGR565[i] = self.dif2565BGRR(i)
  
  def uncompressData(self, nrPixels, data):
    '''Uncompresses data with the huffman table
    '''
    compData = transformPixelsR(data)#, True)
    pixelCList = []
    
    i = 0
    pixels = 0
    while i < len(compData) and pixels < nrPixels:
      c = compData[i]
      
      if c == '0':
	pixelCList.append(int(c))
	i += 1
      else:
	# It is necessary to find the encoding in the huffman table
	# So we are goind bit by bit until we find a match
	
	txt = ''
	j = i + 1
	found = False
	while j < len(compData) and not found:
	  txt += compData[j]
	  
	  value = self.huffman.get(txt)
	  if value != None:
	    found = True
	    i = j + 1
	    pixelCList.append(value)
	  
	  j += 1
      
      pixels += 1
    return pixelCList
  
  def af68(self, target, length, data):
    '''This data is uncompressed, so I assume it is 565RGB.
	This command write some data to the memory position defined by target, length 
	defines the number of pixels to set. The ammount of data bits should be 16*length,
	or 16*length/4 hexadecimals, e.g.:
	
	  af68 b929fa 03 d69984100000 
	  03 * 16 == len(d69984100000)*4
    '''
    data = bin(int(data,16))[2:]
    ini = 0
    fin = 16
    for pixel in range(length):
      pixData = int(data[ini:fin], 2)
      self.memory[target+2*pixel + 0] = pixData >> 0x08
      self.memory[target+2*pixel + 1] = pixData &  0xFF
      ini += 16
      fin += 16

  def af68R(self, target, length, data):
    '''This data is uncompressed, so I assume it is 565RGB.
	This command write some data to the memory position defined by target, length 
	defines the number of pixels to set. The ammount of data bits should be 16*length,
	or 16*length/4 hexadecimals, e.g.:
	
	  af68 b929fa 03 d69984100000 
	  03 * 16 == len(d69984100000)*4
    '''
    data = bin(int(data,16))[2:]
    ini = 0
    fin = 16
    for pixel in range(length):
      pixData = int(data[ini:fin], 2)
      i, j, frameID  = self.ijOffset(target + 2*pixel)
      
      BGR = self.dif2565BGR(pixData)
      
      if frameID == 1:
	self.frame1[i, j] = BGR
      else:
	self.frame2[i, j] = BGR
      
      ini += 16
      fin += 16
  
  def af6a(self, target, length, source):
    '''This copies data from in-memory source to target memory
    '''
    for pix in range(length):
      self.memory[target + 2*pix + 0] = self.memory[source + 2*pix + 0]
      self.memory[target + 2*pix + 1] = self.memory[source + 2*pix + 1]
  
  def af6aR(self, target, length, source):
    '''This copies data from in-memory source to target memory
    '''
    for pix in range(length):
      i1, j1, frameID1  = self.ijOffset(target + 2*pix)
      i2, j2, frameID2  = self.ijOffset(source + 2*pix)
      
      if frameID1 == 1 and frameID2 == 1:
	self.frame1[i1, j1] = self.frame1[i2, j2]
      elif frameID1 == 2 and frameID2 == 1:
	self.frame2[i1, j1] = self.frame1[i2, j2]
      elif frameID1 == 1 and frameID2 == 2:
	self.frame1[i1, j1] = self.frame2[i2, j2]
      elif frameID1 == 2 and frameID2 == 2:
	self.frame2[i1, j1] = self.frame2[i2, j2]
  
  def af78(self, target, length, data):
    '''This data is compressed.
    '''
    pixels = self.uncompressData(length, data)
    
    count = 0
    last = 0
    for pixData in pixels:
      pixData += last
      self.memory[target+2*count + 0] = pixData >> 0x08
      self.memory[target+2*count + 1] = pixData &  0xFF
      last = pixData
      count += 1
  
  def af78R(self, target, length, data):
    '''This data is compressed.
    '''
    pixels = self.uncompressData(length, data)
    
    count = 0
    last = 0
    for pixData in pixels:
      pixData += last
      i, j, frameID  = self.ijOffset(target + 2*count)
      
      #print target, length, count, i, j, frameID
      #print 'frame size', len(self.frame1), len(self.frame1[0])
      #if count == 3:
	#raise ValueError
      
      BGR = self.dif2565BGR(pixData)
      
      if frameID == 1:
	self.frame1[i, j] = BGR
      else:
	self.frame2[i, j] = BGR
      
      last = pixData
      count += 1
  
  def af20(self, reg, value):
    if reg == '20':
      if value == 'b8':
	self.frameID = 1
      else:
	self.frameID = 2
  
  def __init__(self, huffFile, name):
    self.commands = {'af60': None, 'af68': self.af68,
		    'af62': None, 'af6a': self.af6a,
		    'af70': None, 'af78': self.af78,
		    'afa0': self.createImage
		    }
    
    # Huffman Table Dict
    self.huffman = self.readHuffmanTable(huffFile)
    
    #System Memory - Set to 0
    self.memory = [0] * 0xFFFFFF
    
    #Framebuffers locations, for 16 bit color information
    # The 16 bit buffers store two hex values per pixel, this two make up the 
    # difference from the previous pixel according to the huffman table
    self._WFB1 = 0xB8AD00
    self._WFB1Max = 0xC75300
    self._WFB1Dif = 0x0EA600 #800*600*2
    
    self._WFB2 = 0x38AD00
    self._WFB2Max = 0x475300
    self._WFB2Dif = 0x0EA600 #800*600*2
    
    #Framebuffers locations, for 8 bit color information
    # The 8 bit buffers store one hex value per pixel, this make up the 
    # difference from the previous pixel according to the huffman table, which 
    # does not exist as of today, 25 Nov. 2013
    self._8WFB1_1 = 0xFC5680
    self._8WFB1Max_1 = 0x1000000
    self._8WFB1_2Dif = 0x03A980
    
    self._8WFB1_2 = 0x000000
    self._8WFB1Max_2 = 0x03A980
    self._8WFB1_2Dif = 0x03A980
    
    self._8WFB1Dif = 0x03A980+0x03A980 #800*600
    
    self._8WFB2 = 0x7C5680
    self._8WFB2Max = 0x83a980
    self._8WFB2Dif = 0x075300 #800*600
    
    #Frame Resolution
    self.height = 600
    self.width = 800
    
    #Pre-calculate BGR565 values
    self.calcAllBGR565()
    
    #OpenCV Frame for each buffer and BGR channel
    self.frameID = 1
    self.frame1 = np.zeros((self.height, self.width, 3), dtype=np.uint8)
    self.frame2 = np.zeros((self.height, self.width, 3), dtype=np.uint8)
    self.empty = np.zeros((self.height, self.width, 3), dtype=np.uint8)
    
    #OpenCV Video buffer
    self.vidBuffer = cv2.VideoWriter(name + '.avi', cv2.cv.CV_FOURCC('M','J','P','G'), 1, (self.width, self.height))
  
  def dif2565BGRR(self, val):
    '''Retrieves the BGR values for a given difference value
    '''
    val %= 0xFFFF
    val = abs(val)
    
    BGR = [0, 0, 0]
    BGR[0] = (val & BLUE_MASK) * factor5Bit
    BGR[1] = ((val & GREEN_MASK) >> 0x05) * factor6Bit
    BGR[2] = ((val & RED_MASK)   >> 0x0B)  * factor5Bit
    
    return np.array(BGR, dtype=np.uint8)
  
  def dif2565BGR(self, val):
    '''Retrieves the BGR values for a given difference value
    '''
    return self.BGR565[abs(val%0xFFFF)]
  
  def createImage(self):
    '''This will create the image
    '''
    if self.frameID == 1:
      offset = self._WFB1
    else:
      offset = self._WFB2
    
    for pixel in range(self.height * self.width):
	val1 = self.memory[offset + 2*pixel + 0] << 8
	val2 = self.memory[offset + 2*pixel + 1]
	val = val1 + val2
	
	BGR = self.dif2565BGR(val)
	
	self.frame1[pixel/self.width, pixel%self.width] = BGR

  def createImageR(self):
    '''This will create the image
    '''
    return 1
  
  def processCommand(self, line):
    '''Process one line of the USB communication, after parsing.
    '''
    #parameters = line.rstrip('\n').split(' ')
    parameters = line
    if len(parameters) < 3 or len(parameters) > 4:
      return False
      
    cmd = parameters[0]
    offset = int(parameters[1], 16)
    length = int(parameters[2], 16)
    if length == 0:
      length = 256
    
    if cmd == 'af78':
      self.af78R(offset, length, parameters[3])
    elif cmd == 'af6a':
      self.af6aR(offset, length, int(parameters[3], 16))
    elif cmd == 'af68':
      self.af68R(offset, length, parameters[3])
    elif cmd == 'af20':
      self.af20(parameters[1], parameters[2])
      
    return True

  def ijOffset(self, offset):
    if self._WFB1 <= offset <= self._WFB1Max:
      frame = 1
      minOff = self._WFB1
      maxOff = self._WFB1Max
    else:#if self._WFB2 <= offset <= self._WFB2Max:
      frame = 2
      minOff = self._WFB2
      maxOff = self._WFB2Max
    
    pixel = (offset - minOff)/2
    return pixel/self.width, pixel%self.width, frame

if __name__ == '__main__':
  huffFile = sys.argv[1]
  cmds = sys.argv[2]
  
  fStream = open(cmds, 'r')
  stream = fStream.readlines()
  fStream.close()
  
  dlEmu = emulator(huffFile)
  #cv2.namedWindow('Stream buff1', cv2.WINDOW_NORMAL)
  #cv2.namedWindow('Stream buff2', cv2.WINDOW_NORMAL)
  
  count = 0
  for line in stream:
    
    if line[0:4] == 'afa0':
      dlEmu.createImage()
      dlEmu.createImage()
      
      if count % 100 == 0:
	print count
      count += 1
      continue
    
    dlEmu.processCommand(line)
  dlEmu.vidBuffer.release()
  print 'Done'
  
  