# -*- coding: iso-8859-15 -*-
#*******************************************************************************
#Fábio Reis - 2013, Dec
#fabio.reis -at- ist.utl.pt
#HDA - Auditbox
#*******************************************************************************
#Display Link USB Protocol decryptor algorithm

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

class Decrypt:
  
  keybuffer = [0] * 0x11000
  ofsbuffer = [0] * 0x1000
  
  key = [0] * 0x10
  offset = 0
  
  def dl_crc12(self, data, length):
    rem = 0
    for i in range(length):
      for j in range(8):
	rem = (rem << 1) | ((data[i] >> j) & 0x01)
	if rem & 0x1000:
	  rem = rem ^ 0x180F
    return rem
  
  def dl_generate_key(self):
    coeffs = [0] * 0x20
    count = 0
    
    # loop1
    for i in range(0x20):
      tmp = 1 << i
      if (tmp & 0x0829) == 0:
	continue
      
      coeffs[count] = i
      count += 1
    
    val = 0x01
    
    # loop2
    for i in range(0x11000):
      
      self.keybuffer[i] = val & 0xFF
      
      if i < 0x1000:
	self.ofsbuffer[val] = i
	
      # loop3
      for j in reversed(range(9)[1:]):
	res = 0
	
	# loop4
	for k in range(count):
	  coeff = coeffs[k]
	  coeff = val >> coeff
	  res = res ^ coeff
	
	res = res & 1
	res = res ^ (2 * val)
	val = res & 0xFFF
  
  def setKey(self, key):
    self.key = key
    self.dl_generate_key()
    
    crc = self.dl_crc12(self.key, 16)
    self.offset = self.ofsbuffer[crc]
    
    print 'key crc: {0}, start offset: {1}'.format(hex(crc), hex(self.offset))
  
  def decrypt(self, string):
    result = []
    
    buffered = chunks(string, 4095)
    for i, buff in enumerate(buffered):      
      size = len(buff)
      buff = [c.encode('hex') for c in buff]
      for j in range(size):
	buff[j] = int(buff[j],16) ^ self.keybuffer[j + self.offset]
	
      self.offset += size
      self.offset %= 4095
      
      result.append(buff)
    
    return result
  
  def __init__(self, key):
    self.setKey(key)
    print 'Decryptin key set.'