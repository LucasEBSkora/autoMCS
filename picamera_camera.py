from picamera import PiCamera
from numpy import uint8, int32, empty
from threading import Lock, Thread
from time import sleep
class Camera:
	def __init__(self, resolution):
		self.camera = PiCamera(resolution = resolution, framerate = 1)
		self.resolution = int32(self.camera.resolution)
		self.frame_size = self.resolution[0]*self.resolution[1]*3

		self.current_frame = None
		self.lock = Lock()
		self.thread = Thread(target=self.__capture)
		self.thread.daemon = True
		self.thread.start()
	def __del__(self):
		# releases camera resource
		self.camera.close()

	def capture(self):
		while self.current_frame is None:
			pass
		with self.lock:
			ret_frame = self.current_frame
		return ret_frame


	def __capture(self):
		while True:
			img = empty((self.frame_size,), dtype=uint8)
			self.camera.capture(img, 'bgr')
			with self.lock:
				self.current_frame = img.reshape((self.resolution[1], self.resolution[0], 3))
			sleep(0.2)


	def getRealResolution(self):
		# the PiCamera class might round the resolution up or down to a supported size
		return self.resolution
