import cv2
import numpy as np
import tensorflow as tf

from typing import Tuple, List, Dict, Optional
from logic.machine_learning.detection.bbox_scores import get_bbox
from logic.machine_learning.utilities.constants import MODEL_WIDTH, MODEL_HEIGHT

def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Preprocess the input image to make it compatible with the detection model.

    This function resizes the input image to match the model's expected input size,
    normalizes pixel values, and converts the image to the correct format for the model.
    The pixel values are normalized to the range [0, 1] and the image is cast to float16.

    Args:
        image (numpy.ndarray): The input image to preprocess. The image is in the format (H, W, C) where:
                        - H and W are the height and width of the image respectively.
                        - C represents the number of channels (3 for RGB).

    Returns:
        numpy.ndarray: Preprocessed image ready for inference (with batch dimension and normalized).
        Image is in the format CHW.
    """

    # image = cv2.resize(image, (MODEL_WIDTH, MODEL_HEIGHT))  # Resize image
    image = image / 255.0  # Normalize pixel values to [0, 1]
    image = image.transpose(2, 0, 1)  # Convert HWC to CHW
    return image[np.newaxis, ...].astype(np.float16)  # Add batch dimension and convert to float16

    #After adding a batch dimension the image is in the shape (1,C,H,W)
    # We need to add a batch dimension to the image to match the input shape expected by the model
    #This you can confirm in netron.app by loading the model and checking the input shape.

    #We convert it to float16 to match the model's input data type. Also float16 saves memory
    #and speeds up computation during inference. Inference is the process of using a trained model to 
    #make predictions on new data.

    #One other thing, normalizing the pixel values helps improve model performance by
    #Ensuring consistent input range, as many models are trained with inputs in the [0, 1] range.
    


def get_input(
    video_ref: np.ndarray, 
    keypoints: Optional[np.ndarray] = None, 
    padding_ratio: int = 12
) -> Tuple[int, int, Optional[np.ndarray]]:
    """
    Processes the input video frame by extracting the region of interest (ROI),
    resizing it to match the model's input dimensions, and applying necessary padding.

    Args:
        video_ref (np.ndarray): Input video frame represented as a NumPy array of shape (height, width, channels).
        keypoints (Optional[np.ndarray]): Array of keypoints used to determine the bounding box (ROI). Defaults to None.
        padding_ratio (int): Factor to compute padding around the detected bounding box. Defaults to 12.

    Returns:
        Tuple[np.ndarray, int, int, List[int], List[int]]:
            - image4d (np.ndarray): Preprocessed and padded input ready for the model.
            - width (int): Width of the cropped video region.
            - height (int): Height of the cropped video region.
            - padding (List[int]): Padding applied as [left, right, top, bottom].
            - roi (List[int]): Coordinates of the region of interest in the format [xmin, ymin, xmax, ymax].
    """

    video_height, video_width, _ = video_ref.shape
    roi = None

    if keypoints is not None:
        bbox = get_bbox(keypoints)
        padding_left = int(bbox['width'] / padding_ratio)
        padding_right = int(bbox['width'] / padding_ratio)
        padding_top = int(bbox['height'] / padding_ratio)
        padding_bottom = int(bbox['height'] / padding_ratio)

        padded_roi_width = bbox['width'] + padding_left + padding_right
        padded_roi_height = bbox['height'] + padding_top + padding_bottom
        ratio = padded_roi_height / padded_roi_width
        desired_ratio = MODEL_HEIGHT / MODEL_WIDTH

        if ratio > desired_ratio:
            target_width = padded_roi_height / desired_ratio
            dx = target_width - padded_roi_width
            padding_left += int(dx / 2)
            padding_right += dx - int(dx / 2)
        else:
            target_height = padded_roi_width * desired_ratio
            padding_top += target_height - padded_roi_height

        roi = [
            max(int(video_width * (bbox['xmin'] - padding_left) / MODEL_WIDTH), 0),
            max(int(video_height * (bbox['ymin'] - padding_top) / MODEL_HEIGHT), 0),
            min(int(video_width * (bbox['xmax'] + padding_right) / MODEL_WIDTH), video_width),
            min(int(video_height * (bbox['ymax'] + padding_bottom) / MODEL_HEIGHT), video_height)
        ]
    else:
        roi = [0, 0, video_width, video_height]

    # Cropping
    video_ref = video_ref[roi[1]:roi[3], roi[0]:roi[2], :]
    
    # Resizing
    height, width, _ = video_ref.shape
    ratio = height / width
    desired_ratio = MODEL_HEIGHT / MODEL_WIDTH
    resize_height = MODEL_HEIGHT
    resize_width = MODEL_WIDTH
    if ratio > desired_ratio:
        resize_width = int(MODEL_HEIGHT / ratio)
    else:
        resize_height = int(MODEL_WIDTH * ratio)
    
    video_ref = tf.image.resize(video_ref, [resize_height, resize_width])
    
    # Padding
    dx = MODEL_WIDTH - video_ref.shape[1]
    dy = MODEL_HEIGHT - video_ref.shape[0]
    pad_right = dx // 2
    pad_left = dx - pad_right
    pad_bottom = dy // 2
    pad_top = dy - pad_bottom
    padding = [pad_left, pad_right, pad_top, pad_bottom]
    
    video_ref = tf.pad(
    video_ref,
    paddings=[[pad_top, pad_bottom], [pad_left, pad_right], [0, 0]],
    constant_values=114
)

    image4d = preprocess_image(video_ref.numpy())
    
    return image4d, width, height, padding, roi
