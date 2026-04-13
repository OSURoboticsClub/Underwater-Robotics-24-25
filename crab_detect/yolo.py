import cv2
import time
from ultralytics import YOLO
import pathlib
import platform
import os

if platform.system() == 'Windows':
    pathlib.PosixPath = pathlib.WindowsPath

model_path = 'best_lightblur.pt'
model_trained = YOLO(model_path)
model_trained.to('cpu')

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

print("==========================================")
print("1-Second Delay Feed started!")
print("Press 'q' to QUIT.")
print("Press 'c' to capture a image.")
print("==========================================")
capture_count = 0
last_prediction_time = 0
crab_count = 0
current_display_frame = None
while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame.")
        break

    current_time = time.time()

    if current_time - last_prediction_time >= 0.2:
        
        # Run prediction
        results = model_trained.predict(source=frame, conf=0.3, iou=0.45, verbose=False)
        
        current_clock_time = time.strftime('%X')
        print(f"\n--- Detections at [{current_clock_time}] ---")
        
        # ==========================================
        # REVISED RESULT PARSING (From your image)
        # ==========================================
        for r in results:
            # CHANGED: Use r.obb instead of r.boxes for Oriented Bounding Box models
            boxes = r.obb 
            classes = r.names 
            
            # SAFETY CHECK: Only try to count/loop if boxes actually exist
            if boxes is not None:
                print(f"Total objects found: {len(boxes)}")
                
                for box in boxes:
                    class_id = int(box.cls[0]) 
                    class_name = classes[class_id]
                    confidence = float(box.conf[0])
                    print(f"  - Found: {class_name} (Confidence: {confidence:.2f})")
            else:
                # If boxes is None, it means 0 objects were detected
                print("Total objects found: 0")
            # Loop through every individual box found in this frame
# ==========================================

            # Draw the bounding boxes on the image
            annotated_frame = results[0].plot()
            current_display_frame = annotated_frame
            crab_count = len(results[0].obb) if results[0].obb is not None else 0
            # Update the live window with the new boxed frame
            cv2.imshow("Live Prediction Feed", annotated_frame)

            # Reset the timer
            last_prediction_time = current_time

        # Wait for key press to quit
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("Quitting...")
            break
        # If 'c' is pressed...
        if key == ord('c'):
        # Make sure we actually have a processed frame ready to save
            if current_display_frame is not None:
                filename = f"detected_crab_{capture_count}_{crab_count}.jpg"

                filepath = os.path.join('result', filename)
                cv2.imwrite(filepath, current_display_frame)
                print(f"--> SNAPSHOT SAVED: {filename} (Recorded {crab_count} crabs)")
                capture_count += 1
            else:
                print("Wait a second for the first prediction to finish...")

cap.release()
cv2.destroyAllWindows()