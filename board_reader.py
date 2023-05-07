from cv2 import aruco, VideoCapture, cvtColor, COLOR_RGB2GRAY, getPerspectiveTransform, perspectiveTransform # indispensable
from cv2 import CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT, CAP_PROP_BUFFERSIZE # camera properties
from cv2 import imwrite, polylines, line, putText, circle, warpPerspective, FONT_HERSHEY_DUPLEX # for debug image printing
from datetime import datetime # debug image printing
import numpy as np
from numpy import int32, int8, ravel, zeros, array, float32, mean
from os import system # clearing image folder

class BoardReader:
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

	def __init__(self, resolution = (1920, 1280), board_dimensions = (12, 8), write_steps = False):
		self.resolution = int32(resolution)
		self.board_dimensions = int32(board_dimensions)
		self.write_steps = write_steps

		self.cap = VideoCapture(0)

		ret = self.cap.set(CAP_PROP_FRAME_WIDTH, resolution[0])

		if (ret != True):
			print("failed to set frame width")
			exit(-1)

		ret = self.cap.set(CAP_PROP_FRAME_HEIGHT,resolution[1])

		if (ret != True):
			print("failed to set frame height")
			exit(-1)

		ret = self.cap.set(CAP_PROP_BUFFERSIZE, 1)

		if (ret != True):
			print("failed to set buffer size")
			exit(-1)
		
		self.dictionary = aruco.Dictionary_get(aruco.DICT_4X4_50)

		if self.write_steps == True:
			system("rm arucos/*")
			self.now = datetime.now().strftime("%Y.%m.%d-%H:%M:%S")

	def __del__(self):
		self.cap.release()

	def _getArucoCorners(self):
		ret, img = self.cap.read()
		if ret != True:
			print("failed to read image!")
			return []

		print("image read!")
		gray = cvtColor(img, COLOR_RGB2GRAY)

		if self.write_steps == True:
			imwrite(f"arucos/{self.now}_RAW.png", img)
			imwrite(f"arucos/{self.now}_GRAY.png", gray)

		corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, self.dictionary)

		if self.write_steps == True:
			self.img = img

		ids = ravel(ids)

		unravel_corners = []
		if ids[0] != None:
			for i in range(len(ids)):
				unravel_corners.append(corners[i][0])
			return [ids, int32(unravel_corners)]
		else:
			return []

	def _getBoardCorners(self, ids_and_corners):
		corners = zeros((4, 2), int32)
		LL = None
		LR = None
		UR = None
		UL = None

		corners_found = 0
		for i in range(len(ids_and_corners[0])):
			id = ids_and_corners[0][i]
			if id == 0:
				LL = ids_and_corners[1][i][0]
				corners_found += 1
			elif id == 1:
				LR = ids_and_corners[1][i][0]
				corners_found += 1
			elif id == 2:
				UR = ids_and_corners[1][i][0]
				corners_found += 1
			elif id == 3:
				UL = ids_and_corners[1][i][0]
				corners_found += 1
		if corners_found != 4:
			print(f"found {corners_found} corners only!")
			if LL is None:
				print("didn't find lower left corner!")
			if LR is None:
				print("didn't find lower right corner!")
			if UR is None:
				print("didn't find upper right corner!")
			if UL is None:
				print("didn't find upper left corner!")

			return [], ids_and_corners

		corners = array([LL, LR, UR, UL])
		
		if self.write_steps == True:
			self.img = polylines(self.img, int32([corners]), True, (0, 255, 0), 5)
			imwrite(f"arucos/{self.now}_BORDER.png", self.img)

		return corners

	def _trasformPerspective(self, board_corners, ids_and_corners):
		image_corners = float32([[0, self.resolution[1]],  self.resolution, [self.resolution[0], 0], [0, 0]])
		matrix = getPerspectiveTransform(float32(board_corners), image_corners)
		
		if self.write_steps == True:
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
		filtered_ids = []
		piece_centers = []
		for i in range(len(ids_and_corners[0])):
			id = ids_and_corners[0][i]
			corners = ids_and_corners[1][i]
			if 4 <= id and id <= 15:
				center = mean(corners, axis=0)
				if self.write_steps == True:
					self.img = putText(self.img, str(id), int32(center), FONT_HERSHEY_DUPLEX, 1, (0, 0, 255), 1)
					self.img = circle(self.img, int32(center), 1, (0, 0, 255), 5)
				filtered_ids.append(id)
				piece_centers.append(center)
			if id > 15:
				print(f"unexpected ID {id} at coordinates {corners}")
		imwrite(f"arucos/{self.now}_PIECES.png", self.img)
		return [filtered_ids, int32(piece_centers)]

	def _generateBoard(self, board_corners, piece_centers):
		board = zeros(self.board_dimensions, dtype = int8)
		ids = piece_centers[0]
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
		if self.write_steps == True:
			self.now = datetime.now().strftime("%Y.%m.%d-%H:%M:%S")
		
		ids_and_corners = self._getArucoCorners()
		if len(ids_and_corners) > 0:
			return None
	
		board_corners, ids_and_corners = self._getBoardCorners(ids_and_corners)
		piece_centers = self._getPieceCenters(ids_and_corners)
		board = self._generateBoard(board_corners, piece_centers)
		return board
		
