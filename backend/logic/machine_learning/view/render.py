import cv2
import numpy as np
import tensorflow as tf

from typing import List, Tuple
from logic.machine_learning.utilities.constants import MODEL_WIDTH, MODEL_HEIGHT


def draw_boxes_with_scores(frame: np.ndarray, boxes: tf.Tensor, scores: tf.Tensor, threshold: float = 0.5) -> None:
    """
    Draw bounding boxes on a frame for detections with a score above the threshold.

    Args:
        frame (np.ndarray): The image/frame to draw on.
        boxes (np.ndarray or tf.Tensor): Bounding boxes of shape (N, 4), normalized to the model input size.
        scores (np.ndarray or tf.Tensor): Confidence scores of shape (N, num_classes).
        threshold (float): Minimum score to draw a box.
    """
    boxes_np = boxes.numpy() if isinstance(boxes, tf.Tensor) else boxes
    scores_np = scores.numpy() if isinstance(scores, tf.Tensor) else scores

    frame_height, frame_width = frame.shape[:2]
    scale_x = frame_width / MODEL_WIDTH
    scale_y = frame_height / MODEL_HEIGHT

    for box, score_arr in zip(boxes_np, scores_np):
        max_score = np.max(score_arr)
        if max_score >= threshold:
            l, t, r, b = box
            scaled_box = (l * scale_x, t * scale_y, r * scale_x, b * scale_y)
            draw_box(frame, (0, 100, 200), scaled_box, max_score)


def draw_box(frame: np.ndarray, color: Tuple[int, int, int],  box: Tuple[float, float, float, float], score: float,) -> np.ndarray:
    """
    Draw a labeled bounding box on a frame.

    Args:
        frame (np.ndarray): The image to draw on.
        color (Tuple[int, int, int]): Box color in BGR format.
        box (Tuple[float, float, float, float]): The bounding box (left, top, right, bottom).
        score (float): Confidence score to display on the box.
        font_height (int): Font size (for compatibility/future use).

    Returns:
        np.ndarray: The frame with the box and label drawn.
    """
    font = cv2.FONT_HERSHEY_SIMPLEX
    l, t, r, b = map(int, box)

    cv2.rectangle(frame, (l, t), (r, b), color, 2)
    text = f"{score:.2f}"
    text_size = cv2.getTextSize(text, font, 0.5, 1)[0]
    text_w, text_h = text_size

    cv2.rectangle(frame, (l, t - text_h - 4), (l + text_w + 4, t), color, -1)
    cv2.putText(frame, text, (l + 2, t - 2), font, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    return frame


def draw_points(frame: np.ndarray, points: List[Tuple[float, float]]) -> np.ndarray:
    """
    Draws points as red circles on a frame.

    Args:
        frame (np.ndarray): The image/frame to draw on.
        points (List[Tuple[float, float]]): List of normalized (x, y) points.

    Returns:
        np.ndarray: Frame with the points drawn.
    """
    frame_height, frame_width = frame.shape[:2]

    for x, y in points:
        cx = round(x * frame_width / MODEL_WIDTH)
        cy = round(y * frame_height / MODEL_HEIGHT)
        cv2.circle(frame, (cx, cy), radius=5, color=(0, 0, 255), thickness=-1)

    return frame


def draw_polygon(frame: np.ndarray, polygon: List[Tuple[float, float]]) -> np.ndarray:
    """
    Draws a closed polygon on the frame.

    Args:
        frame (np.ndarray): The image/frame to draw on.
        polygon (List[Tuple[float, float]]): Normalized (x, y) coordinates of the polygon vertices.

    Returns:
        np.ndarray: Frame with the polygon drawn.
    """
    frame_height, frame_width = frame.shape[:2]
    sx = frame_width / MODEL_WIDTH
    sy = frame_height / MODEL_HEIGHT

    scaled_polygon = np.array(
        [[(x * sx, y * sy) for x, y in polygon]], dtype=np.int32
    )

    cv2.polylines(frame, scaled_polygon, isClosed=True, color=(0, 0, 255), thickness=2)

    return frame
