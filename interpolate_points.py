from numpy import int32, int8, ravel, zeros, array, float32, mean, dot
from scipy.linalg import lu, norm

	# def interpolate_last_point(self, first, second, third):
	# 	return first + (third - second)

	# 	u = float32(second - first)
	# 	v = float32(third - second)

	# 	projection = u * dot(u, v) / dot(u, u)
	# 	normal = projection - v
	# 	vector = v - 2*projection
	# 	return int32(first + vector)
	# 	line_vector = second_line_point - first_line_point

	# 	print(line_vector)
	# 	project_vector = point_to_reflect - first_line_point
	# 	print(project_vector)
	# 	projection = line_vector * dot(line_vector, project_vector) / dot(line_vector, line_vector)
	# 	print(projection)
	# 	normal = project_vector - projection
	# 	print(normal)
	# 	print(point_to_reflect - 2*normal)

		# print(point_to_reflect)
		# print(first_line_point)
		# print(second_line_point)
		
		# line_vector = second_line_point - first_line_point

		# print(line_vector)
		# project_vector = point_to_reflect - first_line_point
		# print(project_vector)
		# projection = line_vector * dot(line_vector, project_vector) / dot(line_vector, line_vector)
		# print(projection)
		# normal = project_vector - projection
		# print(normal)
		# print(point_to_reflect - 2*normal)
		# return point_to_reflect - 2*normal
		# line_a = second_line_point - first_line_point
		# line_b = first_line_point

		# orthogonal_a = array([line_a[1], line_a[0]])
		# orthogonal_b = point_to_reflect

		# B = orthogonal_b - line_b

		# matrix = array([[line_a[0], orthogonal_a[0], B[0]], [line_a[1], orthogonal_a[1], B[1]]])
		# _, _, solved = lu(matrix)
		# r = solved[0][2]
		# return orthogonal_a*2*r+ orthogonal_b
		# a*r + b = c*q + d

		# A = [[a[0], c[0]], [a[1], c[1]]]
		# B = d - b
		# X = [[r], [q]]
		# a[0]*r + b[0] = c[0]*q + d[0]
		# a[1]*r + b[1] = c[1]*q + d[1]


	# def _attemptExtrapolateMissingCorners(self, corners_found, LL, LR, UR, UL):
	# 	if corners_found == 1:
	# 		return False, array([]) 
	# 	elif corners_found == 2:
	# 		return False, array([]) 
	# 	elif corners_found == 3:
	# 		print(LL)
	# 		if LL is None:
	# 			#LL = UL - (UR - LR)
	# 			LL = self.interpolate_last_point(LR, UR, UL)
	# 			print(LL)
	# 		elif LR is None:
	# 			LR = self.interpolate_last_point(UR, UL, LL)
	# 		elif UR is None:
	# 			UR = self.interpolate_last_point(UL, LL, LR)
	# 		else:
	# 			UL = self.interpolate_last_point(LL, LR, UR)

	# 	return True, array([LL, LR, UR, UL])