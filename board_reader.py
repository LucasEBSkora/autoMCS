from cv2 import __version__ as cv2_version
from cv2 import aruco, cvtColor, COLOR_RGB2GRAY, getPerspectiveTransform, perspectiveTransform # indispensable
from cv2 import imwrite, polylines, line, putText, circle, warpPerspective, FONT_HERSHEY_DUPLEX # for debug image printing
from cv2 import imread # used for tests
from datetime import datetime # debug image printing
from numpy import int32, int8, uint8, ravel, zeros, array, float32, mean, empty
from os import system # clearing image folder

#from picamera_camera import Camera
from opencv_camera import Camera

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

	def __init__(self, resolution = (1920, 1280), board_dimensions = (12, 8), write_steps = False, DEBUG_MODE = False):
		self.resolution = int32(resolution)
		self.board_dimensions = int32(board_dimensions)
		self.write_steps = write_steps
		self.DEBUG_MODE = DEBUG_MODE
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

		system("rm arucos/*") # clears aruco image folder so we don't get images we already have through scp command
		if self.write_steps:
			self.now = self._getTimeString() # gets current time string to use in image names

	def _getTimeString(self):
		if self.DEBUG_MODE and not self.debug_path is None:
			return self.debug_path.split('/')[1]
		else:
			return datetime.now().strftime("%Y.%m.%d-%H:%M:%S")

	def _getArucoCorners(self):
		'''gets frame from camera and detects aruco codes, returning the coordinates of their corners'''
		if self.DEBUG_MODE:
			img = imread(self.debug_path)
		else:
			time = datetime.now()
			img = self.camera.capture()
			print(f"image read in {(datetime.now() - time).total_seconds()} seconds!")

		gray = cvtColor(img, COLOR_RGB2GRAY)

		if self.write_steps:
			imwrite(f"arucos/{self.now}_RAW.png", img)
		if cv2_version == '4.7.0':
			corners, ids, rejectedImgPoints = self.arucoDetector.detectMarkers(gray)
		else:
			corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, self.dictionary)

		if ids is None:
			return []

		if self.write_steps:
			self.img = img

		ids = ravel(ids)

		unravel_corners = []
		for i in range(len(ids)):
			unravel_corners.append(corners[i][0])

		return [ids, int32(unravel_corners)]

	def _getBoardCorners(self, ids_and_corners):
		'''Gets coordinates of the four corners of the board'''
		corners = zeros((4, 2), int32)
		found_corner = [0] * 4

		for i in range(len(ids_and_corners[0])):
			id = ids_and_corners[0][i]
			if 0 <= id and id <= 3:
				found_corner[id] += 1
				corners[id] = ids_and_corners[1][i][0]

		found_all_corners = True
		for i in range(0, 4):
			if found_corner[i] != 1:
				found_all_corners = False

		if not found_all_corners:
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

			if not self.last_position_corners is None:
				for i in range(0, 4):
					if found_corner[i] == 0:
						corners[i] = self.last_position_corners[i]
			else:
				print("can't find all points!")
				return None

		self.last_position_corners = corners

		if self.write_steps:
			self.img = polylines(self.img, int32([corners]), True, (0, 255, 0), 5)
			imwrite(f"arucos/{self.now}_BORDER.png", self.img)

		return corners

	def _trasformPerspective(self, board_corners, ids_and_corners):
		'''applies a perspective transformation to the corner cordinates mapping the corners of the board to the corners of the image'''
		image_corners = float32([[0, self.resolution[1]],  self.resolution, [self.resolution[0], 0], [0, 0]])
		matrix = getPerspectiveTransform(float32(board_corners), image_corners)

		if self.write_steps:
			self.img = warpPerspective(self.img, matrix, self.resolution)
			inc = self.resolution / self.board_dimensions

			imwrite(f"arucos/{self.now}_TRANSFORM.png", self.img)

			for i in range(1, self.board_dimensions[0]):
				first_point = tuple(int32([i*inc[0], self.resolution[1]]))
				second_point = tuple(int32([i*inc[0], 0]))
				line(self.img, first_point, second_point, (255, 0, 0), 5)

			for i in range(1, self.board_dimensions[1]):
				first_point = tuple(int32([self.resolution[0], i*inc[1]]))
				second_point = tuple(int32([0, i*inc[1]]))
				line(self.img, first_point, second_point, (255, 0, 0), 5)

			imwrite(f"arucos/{self.now}_BOARD.png", self.img)

		ids_and_corners[1] = perspectiveTransform(float32(ids_and_corners[1]), matrix)

		return ids_and_corners

	def _getPieceCenters(self, ids_and_corners):
		'''gets the center of each chess piece identified in the image'''
		filtered_ids = []
		piece_centers = []
		for i in range(len(ids_and_corners[0])):
			id = ids_and_corners[0][i]
			corners = ids_and_corners[1][i]
			if 4 <= id and id <= 15:
				center = mean(corners, axis=0)
				if self.write_steps:
					self.img = putText(self.img, str(id), int32(center), FONT_HERSHEY_DUPLEX, 1, (0, 0, 255), 1)
					self.img = circle(self.img, int32(center), 1, (0, 0, 255), 5)
				filtered_ids.append(id)
				piece_centers.append(center)
			if id > 15:
				print(f"unexpected ID {id} at coordinates {corners}")
		if self.write_steps:
			imwrite(f"arucos/{self.now}_PIECES.png", self.img)
		return [filtered_ids, int32(piece_centers)]

	def _generateBoard(self, board_corners, piece_centers):
		board = zeros(self.board_dimensions, dtype = int8)
		ids = piece_centers[0]
		if len(ids) == 0:
			return board
		square_size = self.resolution / self.board_dimensions
		coordinates = int8(piece_centers[1] / square_size)

		for i in range(len(ids)):
			id = ids[i]
			coord = int8([coordinates[i][0] , self.board_dimensions[1] - 1 - coordinates[i][1]])
			if coord[0] > self.board_dimensions[0] or coord[1] > self.board_dimensions[1]:
				print(f"piece {BoardReader.piece_types[id]} at coordinates {tuple(coord)} out of board with dimensions {tuple(coord)}")
			elif board[coord[0]][coord[1]] != 0:
				print(f"position {coord} has pieces {board[coord[0]][coord[1]]} and {BoardReader.piece_types[id]}!")
				board[coord[0]][coord[1]] *= 100
				board[coord[0]][coord[1]] += id
			else:
				board[coord[0]][coord[1]] = id
		return board

	def printBoard(self, board):
		'''pretty prints the chess board matrix'''
		for i in range(board.shape[1] - 1, -1, -1):
			line = ""
			for j in range(board.shape[0]):
				value = board[j][i]
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

	def getBoard(self):
		''' takes picture and gets chess board matrix from it'''
		if self.write_steps:
			self.now = self._getTimeString()

		ids_and_corners = self._getArucoCorners()
		if len(ids_and_corners) == 0:
			return None

		board_corners = self._getBoardCorners(ids_and_corners)
		if board_corners is None:
			return None

		ids_and_transformed_corners = self._trasformPerspective(board_corners, ids_and_corners)

		piece_centers = self._getPieceCenters(ids_and_transformed_corners)
		board = self._generateBoard(board_corners, piece_centers)
		return board

if __name__ == "__main__":
	reader = BoardReader(write_steps = True)
	board = reader.getBoard()
	if board is None:
		print(":(")
	else:
		reader.printBoard(board)
