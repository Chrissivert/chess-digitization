
import numpy as np
import tensorflow as tf

from typing import Tuple, List, Dict
from logic.machine_learning.utilities.constants import MODEL_WIDTH, MODEL_HEIGHT, MARKER_DIAMETER

def process_boxes_and_scores(boxes: tf.Tensor, scores: tf.Tensor) -> np.ndarray:
    """
    Processes bounding boxes and scores to apply non-max suppression (NMS),
    extract centers of selected boxes, and concatenate them with their class indices.

    Args:
        boxes (tf.Tensor): A tensor of shape (num_boxes, 4), representing bounding box coordinates [x_min, y_min, x_max, y_max].
        scores (tf.Tensor): A tensor of shape (num_boxes, num_classes), representing the classification scores for each box.

    Returns:
        np.ndarray: A NumPy array containing the centers of the selected bounding boxes and their corresponding class indices.
    """
    max_scores: tf.Tensor = tf.reduce_max(scores, axis=1)
    argmax_scores: tf.Tensor = tf.argmax(scores, axis=1)
    nms: tf.Tensor = tf.image.non_max_suppression(boxes, max_scores, max_output_size=100, iou_threshold=0.3, score_threshold=0.1)
    
    # Use get_centers function to get the centers from the selected boxes
    centers_bbox: tf.Tensor = get_centers_of_bbox(tf.gather(boxes, nms, axis=0))

    # Gather the class indices of the selected boxes and expand dimensions
    class_indices: tf.Tensor = tf.expand_dims(tf.gather(argmax_scores, nms, axis=0), axis=1)

    # Cast cls to float16 (ensure it's compatible with centers)
    class_indices: tf.Tensor = tf.cast(class_indices, dtype=tf.float16)

    # Concatenate the centers with the class indices
    res: tf.Tensor = tf.concat([centers_bbox, class_indices], axis=1)

    res_array: np.ndarray = res.numpy()
    
    return res_array

def get_boxes_and_scores(preds: np.ndarray, width: int, height: int, video_width: int, video_height: int, padding: Tuple[int, int, int, int], roi: Tuple[int, int]
) -> Tuple[tf.Tensor, tf.Tensor]:
    """
    This function processes predictions to extract bounding boxes and their associated scores.

    Args:
        preds: The predictions array with shape (batch_size, num_boxes, num_predictions).
        width: The width to scale the bounding box coordinates to.
        height: The height to scale the bounding box coordinates to.
        video_width: The width of the video for further scaling.
        video_height: The height of the video for further scaling.
        padding: The padding to adjust the bounding boxes.
        roi: The region of interest, which is added to the bounding box coordinates.

    Returns:
        A tuple containing the bounding boxes and scores as Tensor2D tensors.
    """
    
    # Transpose preds to match the desired shape
    preds_t = np.transpose(preds, (0, 2, 1))  # Shape: (batch_size, num_predictions, num_boxes)
    
    # Extract width (w) and height (h) of the boxes
    w = preds_t[:, :, 2:3]  
    h = preds_t[:, :, 3:4]  
    
    # Convert xc, yc, w, h to l, t, r, b (left, top, right, bottom)
    l = preds_t[:, :, 0:1] - (w / 2)  # Left
    t = preds_t[:, :, 1:2] - (h / 2)  # Top
    r = l + w  # Right
    b = t + h  # Bottom

    # Apply padding to the bounding box coordinates
    l -= padding[0]
    r -= padding[0]
    t -= padding[2]
    b -= padding[2]

    # Scale the bounding box coordinates to the target size
    l *= (width / (MODEL_WIDTH - padding[0] - padding[1]))
    r *= (width / (MODEL_WIDTH - padding[0] - padding[1]))
    t *= (height / (MODEL_HEIGHT - padding[2] - padding[3]))
    b *= (height / (MODEL_HEIGHT - padding[2] - padding[3]))

    # Add ROI (Region of Interest)
    l += roi[0]
    r += roi[0]
    t += roi[1]
    b += roi[1]

    # Scale based on video size
    l *= (MODEL_WIDTH / video_width)
    r *= (MODEL_WIDTH / video_width)
    t *= (MODEL_HEIGHT / video_height)
    b *= (MODEL_HEIGHT / video_height)
    
    # Concatenate the left, top, right, and bottom coordinates to form the bounding boxes
    boxes = np.concatenate([l, t, r, b], axis=2) 

    # Extract the scores (assuming score is in the 5th element onward)
    scores = preds_t[:, :, 4:] 

    # Squeeze to remove unnecessary dimensions (if any)
    boxes = np.squeeze(boxes, axis=0)
    scores = np.squeeze(scores, axis=0)

    # Convert to TensorFlow tensors
    boxes_tf = tf.convert_to_tensor(boxes, dtype=tf.float32)
    scores_tf = tf.convert_to_tensor(scores, dtype=tf.float32)

    return boxes_tf, scores_tf


