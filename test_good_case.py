from board_reader import BoardReader

resolution = (1920, 1080) 
board_dimensions = (8, 12)

reader = BoardReader(resolution, board_dimensions, write_steps = False, DEBUG_MODE = True, print_time = True)

reader.debug_path = "./test_image_real.png"
board = reader.getBoard()
board = reader.getBoard()
reader.printBoard(board)