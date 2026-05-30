import os
import shutil
import random
import zipfile
import cv2
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon

# ==========================================
# CONFIGURATION
# ==========================================
class Config:
    # --- Paths ---
    # Update these to where your source images are located. 
    # If using Colab, you can set these back to '/content/drive/MyDrive/...'
    NATIVE_A_PATH = 'native_a_clean.png'
    NATIVE_B_PATH = 'native_b_clean.png'
    INVASIVE_PATH = 'invasive_clean.png'
    
    BASE_DIR = 'crab_obb_dataset'
    OUT_IMAGES = os.path.join(BASE_DIR, "images")
    OUT_LABELS = os.path.join(BASE_DIR, "labels")
    
    # --- Generation Parameters ---
    N_IMAGES = 1000
    CANVAS_SIZE = 1024
    
    # Format: {'species_name': (min_crabs, max_crabs)}
    NUM_CRABS_PER_SPECIES = {
        'native_a': (0, 5),
        'native_b': (0, 5),
        'invasive': (0, 5) 
    }

# ==========================================
# SETUP & UTILITIES
# ==========================================
def setup_directories():
    """Removes the old dataset directory if it exists and creates fresh ones."""
    if os.path.exists(Config.BASE_DIR):
        shutil.rmtree(Config.BASE_DIR)
        print(f"Removed existing directory: {Config.BASE_DIR}")

    os.makedirs(Config.OUT_IMAGES, exist_ok=True)
    os.makedirs(Config.OUT_LABELS, exist_ok=True)
    print(f"Created new directories: {Config.OUT_IMAGES} and {Config.OUT_LABELS}")