def get_bbox(points: List[Tuple[float, float]]) -> Dict[str, float]:
    """
    Computes the bounding box for a list of 2D points.

    The bounding box is the smallest rectangle that can contain all the points, 
    with sides aligned to the axes. It is defined by the minimum and maximum 
    x and y coordinates of the points.

    Args:
        points (List[Tuple[float, float]]): A list of 2D points, where each point 
                                             is represented as a tuple (x, y).

    Returns:
        Dict[str, float]: A dictionary containing the bounding box parameters:
                          "xmin", "xmax", "ymin", "ymax", "width", and "height".
    """
    xs: List[float] = [p[0] for p in points]
    ys: List[float] = [p[1] for p in points]
    
    xmin: float = min(xs)
    xmax: float = max(xs)
    ymin: float = min(ys)
    ymax: float = max(ys)

    width: float = xmax - xmin
    height: float = ymax - ymin

    bbox: Dict[str, float] = {
        "xmin": xmin,
        "xmax": xmax,
        "ymin": ymin,
        "ymax": ymax,
        "width": width,
        "height": height
    }

    return bbox


def get_centers_of_bbox(boxes: tf.Tensor) -> tf.Tensor:
    """
    Calculates the center coordinates of bounding boxes.

    This function computes the center (cx, cy) of each bounding box from 
    the left, top, right, and bottom coordinates. It assumes that the input 
    boxes are in the format [left, top, right, bottom] and casts them to `float16`
    for consistency with the model's data type.

    Args:
        boxes (tf.Tensor): A tensor of shape (N, 4), where each row represents 
                            a bounding box with the format [left, top, right, bottom].

    Returns:
        tf.Tensor: A tensor of shape (N, 2), where each row contains the center 
                   coordinates [cx, cy] of the corresponding bounding box.
    """
    boxes = tf.cast(boxes, dtype=tf.float16)

    # Extract left, top, right, and bottom coordinates
    l = boxes[:, 0:1]
    t = boxes[:, 1:2]
    r = boxes[:, 2:3]
    b = boxes[:, 3:4]

    # Calculate center coordinates (cx, cy)
    cx = (l + r) / 2
    cy = (t + b) / 2

    centers = tf.concat([cx, cy], axis=1)
    
    return centers


def get_bbox_centers(boxes: tf.Tensor) -> tf.Tensor:
    """
    Calculates the center coordinates (cx, cy) of bounding boxes.

    Args:
        boxes (tf.Tensor): A tensor of shape (N, 4), where each row represents 
                           a bounding box in the format [left, top, right, bottom].

    Returns:
        tf.Tensor: A tensor of shape (N, 2), where each row contains the center 
                   coordinates [cx, cy] of the corresponding bounding box.
    """
    # Slice the boxes tensor to get l, r, and b
    l = tf.cast(boxes[:, 0:1], tf.float32)  # Ensure l is float32
    r = tf.cast(boxes[:, 2:3], tf.float32)  # Ensure r is float32
    b = tf.cast(boxes[:, 3:4], tf.float32)  # Ensure b is float32

    # Calculate the center coordinates
    cx = (l + r) / 2
    cy = b - (r - l) / 3

    # Concatenate cx and cy to get the box centers
    box_centers = tf.concat([cx, cy], axis=1)

    return box_centers


def get_center_of_set_of_points(points: List[Tuple[float, float]]) -> List[float]:
    """
    Calculates the center of a set of 2D points by averaging their x and y coordinates.

    Args:
        points (List[Tuple[float, float]]): A list of points where each point is a tuple of (x, y) coordinates.

    Returns:
        List[float]: A list containing the (x, y) coordinates of the center.
    """
    center_x: float = sum(x[0] for x in points)
    center_y: float = sum(x[1] for x in points) 
    center: List[float] = [center_x / len(points), center_y / len(points)]
    
    return center

def get_xy(marker_xy: Tuple[int, int], height: int, width: int) -> Tuple[float, float]:
    """
    Converts marker coordinates to a normalized system based on frame dimensions.

    Args:
        marker_xy (Tuple[int, int]): The (x, y) coordinates of the marker.
        height (int): The height of the canvas.
        width (int): The width of the canvas.

    Returns:
        Tuple[float, float]: The normalized (x, y) coordinates of the marker.
    """
    sx: float = MODEL_WIDTH / width 
    sy: float = MODEL_HEIGHT / height
    xy: Tuple[float, float] = (sx * marker_xy[0], sy * (marker_xy[1] + height + MARKER_DIAMETER))
    return xy