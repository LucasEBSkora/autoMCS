from picamera import PiCamera
from numpy import uint8, int32, empty

class Camera:
	def __init__(self, resolution):
		self.camera = PiCamera(resolution = resolution, framerate = 1)
		# the PiCamera class might round the resolution up or down to a supported size
		self.resolution = int32(self.camera.resolution)

	def __del__(self):
		# releases camera resource
		self.camera.close()

	def capture(self):
		img = empty((self.resolution[0]*self.resolution[1]*3,), dtype=uint8)
		self.camera.capture(img, 'bgr')
		return img.reshape((self.resolution[1], self.resolution[0], 3))

	def getRealResolution(self):
		return self.resolution
