import cv2
import time
import numpy as np

# Adjust imports carefully
from HandTrackingModule import HandDetector
from VolumeHandControl import VolumeController
from models.session import Session
from models.volume_event import VolumeEvent
from dao.mongodb_dao import MongoDBDAO

def main():
    # 1. Initialize Camera
    wCam, hCam = 640, 480
    cap = cv2.VideoCapture(0)
    cap.set(3, wCam)
    cap.set(4, hCam)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    # 2. Initialize Core Modules
    detector = HandDetector(detection_con=0.7, max_hands=1)
    volume_ctrl = VolumeController()
    db = MongoDBDAO()
    
    # 3. Create a new Session and save to MongoDB
    session = Session()
    db.insert_session(session.to_dict())

    # State variables
    volBar = 400
    volPer = 0
    area = 0
    pTime = 0
    
    print("Starting volume control. Press 'q' to exit.")

    try:
        while True:
            success, img = cap.read()
            if not success:
               continue

            # Detect Hands
            img = detector.find_hands(img)
            lmList, bbox = detector.find_position(img, draw=True)

            if len(lmList) != 0:
                # Find dimensions of bounding box for normalization
                area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) // 100
                
                if 250 < area < 1000:
                    # Find Distance between index and Thumb
                    length, img, lineInfo = detector.find_distance(4, 8, img)
                    
                    # Compute expected volume mapping without applying yet
                    min_dist = 50
                    max_dist = 200 # Adjusted max distance for typical span
                    volBar = np.interp(length, [min_dist, max_dist], [400, 150])
                    volPer = np.interp(length, [min_dist, max_dist], [0, 100])

                    # Check fingers up to detect confirmation gesture (Pinky down)
                    fingers = detector.fingers_up()
                    
                    # 4. If pinky is down (intencional change)
                    if fingers[4] == 0:
                        # Grab previous volume before setting
                        old_vol = volume_ctrl.get_current_volume()
                        
                        # Apply volume
                        _, _ = volume_ctrl.set_volume_from_distance(length, min_dist, max_dist)
                        
                        # Visual cue: feedback that volume was set (green circle)
                        cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)

                        # Create event in background
                        new_vol = volume_ctrl.get_current_volume()
                        if abs(old_vol - new_vol) > 1.0: # Only record meaningful changes > 1%
                            event = VolumeEvent(session.session_id, old_vol, new_vol, float(length))
                            db.insert_volume_event(event.to_dict())


            # 5. Drawings (UI overlays)
            cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)
            cv2.rectangle(img, (50, int(volBar)), (85, 400), (255, 0, 0), cv2.FILLED)
            cv2.putText(img, f'{int(volPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX,
                        1, (255, 0, 0), 3)

            # Frame rate calculation
            cTime = time.time()
            fps = 1 / (cTime - pTime) if pTime > 0 else 0
            pTime = cTime
            
            # FPS and Connection Status text
            cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX,
                        1, (255, 0, 0), 3)
            
            db_status = "OK" if db.connected else "--"
            color_db = (0, 255, 0) if db.connected else (0, 0, 255)
            cv2.putText(img, f'DB: {db_status}', (40, 90), cv2.FONT_HERSHEY_COMPLEX,
                        1, color_db, 3)

            cv2.imshow("Hand Volume Control", img)

            # Wait for 'q' to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        # 6. Cleanup and update session end time
        print("Cleaning up...")
        session.end_session()
        db.update_session(session.session_id, {"end_time": session.end_time, "duration": session.get_duration()})
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
