from board_reader import BoardReader
from os import listdir
from os.path import isfile, join

#test_file_path = "f_test_generate_moves"
test_file_path = "f_test_generate_capture"
test_files = sorted([test_file_path + '/' + f for f in listdir(test_file_path) if isfile(join(test_file_path, f))])

resolution = (1920, 1088) 
board_dimensions = (8, 12)

reader = BoardReader(resolution, board_dimensions, DEBUG_MODE= True, write_steps=True)

for image in test_files:
  reader.debug_path = image
  board, real_positions, possible_moves = reader.getBoardRealPositionsAndPossibleMoves()
  reader.printBoard(board)
  print(possible_moves)
