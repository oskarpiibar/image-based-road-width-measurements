import csv
import os
import cv2
import numpy as np
from ..preprocessing.preprocessing import pipeline, mark_edges_of_flat_region, get_hist
from config import DATA, IMAGES, TEMPLATE_FOLDER


def mark_line_intersections_if_car_on_line(binary_img, car_bbox, hist, threshold, min_lane_width):
    detected_edge = None
    other_edge_point = None

    # Prepare image for drawing
    vis_img = cv2.cvtColor((binary_img * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    height, width = binary_img.shape

    # Car bounding box
    x1, y1, x2, y2 = car_bbox
    car_center_x = (x1 + x2) // 2
    car_center_y = (y1 + y2) // 2

    # Draw car box
    cv2.rectangle(vis_img, (x1, y1), (x2, y2), (255, 0, 0), 2)

    # Look for intersection with white line
    pad = 1
    x1e = max(0, x1 - pad)
    x2e = min(width, x2 + pad)
    y1e = max(0, y1 - pad)
    y2e = min(height, y2 + pad)

    car_region = binary_img[y1e:y2e, x1e:x2e]

    if np.any(car_region == 1):  # car intersects white
        top_y = max(0, y1 - 1)
        bot_y = min(height - 1, y2)
        top_edge = binary_img[top_y, x1e:x2e]
        bottom_edge = binary_img[bot_y, x1e:x2e]
        top_hits = np.where(top_edge == 1)[0]
        bottom_hits = np.where(bottom_edge == 1)[0]

        def closest_to_center(hit_indices, y_val):
            if len(hit_indices) == 0:
                return None
            abs_xs = x1e + hit_indices
            closest_idx = np.argmin(np.abs(abs_xs - car_center_x))
            return (abs_xs[closest_idx], y_val)

        top_point = closest_to_center(top_hits, top_y)
        bottom_point = closest_to_center(bottom_hits, bot_y)

        if top_point:
            cv2.circle(vis_img, top_point, 6, (0, 255, 255), -1)  # Yellow
        if bottom_point:
            cv2.circle(vis_img, bottom_point, 6, (0, 255, 0), -1)  # Green
        if top_point and bottom_point:
            avg_x = (top_point[0] + bottom_point[0]) // 2
            avg_y = (top_point[1] + bottom_point[1]) // 2
            mid_point = (avg_x, avg_y)
            cv2.circle(vis_img, mid_point, 6, (0, 0, 255), -1)  # Red

        detected_edge = determine_detected_edge_position(top_point, bottom_point)
        if detected_edge is not None:
            found_right = None
            for x in range(detected_edge[0] + min_lane_width, width):
                if hist[x] >= threshold:
                    found_right = x
                    break

            found_left = None
            for x in range(detected_edge[0] - min_lane_width, -1, -1):
                if hist[x] >= threshold:
                    found_left = x
                    break

            # Choose best valid peak
            if found_left and found_right:
                dist_to_left = abs(detected_edge[0] - found_left)
                dist_to_right = abs(detected_edge[0] - found_right)
                if car_center_x > detected_edge[0] and dist_to_right > dist_to_left:
                    other_edge_point = (found_right, car_center_y)
                elif car_center_x > detected_edge[0] and dist_to_right < dist_to_left:
                    other_edge_point = (found_right, car_center_y)
                elif car_center_x < detected_edge[0] and dist_to_right < dist_to_left:
                    other_edge_point = (found_left, car_center_y)
                else:
                    other_edge_point = (found_left, car_center_y)

            elif found_left:
                other_edge_point = (found_left, car_center_y)
            elif found_right:
                other_edge_point = (found_right, car_center_y)

            if other_edge_point:
                cv2.circle(vis_img, other_edge_point, 6, (0, 165, 255), -1)

    if detected_edge is not None and other_edge_point is not None:
        if detected_edge[0] < other_edge_point[0]:
            left_boundary, right_boundary = detected_edge, other_edge_point
            return left_boundary, right_boundary, vis_img
        else:
            left_boundary, right_boundary = other_edge_point, detected_edge
            return left_boundary, right_boundary, vis_img

    return None, None, vis_img


def find_euclidian_distance(point_1, point_2):
    return np.linalg.norm(np.array(point_1) - np.array(point_2))


def determine_detected_edge_position(top_point, bottom_point):
    if top_point and bottom_point:
        avg_x = (top_point[0] + bottom_point[0]) // 2
        avg_y = (top_point[1] + bottom_point[1]) // 2
        return (avg_x, avg_y)
    elif top_point:
        return top_point
    elif bottom_point:
        return bottom_point
    else:
        return None


def process_image(img_rgb, template_folder):
    binary_img, car_bbox, car_center = pipeline(img_rgb, TEMPLATE_FOLDER)
    x1, y1, x2, y2 = car_bbox
    car_center_x = (x1 + x2) // 2
    car_center_y = (y1 + y2) // 2
    y_range = (max(0, y1), min(binary_img.shape[0], y2))

    hist = get_hist(binary_img, y_range)

    left_boundary, right_boundary, vis_img = mark_line_intersections(binary_img, car_bbox, hist, 2, y_range, 450)

    return (car_center_x, car_center_y), left_boundary, right_boundary, vis_img


def batch_process_folder(input_folder, output_folder, template_folder, csv_file):
    os.makedirs(output_folder, exist_ok=True)

    csv_path = csv_file
    with open(csv_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["filename", "road_width", "distance_left", "distance_right", "car_center"])

        input_folder_path = os.path.join(DATA, IMAGES, input_folder)

        for i, fname in enumerate(os.listdir(input_folder_path)):
            if not fname.lower().endswith((".png")):
                continue

            img_path = os.path.join(input_folder_path, fname)
            img = cv2.imread(img_path)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            car_center, left_boundary, right_boundary, vis_img = process_image(img_rgb, template_folder)

            if left_boundary is not None and right_boundary is not None:
                ratio = 0.018871954437029596 # ground truth ratio for Nurburgring GP track
                road_width = find_euclidian_distance(left_boundary, right_boundary) * ratio
                distance_to_left = find_euclidian_distance(car_center, left_boundary) * ratio
                distance_to_right = find_euclidian_distance(car_center, right_boundary) * ratio

                writer.writerow([fname, road_width, distance_to_left, distance_to_right, car_center])

                save_path = os.path.join(output_folder, fname)
                cv2.imwrite(save_path, vis_img)


def mark_line_intersections(binary_img, car_bbox, hist, threshold, y_range, min_lane_width):
    # Check if car is intersecting a line
    x1, y1, x2, y2 = car_bbox
    car_center_x = (x1 + x2) // 2

    pad = 1
    x1e = max(0, x1 - pad)
    x2e = min(binary_img.shape[1], x2 + pad)
    y1e = max(0, y1 - pad)
    y2e = min(binary_img.shape[0], y2 + pad)

    car_region = binary_img[y1e:y2e, x1e:x2e]

    left_slice = hist[car_center_x - min_lane_width:car_center_x]
    has_activity_left = np.any(left_slice > threshold)

    right_slice = hist[car_center_x:car_center_x + min_lane_width]
    has_activity_right = np.any(right_slice > threshold)

    if np.any(car_region == 1):
        if has_activity_left and has_activity_right:
            return mark_edges_of_flat_region(binary_img, car_bbox, hist, threshold, y_range, min_lane_width)
        else:
            return mark_line_intersections_if_car_on_line(binary_img, car_bbox, hist, threshold, min_lane_width)
    else:
        return mark_edges_of_flat_region(binary_img, car_bbox, hist, threshold, y_range, min_lane_width)
