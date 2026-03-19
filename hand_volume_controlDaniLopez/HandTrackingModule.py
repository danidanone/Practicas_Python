import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import math

class HandDetector:
    def __init__(self, model_path='hand_landmarker.task', max_hands=2, detection_con=0.5):
        self.model_path = model_path
        self.max_hands = max_hands
        self.detection_con = detection_con
        
        # Configure Hand Landmarker
        base_options = python.BaseOptions(model_asset_path=self.model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=self.max_hands,
            min_hand_detection_confidence=self.detection_con,
            running_mode=vision.RunningMode.IMAGE
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        self.results = None
        self.lm_list = []
        self.tip_ids = [4, 8, 12, 16, 20]

    def find_hands(self, img, draw=True):
        # Convert to Mediapipe Image format
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
        
        # Process image
        self.results = self.detector.detect(mp_image)
        
        if draw and self.results.hand_landmarks:
            for hand_landmarks in self.results.hand_landmarks:
                h, w, _ = img.shape
                # Draw landmarks manually since drawing_utils might be missing
                for lm in hand_landmarks:
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
                
                # Draw connections (partial list for common hand connections)
                connections = [
                    (0, 1), (1, 2), (2, 3), (3, 4), # Thumb
                    (0, 5), (5, 6), (6, 7), (7, 8), # Index
                    (5, 9), (9, 10), (10, 11), (11, 12), # Middle
                    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
                    (13, 17), (17, 18), (18, 19), (19, 20), (0, 17) # Pinky & Palm
                ]
                for start, end in connections:
                    p1 = (int(hand_landmarks[start].x * w), int(hand_landmarks[start].y * h))
                    p2 = (int(hand_landmarks[end].x * w), int(hand_landmarks[end].y * h))
                    cv2.line(img, p1, p2, (0, 255, 0), 2)
                    
        return img

    def find_position(self, img, hand_no=0, draw=True):
        self.lm_list = []
        bbox = []
        if self.results and self.results.hand_landmarks:
            if len(self.results.hand_landmarks) > hand_no:
                my_hand = self.results.hand_landmarks[hand_no]
                x_list = []
                y_list = []
                h, w, c = img.shape
                
                for id, lm in enumerate(my_hand):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    x_list.append(cx)
                    y_list.append(cy)
                    self.lm_list.append([id, cx, cy])
                    
                xmin, xmax = min(x_list), max(x_list)
                ymin, ymax = min(y_list), max(y_list)
                bbox = xmin, ymin, xmax, ymax
                
                if draw:
                    cv2.rectangle(img, (xmin - 20, ymin - 20), (xmax + 20, ymax + 20), (0, 255, 0), 2)
                
        return self.lm_list, bbox

    def fingers_up(self):
        fingers = []
        if not self.lm_list:
            return [0, 0, 0, 0, 0]
            
        # Thumb (Horizontal distance check adjusted for new model behavior if needed)
        # Using the same logic as before for simplicity, might need refinement
        if self.lm_list[self.tip_ids[0]][1] > self.lm_list[self.tip_ids[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)
            
        # 4 Fingers (Vertical position check)
        for id in range(1, 5):
            if self.lm_list[self.tip_ids[id]][2] < self.lm_list[self.tip_ids[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
                
        return fingers

    def find_distance(self, p1, p2, img, draw=True, r=15, t=3):
        x1, y1 = self.lm_list[p1][1:]
        x2, y2 = self.lm_list[p2][1:]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        
        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), t)
            cv2.circle(img, (x1, y1), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), r, (0, 0, 255), cv2.FILLED)
            
        length = math.hypot(x2 - x1, y2 - y1)
        return length, img, [x1, y1, x2, y2, cx, cy]