def load_rgba_image(path):
    """Loads an image and ensures it is in RGBA format."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Source image not found at: {path}. Please update Config paths.")
        
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    assert img is not None, f"Error: Could not load image from {path}"

    if img.shape[2] == 3:  # BGR
        img_bgra = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    elif img.shape[2] == 4:  # BGRA
        img_bgra = img
    else:
        raise ValueError(f"Unsupported number of channels: {img.shape[2]} for image {path}")

    return cv2.cvtColor(img_bgra, cv2.COLOR_BGRA2RGBA)

# ==========================================
# GEOMETRY & PLACEMENT
# ==========================================
def transform_crab(img, scale, angle_deg):
    """Scales and rotates the crab image, returning the transformed image and its OBB."""
    img = cv2.resize(img, None, fx=scale, fy=scale)
    h, w = img.shape[:2]
    center = (w // 2, h // 2)

    M = cv2.getRotationMatrix2D(center, angle_deg, 1.0)
    cos_val, sin_val = abs(M[0, 0]), abs(M[0, 1])

    new_w = int(h * sin_val + w * cos_val)
    new_h = int(h * cos_val + w * sin_val)

    M[0, 2] += new_w / 2 - center[0]
    M[1, 2] += new_h / 2 - center[1]

    rotated = cv2.warpAffine(
        img, M, (new_w, new_h),
        flags=cv2.INTER_LINEAR,
        borderValue=(0, 0, 0, 0)
    )

    obb = np.array([
        [0, 0],
        [new_w, 0],
        [new_w, new_h],
        [0, new_h]
    ], dtype=np.float32)

    return rotated, obb

def paste_rgba(bg, fg, x, y):
    """Blends the foreground RGBA image onto the BGR background at coordinates (x,y)."""
    h, w = fg.shape[:2]
    alpha = fg[:, :, 3] / 255.0
    fg_bgra = cv2.cvtColor(fg, cv2.COLOR_RGBA2BGRA)

    for c in range(3):
        bg_slice = bg[y:y+h, x:x+w, c]
        fg_slice = fg_bgra[:, :, c]
        alpha_slice = alpha

        min_h = min(bg_slice.shape[0], fg_slice.shape[0])
        min_w = min(bg_slice.shape[1], fg_slice.shape[1])

        bg[y:y+min_h, x:x+min_w, c] = (
            alpha_slice[:min_h, :min_w] * fg_slice[:min_h, :min_w] +
            (1 - alpha_slice[:min_h, :min_w]) * bg_slice[:min_h, :min_w]
        )

# ==========================================
# AUGMENTATIONS
# ==========================================
def apply_augmentations(canvas):
    """Randomly applies brightness, contrast, and blur to the generated canvas."""
    img_float = canvas.astype(np.float32)

    # 30% chance for brightness/contrast adjustment
    if random.random() < 0.3:
        brightness = random.uniform(-60, 0)
        contrast = random.uniform(0.8, 1)
        img_float = cv2.convertScaleAbs(img_float, alpha=contrast, beta=brightness).astype(np.float32)

    # 30% chance for Gaussian blur
    if random.random() < 0.3:
        kernel_size = random.choice([3, 5, 7, 9, 11, 13, 15, 17])
        img_float = cv2.GaussianBlur(img_float, (kernel_size, kernel_size), 0)

    return img_float.astype(np.uint8)

def save_yolo_obb(path, obbs, img_size):
    """Saves Oriented Bounding Boxes in YOLO format."""
    with open(path, "w") as f:
        for obb in obbs:
            flat_obb = obb.flatten()
            coords = (flat_obb / img_size)
            f.write("0 " + " ".join(f"{c:.6f}" for c in coords) + "\n")

# ==========================================
# MAIN GENERATION LOGIC
# ==========================================
def generate_dataset():
    """Main loop to generate the synthetic dataset."""
    setup_directories()

    crabs_dict = {
        "native_a": load_rgba_image(Config.NATIVE_A_PATH),
        "native_b": load_rgba_image(Config.NATIVE_B_PATH),
        "invasive": load_rgba_image(Config.INVASIVE_PATH)
    }

    print("Starting generation...")
    for idx in range(Config.N_IMAGES):
        canvas = np.ones((Config.CANVAS_SIZE, Config.CANVAS_SIZE, 3), dtype=np.uint8) * 255
        placed_obbs = []
        labels = []

        # Determine how many crabs of each species to place in this image
        crabs_to_place = []
        for species, (min_c, max_c) in Config.NUM_CRABS_PER_SPECIES.items():
            crabs_to_place.extend([species] * random.randint(min_c, max_c))
        random.shuffle(crabs_to_place)

        for species in crabs_to_place:
            img = crabs_dict[species]
            scale = random.uniform(0.2, 0.5)
            angle = random.uniform(0, 359)

            crab_img, base_obb = transform_crab(img, scale, angle)
            h, w = crab_img.shape[:2]

            # Attempt to place the crab without overlapping others (up to 50 tries)
            for _ in range(50):
                x = random.randint(-w // 2, Config.CANVAS_SIZE - w // 2)
                y = random.randint(-h // 2, Config.CANVAS_SIZE - h // 2)
                
                obb_world = base_obb + np.array([x, y])
                current_crab_poly = Polygon(obb_world)

                # Collision check
                collision = any(current_crab_poly.intersects(Polygon(p)) for p in placed_obbs)

                if not collision:
                    # Calculate safe pasting boundaries
                    p_x_start, p_y_start = max(0, x), max(0, y)
                    p_x_end, p_y_end = min(Config.CANVAS_SIZE, x + w), min(Config.CANVAS_SIZE, y + h)

                    c_x_start, c_y_start = max(0, -x), max(0, -y)
                    c_x_end, c_y_end = c_x_start + (p_x_end - p_x_start), c_y_start + (p_y_end - p_y_start)

                    if c_x_end > c_x_start and c_y_end > c_y_start:
                        cropped_crab = crab_img[c_y_start:c_y_end, c_x_start:c_x_end]
                        if cropped_crab.size > 0:
                            paste_rgba(canvas[p_y_start:p_y_end, p_x_start:p_x_end], cropped_crab, 0, 0)
                            placed_obbs.append(obb_world)
                            
                            # Only invasive crabs are labeled for bounding boxes
                            if species == "invasive":
                                labels.append(obb_world)
                            break # Placement successful, move to next crab

        # Finalize image
        canvas = apply_augmentations(canvas)
        img_id = f"{idx:05d}"
        cv2.imwrite(os.path.join(Config.OUT_IMAGES, f"{img_id}.jpg"), canvas)
        save_yolo_obb(os.path.join(Config.OUT_LABELS, f"{img_id}.txt"), labels, Config.CANVAS_SIZE)

        if (idx + 1) % 100 == 0:
            print(f"Generated {idx + 1}/{Config.N_IMAGES} images...")

    print("Dataset generation complete!")

# ==========================================
# POST-PROCESSING
# ==========================================
def zip_dataset(output_filename='crab_obb_dataset.zip'):
    """Zips the generated dataset for easy downloading."""
    print(f"Zipping dataset to {output_filename}...")
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for folder in [Config.OUT_IMAGES, Config.OUT_LABELS]:
            for root, _, files in os.walk(folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, Config.BASE_DIR)
                    zipf.write(file_path, arcname)
    print("Zipping complete.")

def visualize_samples(num_samples=5):
    """Visualizes a few generated images with their bounding boxes."""
    image_files = sorted([f for f in os.listdir(Config.OUT_IMAGES) if f.endswith('.jpg')])
    
    if not image_files:
        print("No images to visualize.")
        return

    print(f"Visualizing {num_samples} samples...")
    for img_filename in image_files[:num_samples]:
        img_id = os.path.splitext(img_filename)[0]
        img_path = os.path.join(Config.OUT_IMAGES, img_filename)
        label_path = os.path.join(Config.OUT_LABELS, f"{img_id}.txt")

        img = cv2.imread(img_path)
        if img is None: continue

        if os.path.exists(label_path):
            with open(label_path, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    coords = np.array([float(p) for p in parts[1:]])
                    obb_pixel = (coords * Config.CANVAS_SIZE).reshape(-1, 2).astype(np.int32)
                    cv2.polylines(img, [obb_pixel], isClosed=True, color=(0, 255, 0), thickness=2)

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        plt.figure(figsize=(8, 8))
        plt.imshow(img_rgb)
        plt.title(f"Image {img_id}.jpg")
        plt.axis('off')
        plt.show()

# ==========================================
# ENTRY POINT
# ==========================================
if __name__ == "__main__":
    # 1. Generate the data
    generate_dataset()
    
    # 2. Package it up
    zip_dataset()
    
    # 3. Verify it visually (safely limited to 5 images)
    visualize_samples(num_samples=5)