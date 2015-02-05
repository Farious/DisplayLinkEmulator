#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#*******************************************************************************
#Fábio Reis - 2013, Dec
#fabio.reis -at- ist.utl.pt
#HDA - Auditbox
#*******************************************************************************
import base64, sys, dpkt, datetime, math, time
import pickle, numpy as np, gc

import cv2

import displayLinkDecryptor as Decryptor
import displayLinkEmulator as Emulator
import displayLinkParser as Parser

commands = {'af68': True,
	    'af6a': True,
	    'af78': True,
	    'af20': True
	    }

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def dumpParser(f):
  pcap = dpkt.pcap.Reader(f)
  packets = pcap.readpkts()
  
  # packets is a list of tuples of the form: (timestamp, binary_data)
  encryptionkey = []
  parsedPackets = []
  for i, pack in enumerate(packets):
    packAux = pack[1].encode('hex')
    
    if packAux[16:18] == '53':
      if packAux[18:20] == '02' and len(packAux[128:]) == 2*16:
	encryptionkey = packAux[128:]
      elif packAux[18:20] == '03' and len(packAux[128:]) > 0 and len(encryptionkey) > 0:
	parsedPackets.append([pack[0], packAux[128:], i])
  
  hexAllVal = []
  for pack in parsedPackets:
    hexAllVal.append(pack[1])
  
  hexVal = ''.join(hexAllVal)
  binHex = base64.b16decode(hexVal, True)
  
  return binHex, parsedPackets, encryptionkey

def _print_text(img, text):
    textcolor = (255, 255, 255)
    bgcolor = (0, 0, 0)
    # get text size
    bottomright, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_PLAIN,
				      1, 1)
    # give one extra pixel on bottom
    bottomright = (bottomright[0], bottomright[1] + 1)
    # draw solid rectangle
    cv2.rectangle(img, (0, 0), bottomright, bgcolor, -1)
    # put text
    cv2.putText(img, text, (1, 11),
		cv2.FONT_HERSHEY_PLAIN, 1, textcolor)

if __name__ == '__main__':
  huffFile = sys.argv[1]
  input1 = sys.argv[2]
  
  logger = open(input1 + '.log.tmp', 'w')
  
  # Creating Display Link Emulator
  print 'Initializing display link emulator.'
  dlEmu = Emulator.emulator(huffFile, input1)
  print 'Emulator initialized.'
  
  # First we process the dump file and filter out the packaged that doesn't
  # concern the Display Link Comunication Protocol.
  print 'Starting dump filter and parser. This may take some time.'
  f = open(input1, 'rb')
  binHex, parsed, key = dumpParser(f)
  f.close()
  print 'Parsing and filtering complete.'
  
  # Processing the encryption key
  if len(key) < 2*16:
    print 'Couldn\'t find the correct key.'
    raise ValueError
  key = list(chunks(key, 2))
  key = [int('0x' + d, 16) for d in key]
  
  # Creating a decryption object and setting the encryption key and offset
  dc = Decryptor.Decrypt(key)
  
  # Starting actual decryption and display link emulation
  # We will draw an actual image only when there is a delta of atleast 1 sec. 
  # between each packet
  print 'Starting decryption.'
  
  # Use this object to parse the stream into readable commands
  cv2.namedWindow('Stream buffered', cv2.WINDOW_NORMAL)
  parser = Parser.DisplayLinkParser()  
  tempProcessed = []
  zeroTime = parsed[0][0]
  lastTime = parsed[0][0]
  diffTime = 0
  length = float(len(parsed))
  for i, usbPkt in enumerate(parsed):
    sys.stdout.write("Processing progress: %f%% : pkt> %d of %d  \r" % ((i/length)*100, i, length))
    sys.stdout.flush()
    
    tmp = base64.b16decode(usbPkt[1], True)
    
    offset = dc.offset
    processed = dc.decrypt(tmp)
    
    # Concatenate bulks of 4095 if needed and transforms 0xXX to XX
    processed = [pkt for stream in processed for pkt in stream]
    processed = ['{:02x}'.format(x) for x in processed]
    
    # Error Checking
    if len(processed) < 4096:
      initialOff = offset
      if processed[-2:] != ['af', 'a0']:
	offset += 1
	dc.offset = offset % 4095
	processed = dc.decrypt(tmp)
	
	# Concatenate bulks of 4095 if needed and transforms 0xXX to XX
	processed = [pkt for stream in processed for pkt in stream]
	processed = ['{:02x}'.format(x) for x in processed]
	
	for i, w in enumerate(processed):
	  if w == 'af':
	    processed = processed[i:]
	    tempProcessed = []
	    break
	
	if initialOff == offset:
	  dc.offset = initialOff
	  logger.write('I had a error at packet: %d.' % (usbPkt[2]))
	  continue
    
    tempProcessed += processed
    
    if processed[-2:] == ['af', 'a0']:
      actualTime = usbPkt[0]
      diffTime += (actualTime - zeroTime) - (lastTime - zeroTime)
      if diffTime >= 1:
	lastTime = actualTime
	diffTime -= math.trunc(diffTime)
	
	# Parse commands
	parsed = parser.parse(tempProcessed)
	
	# Pass commands to emulator
	for cmd in parsed:
	  if commands.get(cmd[0], False):
	    dlEmu.processCommand(cmd)
	    
	# Calculate image
	if cmd[0] == 'afa0':
	  #dlEmu.createImage()
	  
	  if dlEmu.frameID == 1:
	    img = dlEmu.frame1
	  else:
	    img = dlEmu.frame2
	  
	  if img != None:
	    _print_text(img,  str(datetime.datetime.fromtimestamp(lastTime)))
	    dlEmu.vidBuffer.write(img)
	
	# Cleaning processed commands
	tempProcessed = []
	gc.collect()
  dlEmu.vidBuffer.release()
  logger.close()
  print 'Finished decrypting'
  