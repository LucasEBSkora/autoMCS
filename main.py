from board_reader import BoardReader
from time import sleep

#resolution = (640, 480) #unviable
#resolution = (960, 720) #unviable
#resolution = (1280, 960) #almost viable
#resolution = (1440, 1056) #viable at 7mm
resolution = (1920, 1088) #viable at 7mm
#resolution = (1920, 1296) #viable at 7mm
#resolution = (2528, 1808) #sloooooow
#resolution = (3296, 2464) #kills the crab
board_dimensions = (8, 12)

reader = BoardReader(resolution, board_dimensions, write_steps = False)

finish_game = ""

while finish_game != "q":
	board, real_positions, possible_moves = reader.getBoardRealPositionsAndPossibleMoves()
	if board is None:
		print(":(")
	else:
		reader.printBoard(board)
		print(possible_moves)
	print("press q and write enter to finish game")
	finish_game = input()
