from cv2 import VideoCapture, CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT, CAP_PROP_BUFFERSIZE, CAP_PROP_FPS
from numpy import int32

class Camera:
	def __init__(self, resolution):
		self.resolution = int32(resolution)
		self.cap = VideoCapture(0)

		ret = self.cap.set(CAP_PROP_FRAME_WIDTH, resolution[0])

		if (ret != True):
			print("failed to set frame width")
			exit(-1)

		ret = self.cap.set(CAP_PROP_FRAME_HEIGHT,resolution[1])

		if (ret != True):
			print("failed to set frame height")
			exit(-1)

		# default buffer size is 10, meaning we get "very old" images instead of the latest
		ret = self.cap.set(CAP_PROP_BUFFERSIZE, 1)

		if (ret != True):
			print("failed to set buffer size")
			exit(-1)

		ret = self.cap.set(CAP_PROP_FPS, 1)

		if (ret != True):
			print("failed to set FPS")
			exit(-1)

	def __del__(self):
		# releases camera resource
		self.cap.release()

	def capture(self):
		ret, img = self.cap.read()
		if ret != True:
			print("failed to read image!")
			exit(-1)
		return img

	def getRealResolution(self):
		return self.resolution
