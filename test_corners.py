from board_reader import BoardReader
from time import sleep
from os import listdir
from os.path import isfile, join

test_file_path = "test_images_find_corners"
test_files = sorted([test_file_path + '/' + f for f in listdir(test_file_path) if isfile(join(test_file_path, f))])

resolution = (1920, 1080) 
board_dimensions = (12, 8)

reader = BoardReader(resolution, board_dimensions, True, True)

for image in test_files:
  print(image)
  reader.debug_path = image
  board = reader.getBoard()
