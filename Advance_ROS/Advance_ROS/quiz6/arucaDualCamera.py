import numpy as np
import cv2
import threading


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

ARUCO_TYPE = "DICT_5X5_250"
MARKER_SIZE = 0.05  # meters — measure your printed marker and update this

# ---------------------------------------------------------------------------
# Per-camera intrinsics — each camera has a different focal length and lens,
# so they MUST have separate calibration values for accurate depth.
#
# To calibrate: print a checkerboard, run OpenCV camera calibration on each
# camera separately, and paste the resulting matrix + distortion here.
#
# Until you calibrate the Brio 100, its depth will differ from the HP camera.
# ---------------------------------------------------------------------------

# HP True Vision FHD (index 0)
HP_INTRINSIC   = np.array(((933.15867, 0, 657.59), (0, 933.1586, 400.36993), (0, 0, 1)))
HP_DISTORTION  = np.array((-0.43948, 0.18514, 0, 0))

# Logitech Brio 100 (index 2) — replace with your own calibration values
BRIO_INTRINSIC  = np.array(((933.15867, 0, 657.59), (0, 933.1586, 400.36993), (0, 0, 1)))
BRIO_DISTORTION = np.array((-0.43948, 0.18514, 0, 0))

# Fixed display size — both windows will be exactly this size
DISPLAY_WIDTH  = 960
DISPLAY_HEIGHT = 540


class CameraThread:
	"""Captures frames from a camera in a background thread so neither camera blocks the other."""

	def __init__(self, index, name, width=1920, height=1080):
		self.name = name
		self.cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
		self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
		self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
		self._frame = None
		self._ret = False
		self._lock = threading.Lock()
		self._running = True
		self._thread = threading.Thread(target=self._capture, daemon=True)
		self._thread.start()

	def _capture(self):
		while self._running:
			ret, frame = self.cap.read()
			with self._lock:
				self._ret = ret
				self._frame = frame

	def read(self):
		with self._lock:
			if self._frame is None:
				return False, None
			return self._ret, self._frame.copy()

	def is_opened(self):
		return self.cap.isOpened()

	def release(self):
		self._running = False
		self._thread.join(timeout=2)
		self.cap.release()


def rvec_to_euler(rvec):
	R, _ = cv2.Rodrigues(rvec)
	pitch = np.arctan2(-R[2][0], np.sqrt(R[2][1]**2 + R[2][2]**2))
	yaw   = np.arctan2(R[1][0], R[0][0])
	roll  = np.arctan2(R[2][1], R[2][2])
	return np.degrees(roll), np.degrees(pitch), np.degrees(yaw)


def pose_estimation(frame, cam_name, intrinsic, distortion):
	"""Detect ArUco markers and overlay depth + pose on the frame."""
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	aruco_dict = cv2.aruco.Dictionary_get(ARUCO_DICT[ARUCO_TYPE])
	parameters = cv2.aruco.DetectorParameters_create()

	corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

	if len(corners) > 0:
		cv2.aruco.drawDetectedMarkers(frame, corners)

		for i in range(len(ids)):
			rvec, tvec, _ = cv2.aruco.estimatePoseSingleMarkers(
				corners[i], MARKER_SIZE, intrinsic, distortion)

			cv2.drawFrameAxes(frame, intrinsic, distortion, rvec, tvec, MARKER_SIZE * 0.5)

			x     = tvec[0][0][0]
			y     = tvec[0][0][1]
			depth = tvec[0][0][2]
			roll, pitch, yaw = rvec_to_euler(rvec[0])
			marker_id = ids[i][0]

			print(f"[{cam_name}] ID:{marker_id}  Depth:{depth:.3f}m  "
			      f"X:{x:.3f}m  Y:{y:.3f}m  R:{roll:.1f}° P:{pitch:.1f}° Yaw:{yaw:.1f}°")

			top_left = tuple(corners[i][0][0].astype(int))
			tx, ty = top_left[0], top_left[1] - 60

			cv2.putText(frame, f"[{cam_name}] ID:{marker_id}  Depth:{depth:.3f}m",
				(tx, ty),      cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
			# cv2.putText(frame, f"X:{x:.3f}m  Y:{y:.3f}m",
			# 	(tx, ty + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
			# cv2.putText(frame, f"R:{roll:.1f}  P:{pitch:.1f}  Yaw:{yaw:.1f} deg",
			# 	(tx, ty + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 255), 2)

	return frame


def resize_for_display(frame):
	return cv2.resize(frame, (DISPLAY_WIDTH, DISPLAY_HEIGHT), interpolation=cv2.INTER_LINEAR)


# Open both cameras in background threads
cam_hp   = CameraThread(index=0, name="HP Built-in")
cam_brio = CameraThread(index=2, name="Brio 100")

print("Dual camera ArUco detection started. Press 'q' to quit.")

while True:
	ret0, frame0 = cam_hp.read()
	ret2, frame2 = cam_brio.read()

	if ret0 and frame0 is not None:
		out0 = pose_estimation(frame0, "HP", HP_INTRINSIC, HP_DISTORTION)
		cv2.imshow("HP Built-in (index 0)", resize_for_display(out0))

	if ret2 and frame2 is not None:
		out2 = pose_estimation(frame2, "Brio", BRIO_INTRINSIC, BRIO_DISTORTION)
		cv2.imshow("Brio 100 (index 2)", resize_for_display(out2))

	if cv2.waitKey(1) & 0xFF == ord('q'):
		break

cam_hp.release()
cam_brio.release()
cv2.destroyAllWindows()
