from board_reader import BoardReader
from time import sleep

#resolution = (640, 480) #unviable
#resolution = (960, 720) #unviable
#resolution = (1280, 960) #almost viable
#resolution = (1440, 1050) #viable at 7mm
resolution = (1920, 1080) #viable at 7mm
#resolution = (1920, 1280) #viable at 7mm
#resolution = (3280, 2464) #kills the crab
board_dimensions = (12, 8)

reader = BoardReader(resolution, board_dimensions, True)

board = reader.getBoard()
if board is None:
  reader.printBoard(board)
else:
  print(":(")