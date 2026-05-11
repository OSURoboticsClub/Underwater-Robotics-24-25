import cv2
import time
from ultralytics import YOLO
import pathlib
import platform
import os
import sys
import glob

if platform.system() == 'Windows':
    pathlib.PosixPath = pathlib.WindowsPath

crab_dir = pathlib.Path(__file__).resolve().parent

model_path = os.path.join(crab_dir,'best_lightblur.pt')
model_trained = YOLO(model_path)
model_trained.to('cpu')

inputs = glob.glob(os.path.join(crab_dir, 'inputs', '*.jpeg'))

for path in inputs:
    crab_count = 0
    frame = cv2.imread(path)
    if len(frame) == 0:
        print("Failed to open provided image")
        exit()

    # Run prediction
    results = model_trained.predict(source=frame, conf=0.3, iou=0.45, verbose=False)


    # ==========================================
    # REVISED RESULT PARSING (From your image)
    # ==========================================
    font = cv2.FONT_HERSHEY_SIMPLEX
    height = 12
    font_size = cv2.getFontScaleFromHeight(font, height,2)
    pos = (5,5+height)

    for r in results:
        # CHANGED: Use r.obb instead of r.boxes for Oriented Bounding Box models
        boxes = r.obb 
        classes = r.names 
        
        # SAFETY CHECK: Only try to count/loop if boxes actually exist
        if boxes is not None:
            for box in boxes:
                class_id = int(box.cls[0]) 
                class_name = classes[class_id]
                confidence = float(box.conf[0])
        # Loop through every individual box found in this frame
    # ==========================================

        # Draw the bounding boxes on the image
        crab_count = len(results[0].obb) if results[0].obb is not None else 0
        txt = f'Invasive Crabs Found: {crab_count}'
        size = cv2.getTextSize(txt, font, font_size, 2)
        annotated_frame = results[0].plot(labels=False, conf=False)
        annotated_frame = cv2.rectangle(annotated_frame, (pos[0]-2,pos[1]+3), (pos[0]+size[0][0], pos[1]-size[0][1]-1), (0,0,0), cv2.FILLED)
        annotated_frame = cv2.putText(annotated_frame, txt, pos, font, font_size, (255,255,255), 2)
        current_display_frame = annotated_frame
        # Update the live window with the new boxed frame

    filename = pathlib.Path(path).stem + f'_processed'
    filepath = os.path.join(crab_dir, 'result', filename + '.jpeg')
    cv2.imwrite(filepath, current_display_frame)
    print(f"--> SNAPSHOT SAVED: {filename} (Recorded {crab_count} crabs)")
