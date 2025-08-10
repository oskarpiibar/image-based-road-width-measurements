import os
import cv2
import numpy as np
from scipy.ndimage import gaussian_filter1d


def pipeline(img, template_folder, threshold=170):
    img = np.copy(img)

    # Car mask, bounding box, center
    car_mask, car_bbox, car_center = None, None, None
    if template_folder:
        car_mask, car_bbox, car_center = template_matching(img, template_folder)

    # Convert to HSV for color filtering
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)

    # Green mask (grass)
    lower_green = np.array([35, 40, 40])
    upper_green = np.array([90, 255, 255])
    green_mask = cv2.inRange(hsv, lower_green, upper_green)

    # Yellow/brown mask (gravel/sand)
    lower_yellow = np.array([15, 40, 40])
    upper_yellow = np.array([35, 255, 255])
    yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

    # Exclude those regions
    exclude_mask = cv2.bitwise_or(green_mask, yellow_mask)
    road_mask = cv2.bitwise_not(exclude_mask)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # Apply simple threshold
    _, binary_all = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)

    # Apply the road-only mask
    binary = cv2.bitwise_and(binary_all, binary_all, mask=road_mask)

    # Convert to binary (0 and 1 for further use)
    combined_binary = (binary // 255).astype(np.uint8)

    # Apply car mask
    if car_mask is not None:
        combined_binary = combined_binary * car_mask

    # Light denoising
    kernel = np.ones((3, 3), np.uint8)
    combined_binary = cv2.morphologyEx(combined_binary, cv2.MORPH_OPEN, kernel)

    return combined_binary, car_bbox, car_center


def template_matching(img, template_folder, alpha=0.9, orb_weight=0.2):
    # Apply CLAHE to input image
    gray_img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(2.0, (8, 8))
    gray_img = clahe.apply(gray_img)
    edge_img = cv2.Canny(gray_img, 50, 150)

    best_score = -1
    best_bbox = None
    best_center = None
    car_mask = np.ones_like(gray_img, dtype=np.uint8)

    orb = cv2.ORB_create(nfeatures=500)

    for filename in os.listdir(template_folder):
        if not filename.lower().endswith(".png"):
            continue
        template_path = os.path.join(template_folder, filename)
        template_color = cv2.imread(template_path)
        if template_color is None:
            continue

        template_gray = cv2.cvtColor(template_color, cv2.COLOR_BGR2GRAY)
        template_gray = clahe.apply(template_gray)
        template_edge = cv2.Canny(template_gray, 50, 150)

        for scale in [0.9, 1.0, 1.1]:
            t_gray = cv2.resize(template_gray, None, fx=scale, fy=scale)
            t_edge = cv2.resize(template_edge, None, fx=scale, fy=scale)

            for angle in [-15, 0, 15]:
                center = (t_gray.shape[1] // 2, t_gray.shape[0] // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                r_gray = cv2.warpAffine(t_gray, M, (t_gray.shape[1], t_gray.shape[0]))
                r_edge = cv2.warpAffine(t_edge, M, (t_edge.shape[1], t_edge.shape[0]))

                # Template matching scores
                result_color = cv2.matchTemplate(gray_img, r_gray, cv2.TM_CCOEFF_NORMED)
                _, color_score, _, color_loc = cv2.minMaxLoc(result_color)

                result_edge = cv2.matchTemplate(edge_img, r_edge, cv2.TM_CCOEFF_NORMED)
                _, edge_score, _, edge_loc = cv2.minMaxLoc(result_edge)

                h, w = r_gray.shape
                x1, y1 = color_loc
                x2, y2 = x1 + w, y1 + h
                patch = gray_img[y1:y2, x1:x2]

                orb_score = 0

                if patch.shape == r_gray.shape:
                    kp1, des1 = orb.detectAndCompute(r_gray, None)
                    kp2, des2 = orb.detectAndCompute(patch, None)
                    if des1 is not None and des2 is not None:
                        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                        matches = bf.match(des1, des2)
                        match_count = len(matches)
                        orb_score = min(1.0, np.log1p(match_count) / np.log1p(150))

                # Final score combining all components
                combined_score = (
                        alpha * color_score +
                        (1 - alpha) * edge_score +
                        orb_weight * orb_score
                )

                if combined_score > best_score:
                    best_score = combined_score
                    best_bbox = (x1, y1, x2, y2)
                    best_center = (x1 + w // 2, y1 + h * 5 // 8)
                    car_mask = np.ones_like(gray_img, dtype=np.uint8)
                    car_mask[y1:y2, x1:x2] = 0

    return car_mask, best_bbox, best_center


def get_hist(img, y_range, band_half_height=5):
    y1, y2 = y_range
    center_y = (y1 + y2) // 2
    band_y1 = max(0, center_y - band_half_height)
    band_y2 = min(img.shape[0], center_y + band_half_height)

    hist = np.sum(img[band_y1:band_y2, :].astype(np.uint8), axis=0)
    smoothed = gaussian_filter1d(hist, sigma=5)

    return smoothed


def mark_edges_of_flat_region(binary_img, car_bbox, hist, threshold, y_range, min_road_width):
    vis_img = cv2.cvtColor((binary_img * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    h, w = binary_img.shape
    center_x = w // 2
    y_center = (y_range[0] + y_range[1]) // 2
    x1, y1, x2, y2 = car_bbox

    def find_valid_flat_groups(hist, min_road_width, threshold):
        # Find indices where the histogram is exactly zero
        zero_indices = np.where(hist == 0)[0]
        if len(zero_indices) == 0:
            return []

        # Group continuous flat regions
        groups = np.split(zero_indices, np.where(np.diff(zero_indices) > 1)[0] + 1)

        valid_groups = []
        for group in groups:
            if len(group) < min_road_width:
                continue

            left = group[0]
            right = group[-1]

            # Check for peaks near the edges of the flat region
            left_peak = np.max(hist[max(0, left - 50):left]) if left > 0 else 0
            right_peak = np.max(hist[right + 1:min(len(hist), right + 51)]) if right < len(hist) - 1 else 0

            if left_peak >= threshold and right_peak >= threshold:
                valid_groups.append(group)

        return valid_groups

    flat_groups = find_valid_flat_groups(hist, min_road_width, threshold)
    cv2.rectangle(vis_img, (x1, y1), (x2, y2), (255, 0, 0), 2)

    # Try to select group that includes center
    central_group = None
    for group in flat_groups:
        if group[0] <= center_x <= group[-1]:
            central_group = group
            break

    if central_group is None and flat_groups:
        central_group = flat_groups[0]  # Fallback: first valid group found

    if central_group is not None:
        left_idx = central_group[0]
        right_idx = central_group[-1]

        # Draw on image
        cv2.circle(vis_img, (left_idx, y_center), 6, (0, 0, 255), -1)  # Red
        cv2.circle(vis_img, (right_idx, y_center), 6, (0, 0, 255), -1)  # Red

        return (left_idx, y_center), (right_idx, y_center), vis_img

    return None, None, vis_img
