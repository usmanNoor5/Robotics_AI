import numpy as np
import cv2
import sys
import time


ARUCO_DICT = {
	"DICT_4X4_50": cv2.aruco.DICT_4X4_50,
	"DICT_4X4_100": cv2.aruco.DICT_4X4_100,
	"DICT_4X4_250": cv2.aruco.DICT_4X4_250,
	"DICT_4X4_1000": cv2.aruco.DICT_4X4_1000,
	"DICT_5X5_50": cv2.aruco.DICT_5X5_50,
	"DICT_5X5_100": cv2.aruco.DICT_5X5_100,
	"DICT_5X5_250": cv2.aruco.DICT_5X5_250,
	"DICT_5X5_1000": cv2.aruco.DICT_5X5_1000,
	"DICT_6X6_50": cv2.aruco.DICT_6X6_50,
	"DICT_6X6_100": cv2.aruco.DICT_6X6_100,
	"DICT_6X6_250": cv2.aruco.DICT_6X6_250,
	"DICT_6X6_1000": cv2.aruco.DICT_6X6_1000,
	"DICT_7X7_50": cv2.aruco.DICT_7X7_50,
	"DICT_7X7_100": cv2.aruco.DICT_7X7_100,
	"DICT_7X7_250": cv2.aruco.DICT_7X7_250,
	"DICT_7X7_1000": cv2.aruco.DICT_7X7_1000,
	"DICT_ARUCO_ORIGINAL": cv2.aruco.DICT_ARUCO_ORIGINAL,
	"DICT_APRILTAG_16h5": cv2.aruco.DICT_APRILTAG_16h5,
	"DICT_APRILTAG_25h9": cv2.aruco.DICT_APRILTAG_25h9,
	"DICT_APRILTAG_36h10": cv2.aruco.DICT_APRILTAG_36h10,
	"DICT_APRILTAG_36h11": cv2.aruco.DICT_APRILTAG_36h11
}

# Physical size of the printed ArUco marker in meters.
# Measure your actual printed marker and update this value — depth accuracy depends on it.
MARKER_SIZE = 0.05  # 5 cm


def rvec_to_euler(rvec):
	"""Convert rotation vector to Euler angles (roll, pitch, yaw) in degrees."""
	R, _ = cv2.Rodrigues(rvec)
	pitch = np.arctan2(-R[2][0], np.sqrt(R[2][1]**2 + R[2][2]**2))
	yaw   = np.arctan2(R[1][0], R[0][0])
	roll  = np.arctan2(R[2][1], R[2][2])
	return np.degrees(roll), np.degrees(pitch), np.degrees(yaw)


def pose_estimation(frame, aruco_dict_type, matrix_coefficients, distortion_coefficients):
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	aruco_dict = cv2.aruco.Dictionary_get(aruco_dict_type)
	parameters = cv2.aruco.DetectorParameters_create()

	corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

	if len(corners) > 0:
		cv2.aruco.drawDetectedMarkers(frame, corners)

		for i in range(len(ids)):
			rvec, tvec, _ = cv2.aruco.estimatePoseSingleMarkers(
				corners[i], MARKER_SIZE, matrix_coefficients, distortion_coefficients)

			# Draw 3D axis on the marker
			cv2.drawFrameAxes(frame, matrix_coefficients, distortion_coefficients, rvec, tvec, MARKER_SIZE * 0.5)

			# Extract position (in meters)
			x   = tvec[0][0][0]
			y   = tvec[0][0][1]
			depth = tvec[0][0][2]  # z = depth from camera

			# Convert rotation vector to Euler angles
			roll, pitch, yaw = rvec_to_euler(rvec[0])

			marker_id = ids[i][0]
			print(f"[ID {marker_id}] Depth: {depth:.3f}m  X: {x:.3f}m  Y: {y:.3f}m  "
			      f"Roll: {roll:.1f}°  Pitch: {pitch:.1f}°  Yaw: {yaw:.1f}°")

			# Overlay pose info on the frame
			# Get the top-left corner of this marker for text placement
			top_left = tuple(corners[i][0][0].astype(int))
			text_x = top_left[0]
			text_y = top_left[1] - 60

			cv2.putText(frame, f"ID:{marker_id}  Depth:{depth:.3f}m",
				(text_x, text_y),      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
			# cv2.putText(frame, f"X:{x:.3f}m  Y:{y:.3f}m",
			# 	(text_x, text_y + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
			# cv2.putText(frame, f"R:{roll:.1f}  P:{pitch:.1f}  Yaw:{yaw:.1f} deg",
			# 	(text_x, text_y + 36), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

	return frame


aruco_type = "DICT_5X5_250"

intrinsic_camera = np.array(((933.15867, 0, 657.59), (0, 933.1586, 400.36993), (0, 0, 1)))
distortion = np.array((-0.43948, 0.18514, 0, 0))

cap = cv2.VideoCapture(2, cv2.CAP_V4L2)  # HP True Vision FHD built-in
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

while cap.isOpened():
	ret, img = cap.read()

	if not ret:
		print("Failed to grab frame")
		break

	output = pose_estimation(img, ARUCO_DICT[aruco_type], intrinsic_camera, distortion)

	cv2.imshow('Estimated Pose', output)

	key = cv2.waitKey(1) & 0xFF
	if key == ord('q'):
		break

cap.release()
cv2.destroyAllWindows()
