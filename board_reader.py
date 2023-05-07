#most importantly for this code to run is to import OpenCV
import cv2
from cv2 import aruco, VideoCapture, CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT, COLOR_RGB2GRAY, polylines, line, cvtColor, putText, FONT_HERSHEY_DUPLEX, circle, imwrite, destroyAllWindows, perspectiveTransform
import numpy as np
from time import sleep
from datetime import datetime
from os import system

system("rm arucos/*")

cap = VideoCapture(0)

#resolution = (640, 480) #unviable
#resolution = (960, 720) #unviable
#resolution = (1280, 960) #almost viable
#resolution = (1440, 1050) #viable at 7mm
resolution = (1920, 1080) #viable at 7mm
#resolution = (1920, 1280) #viable at 7mm
#resolution = (3280, 2464) #kills the crab
resolution = np.int32(resolution)
board_dimensions = np.int32([12, 8])

ret = cap.set(CAP_PROP_FRAME_WIDTH, resolution[0])

if (ret != True):
	print("failed to set frame width")
	exit(-1)

ret = cap.set(CAP_PROP_FRAME_HEIGHT,resolution[1])

if (ret != True):
	print("failed to set frame height")
	exit(-1)

cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
dictionary = aruco.Dictionary_get(aruco.DICT_4X4_50)

def getArucoCorners():

	_, img = cap.read()
	print("image read!")
	gray = cvtColor(img, COLOR_RGB2GRAY)

	corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, dictionary)

	ids = np.ravel(ids)

	unravel_corners = []
	if ids[0] != None:
		for i in range(len(ids)):
			unravel_corners.append(corners[i][0])
		return img, [ids, np.int32(unravel_corners)]
	else:
		return img, []

def getBoardCorners(img, ids_and_corners):
	corners = np.zeros((4, 2), np.int32)
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

		return img, [], ids_and_corners

	corners = np.array([LL, LR, UR, UL])
	img = polylines(img, np.int32([corners]), True, (0, 255, 0), 5)

	image_corners = np.float32([[0, resolution[1]],  resolution, [resolution[0], 0], [0, 0]])
	matrix = cv2.getPerspectiveTransform(np.float32(corners), image_corners)
	img = cv2.warpPerspective(img, matrix, resolution)

	inc = resolution / board_dimensions

	for i in range(1, board_dimensions[0]):
		first_point = tuple(np.int32([i*inc[0], resolution[1]]))
		second_point = tuple(np.int32([i*inc[0], 0]))
		line(img, first_point, second_point, (255, 0, 0), 5)

	for i in range(1, board_dimensions[1]):
		first_point = tuple(np.int32([resolution[0], i*inc[1]]))
		second_point = tuple(np.int32([0, i*inc[1]]))
		line(img, first_point, second_point, (255, 0, 0), 5)

	ids_and_corners[1] = perspectiveTransform(np.float32(ids_and_corners[1]), matrix)

	return img, corners, ids_and_corners

def getPieceCenters(img, ids_and_corners):
	filtered_ids = []
	piece_centers = []
	for i in range(len(ids_and_corners[0])):
		id = ids_and_corners[0][i]
		corners = ids_and_corners[1][i]
		if 4 <= id and id <= 15:
			center = np.mean(corners, axis=0)
			img = putText(img, str(id), np.int32(center), FONT_HERSHEY_DUPLEX, 1, (0, 0, 255), 1)
			img = circle(img, np.int32(center), 1, (0, 0, 255), 5)
			filtered_ids.append(id)
			piece_centers.append(center)
		if id > 15:
			print(f"unexpected ID {id} at coordinates {corners}");
	return img, [filtered_ids, np.int32(piece_centers)]

def generateBoard(board_corners, piece_centers):
	board = np.zeros(board_dimensions, dtype = np.int8)
	ids = piece_centers[0]
	square_size = resolution / board_dimensions
	coordinates = np.int8(piece_centers[1] / square_size)

	for i in range(len(ids)):
		id = ids[i]
		coord = np.int8([coordinates[i][0] , board_dimensions[1] - 1 - coordinates[i][1]])
		if board[coord[0]][coord[1]] != 0:
			print(f"position {coord} has piece type {board[coord[0]][coord[1]]} and {id}!")
			board[coord[0]][coord[1]] *= 100
			board[coord[0]][coord[1]] += id
		else:
			board[coord[0]][coord[1]] = id
	return board

def printBoard(board):
	for i in range(board_dimensions[1] - 1, -1, -1):
		line = ""
		for j in range(board_dimensions[0]):
			value = board[j][i]
			if value == 0:
				if (i + j ) % 2 == 0:
					line += '□'
				else:
					line += '■'
			elif value == 4:
				line += '♟'
			elif value == 5:
				line += '♜'
			elif value == 6:
				line += '♞'
			elif value == 7:
				line += '♝'
			elif value == 8:
				line += '♚'
			elif value == 9:
				line += '♛'
			elif value == 10:
				line += '♙'
			elif value == 11:
				line += '♖'
			elif value == 12:
				line += '♘'
			elif value == 13:
				line += '♗'
			elif value == 14:
				line += '♔'
			elif value == 15:
				line += '♕'
		print(line)

#if True:
while True:
	img, ids_and_corners = getArucoCorners()
	if len(ids_and_corners) > 0:
		img, board_corners, ids_and_corners = getBoardCorners(img, ids_and_corners)
#		print(f"board corners: {board_corners}")
		now = datetime.now().strftime("%Y.%m.%d-%H:%M:%S")
		img, piece_centers = getPieceCenters(img, ids_and_corners)
		imwrite(f"arucos/aruco{now}.png", img)
		if len(piece_centers[0]) != 32:
			print(f"{len(piece_centers[0])} found :(")
#		print(f"piece centers: {piece_centers}")
		board = generateBoard(board_corners, piece_centers)
		printBoard(board)
	else:
		print(":(")
		imwrite(f"noaruco.png", img)
	sleep(5)

cap.release()
destroyAllWindows()
