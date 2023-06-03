from cv2 import __version__ as cv2_version
from cv2 import aruco, cvtColor, COLOR_RGB2GRAY, getPerspectiveTransform, perspectiveTransform # indispensable
from cv2 import imwrite, polylines, line, putText, circle, warpPerspective, FONT_HERSHEY_DUPLEX # for debug image printing
from cv2 import imread # used for tests
from datetime import datetime # debug image printing
from numpy import int32, int8, ravel, zeros, float32, mean, flip
from os import system # clearing image folder
from uci_string_generator import UCIStringGenerator

from picamera_camera import Camera
#from opencv_camera import Camera

class BoardReader:
	'''reads images from camera and translates to a chess board matrix with piece positions'''

	piece_types = {
		4: '♟',
		5: '♜',
		6: '♞',
		7: '♝',
		8: '♚',
		9: '♛',
		10: '♙',
		11: '♖',
		12: '♘',
		13: '♗',
		14: '♔',
		15: '♕',
	}
	'''maps aruco IDs to chess piece and color'''

	def __init__(self, resolution = (1920, 1280), board_dimensions = (8, 12), write_steps = False, DEBUG_MODE = False, print_time = False):
		self.resolution = int32(resolution)
		self.board_dimensions = int32(board_dimensions)
		self.write_steps = write_steps
		self.DEBUG_MODE = DEBUG_MODE
		self.print_time = print_time
		self.UCI_generator = UCIStringGenerator()

		if self.DEBUG_MODE:
			self.debug_path = None
		else:
			self.camera = Camera(resolution)

			self.resolution = self.camera.getRealResolution()

		if cv2_version == '4.7.0':
			dictionary = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
			self.arucoDetector = aruco.ArucoDetector(dictionary)
		else:
			self.dictionary = aruco.Dictionary_get(aruco.DICT_4X4_50)

		self.last_position_corners = None
		self.last_board = None

		system("rm arucos/*") # clears aruco image folder so we don't get images we already have through scp command
		if self.write_steps:
			self.now = self._getTimeString() # gets current time string to use in image names

	def _getTimeString(self):
		if self.DEBUG_MODE and not self.debug_path is None:
			return self.debug_path.split('/')[1]
		else:
			return datetime.now().strftime("%Y.%m.%d-%H:%M:%S")

	# for some reason detectMarkers returns a tuple of n arrays of dimension (1, 4, 2) when an (n, 4, 2) array is a lot more useful
	def _formatArucoCornerArray(self, corners):
		return int32(corners).reshape((len(corners), 4, 2))
	
	def _detectArucos(self, img):
		if cv2_version == '4.7.0':
			corners, ids, _ = self.arucoDetector.detectMarkers(img)
		else:
			corners, ids, _ = aruco.detectMarkers(img, self.dictionary)
		return corners, ids

	def _getArucoCorners(self):
		'''gets frame from camera and detects aruco codes, returning the coordinates of their corners'''
		if self.DEBUG_MODE:
			img = imread(self.debug_path)
		else:
			time = datetime.now()
			img = self.camera.capture()
			if self.print_time:
				print(f"image read in {(datetime.now() - time).total_seconds()} seconds!")

		gray = cvtColor(img, COLOR_RGB2GRAY)

		if self.write_steps:
			imwrite(f"arucos/{self.now}_RAW.png", img)
		time = datetime.now()
		corners, ids = self._detectArucos(gray)		
		if self.print_time:
			print(f"arucos read in {(datetime.now() - time).total_seconds()} seconds!")

		if ids is None:
			return []

		if self.write_steps:
			self.img = img

		ids = ravel(ids)

		return [ids, self._formatArucoCornerArray(corners)]

	def _showCornerNotFoundMessage(self, found_corner):
		corners_found = sum(found_corner)
		print(f"found {corners_found} corners only!")
		if found_corner[0] == 0:
			print("didn't find lower left corner!")
		if found_corner[1] == 0:
			print("didn't find lower right corner!")
		if found_corner[2] == 0:
			print("didn't find upper right corner!")
		if found_corner[3] == 0:
			print("didn't find upper left corner!")

	def _restoreLastFoundCorners(self, found_corner, corners):
		for i in range(0, 4):
			if found_corner[i] == 0:
				corners[i] = self.last_position_corners[i]
	
	def _printImageWithBoardCorners(self, corners):
		self.img = polylines(self.img, int32([corners]), True, (0, 255, 0), 5)
		imwrite(f"arucos/{self.now}_BORDER.png", self.img)

	def _checkFoundAllCorners(self, found_corner):
		for corner in found_corner:
			if corner == 0:
				return False
		return True

	def _getBoardCorners(self, ids_and_corners):
		'''Gets coordinates of the four corners of the board'''
		corners = zeros((4, 2), int32)
		found_corner = [0] * 4

		for i in range(len(ids_and_corners[0])):
			id = ids_and_corners[0][i]
			if 0 <= id and id <= 3:
				found_corner[id] += 1
				corners[id] = ids_and_corners[1][i][0]

		found_all_corners = self._checkFoundAllCorners(found_corner)			

		if not found_all_corners:
			self._showCornerNotFoundMessage(found_corner)

			if self.last_position_corners is None:
				print("can't find all points!")
				return None
			
			corners = self._restoreLastFoundCorners(found_corner, corners)				

		self.last_position_corners = corners

		if self.write_steps:
			self._printImageWithBoardCorners(corners)

		return corners
	
	def	_getImageCorners(self):
		return float32([[0, self.resolution[1]],  self.resolution, [self.resolution[0], 0], [0, 0]])
	
	def _getBoardSquareDimensions(self):
		return self.resolution / flip(self.board_dimensions)
	
	def _drawNthVerticalLine(self, distance_between_lines, n):
		first_point = tuple(int32([n*distance_between_lines, self.resolution[1]]))
		second_point = tuple(int32([n*distance_between_lines, 0]))
		line(self.img, first_point, second_point, (255, 0, 0), 5)

	def _drawNthHorizontalLine(self, distance_between_lines, n):
		first_point = tuple(int32([self.resolution[0], n*distance_between_lines]))
		second_point = tuple(int32([0, n*distance_between_lines]))
		line(self.img, first_point, second_point, (255, 0, 0), 5)
	
	def _trasformPerspective(self, board_corners, ids_and_corners):
		'''applies a perspective transformation to the corner cordinates mapping the corners of the board to the corners of the image'''
		image_corners = self._getImageCorners() 
		matrix = getPerspectiveTransform(float32(board_corners), image_corners)

		if self.write_steps:
			self.img = warpPerspective(self.img, matrix, self.resolution)
			(vertical_distance_between_lines, horizontal_distance_between_lines) = self._getBoardSquareDimensions()

			imwrite(f"arucos/{self.now}_TRANSFORM.png", self.img)

			for i in range(1, self.board_dimensions[0]):
				self._drawNthHorizontalLine(horizontal_distance_between_lines, i)

			for i in range(1, self.board_dimensions[1]):
				self._drawNthVerticalLine(vertical_distance_between_lines, i)

			imwrite(f"arucos/{self.now}_BOARD.png", self.img)

		ids_and_corners[1] = perspectiveTransform(float32(ids_and_corners[1]), matrix)

		return ids_and_corners

	def _drawArucoCenterAndWriteID(self, id, center):
		color = (0, 0, 255)
		
		id = str(id)
		center = int32(center)
		self.img = putText(self.img, id, center, FONT_HERSHEY_DUPLEX, 1, color, 1)
		self.img = circle(self.img, center, 1, color, 5)
	
	def _getPieceCenters(self, ids_and_corners):
		'''gets the center of each chess piece identified in the image'''
		filtered_ids = []
		piece_centers = []
		ids = ids_and_corners[0]
		centers = mean(ids_and_corners[1], axis=1)

		for i in range(len(ids)):
			id = ids[i]
			center = centers[i]
			if id < 4:
				continue

			if id <= 15:
				filtered_ids.append(id)
				piece_centers.append(center)
			else:
				print(f"unexpected ID {id} at coordinates {center}")

			if self.write_steps:
				self._drawArucoCenterAndWriteID(id, center)

		if self.write_steps:
			imwrite(f"arucos/{self.now}_PIECES.png", self.img)
		return [filtered_ids, int32(piece_centers)]

	def _calculatePieceCoordinates(self, centers):
		square_size = self._getBoardSquareDimensions()
		coordinates = flip(int8(centers / square_size), axis=1)
		return coordinates

	def _isPieceOutOfBoard(self, piece_position):
		return piece_position[0] > self.board_dimensions[0] or piece_position[1] > self.board_dimensions[1]

	def _generateBoard(self, piece_centers):
		board = zeros(self.board_dimensions, dtype = int8)
		real_positions = zeros((self.board_dimensions[0], self.board_dimensions[1], 2), dtype = int32)
		ids = piece_centers[0]
		if len(ids) == 0:
			return board
		coordinates = self._calculatePieceCoordinates(piece_centers[1])

		for i in range(len(ids)):
			id = ids[i]
			coord = coordinates[i]
			center = piece_centers[1][i]
			if self._isPieceOutOfBoard(coord):
				print(f"piece {BoardReader.piece_types[id]} at coordinates {tuple(coord)} out of board with dimensions {tuple(coord)}")
				continue
			if board[coord[0]][coord[1]] != 0:
				if board[coord[0]][coord[1]] == id:
					print(f"position {coord} has two pieces of type {BoardReader.piece_types[id]}! - treating piece as duplicate")
				else:
					print(f"position {coord} has pieces {BoardReader.piece_types[board[coord[0]][coord[1]]]} and {BoardReader.piece_types[id]}!")
					board[coord[0]][coord[1]] *= 100
					board[coord[0]][coord[1]] += id
				continue
			board[coord[0]][coord[1]] = id
			real_positions[coord[0]][coord[1]] = center
		return board, real_positions

	def _isNewPieceInPosition(self, last_id, new_id):
		return last_id == 0 and new_id > 0
	
	def _isPieceNoLongerInPosition(self, last_id, new_id):
		return last_id > 0 and new_id == 0
	
	def _isDifferentPieceInPosition(self, last_id, new_id):
		return last_id != new_id

	def _calculateDifferencesBetweenBoards(self, last_board, new_board):
		pieces_not_in_last_position = []
		pieces_in_new_position = []

		for i in range(new_board.shape[0]):
			for j in range(new_board.shape[1]):
				last_piece_id = last_board[i][j]
				new_piece_id = new_board[i][j]
				if self._isNewPieceInPosition(last_piece_id, new_piece_id):
					pieces_in_new_position.append((new_piece_id, (i, j)))
				elif self._isPieceNoLongerInPosition(last_piece_id, new_piece_id):
					pieces_not_in_last_position.append((last_piece_id, (i, j)))
				elif self._isDifferentPieceInPosition(last_piece_id, new_piece_id):
					pieces_in_new_position.append((new_piece_id, (i, j)))
					pieces_not_in_last_position.append((last_piece_id, (i, j)))
		
		return pieces_not_in_last_position, pieces_in_new_position

	def _restoreMissingPieces(self, board, missing_pieces):
		for id, position in missing_pieces:
			if board[position[0]][position[1]] == 0:
				board[position[0]][position[1]] = id
		return board

	def _searchPossibleMovements(self, pieces_in_new_position, pieces_not_in_last_position):
		pieces_moved = []
		for new_piece in pieces_in_new_position:
			for old_piece in pieces_not_in_last_position:
				if new_piece[0] == old_piece[0]:
					pieces_moved.append((new_piece[0], old_piece[1], new_piece[1]))
					pieces_in_new_position.remove(new_piece)
					pieces_not_in_last_position.remove(old_piece)

		return pieces_moved, pieces_in_new_position, pieces_not_in_last_position

	def _verifyBoardAndSearchPossibleMovements(self, board, last_board):
		if board.shape != last_board.shape:
			return board
		pieces_not_in_last_position, pieces_in_new_position = self._calculateDifferencesBetweenBoards(last_board, board)
		pieces_moved, pieces_not_in_last_position, pieces_in_new_position = self._searchPossibleMovements(pieces_in_new_position, pieces_not_in_last_position)
		if len(pieces_moved) > 2:
			print("too many moved pieces!")
			for id, old_position, new_position in pieces_moved:
				print(f"chess piece {BoardReader.piece_types[id]} moved from {old_position} to {new_position}")

		# assumes pieces that we "lost" are in the same place, if there are not other pieces there
		board = self._restoreMissingPieces(board, pieces_not_in_last_position)
		return board, pieces_moved
	def printBoard(self, board):
		'''pretty prints the chess board matrix'''
		for i in range(board.shape[0]):
			line = ""
			for j in range(board.shape[1]):
				value = board[i][j]
				if value == 0:
					if (i + j ) % 2 == 0:
						line += '□'
					else:
						line += '■'
				elif value in BoardReader.piece_types:
					line += BoardReader.piece_types[value]
				else:
					line += '?'
			print(line)

	def getBoardRealPositionsAndPossibleMoves(self):
		''' takes picture and gets chess board matrix from it'''
		if self.write_steps:
			self.now = self._getTimeString()

		ids_and_corners = self._getArucoCorners()
		if len(ids_and_corners) == 0:
			return None, None, None

		time = datetime.now()

		board_corners = self._getBoardCorners(ids_and_corners)

		if not self.write_steps and self.print_time:
			print(f"found corners in {(datetime.now() - time).total_seconds()} seconds!")

		if board_corners is None:
			return None, None, None

		time = datetime.now()
		ids_and_transformed_corners = self._trasformPerspective(board_corners, ids_and_corners)

		if not self.write_steps and self.print_time:
			print(f"transformed perspective in {(datetime.now() - time).total_seconds()} seconds!")

		time = datetime.now()
		piece_centers = self._getPieceCenters(ids_and_transformed_corners)
		if not self.write_steps and self.print_time:
			print(f"calculated centers in {(datetime.now() - time).total_seconds()} seconds!")

		time = datetime.now()
		board, real_positions = self._generateBoard(piece_centers)
		if not self.write_steps and self.print_time:
			print(f"generated boards in {(datetime.now() - time).total_seconds()} seconds!")
			print("--------------------------------------------------------------------------------")

		possible_moves = None

		if not self.last_board is None:
			board, possible_moves = self._verifyBoardAndSearchPossibleMovements(board, self.last_board)
			possible_moves = self.UCI_generator.getUCIPossibleMove(board, possible_moves)
		self.last_board = board

		return board, real_positions, possible_moves

if __name__ == "__main__":
	reader = BoardReader(write_steps = True)
	board, _, _ = reader.getBoardRealPositionsAndPossibleMoves()
	if board is None:
		print(":(")
	else:
		reader.printBoard(board)
