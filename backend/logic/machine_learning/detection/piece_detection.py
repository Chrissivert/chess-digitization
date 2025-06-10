import numpy as np
import onnxruntime as ort
from typing import Tuple

from logic.machine_learning.detection.bbox_scores import get_boxes_and_scores, process_boxes_and_scores
from logic.machine_learning.utilities.preprocess import get_input


async def run_pieces_model(frame, pieces_model_ref):
    """
    Processes a video frame using the given pieces detection model to predict chess pieces.

    Parameters:
    - frame: A single video frame (image).
    - pieces_model_ref: ONNX InferenceSession for piece detection.

    Returns:
    - pieces: A list of detected chess pieces as (x, y, pieceTypeIndex).
    """
    
    frame_height, frame_width, _ = frame.shape

    # Prepare the input tensor
    image4d, width, height, padding, roi = get_input(frame)

    # Prepare input dict for inference
    inputs = {pieces_model_ref.get_inputs()[0].name: image4d}

    # Run model
    pieces_prediction = pieces_model_ref.run(None, inputs)

    # Process prediction
    boxes, scores = get_boxes_and_scores(pieces_prediction[0], width, height, frame_width, frame_height, padding, roi)

    # Final filtering/postprocessing
    pieces = process_boxes_and_scores(boxes, scores)

    # Clean up
    del pieces_prediction
    del image4d  
    del boxes  

    return pieces




# async def detect(pieces_model_ref: ort.InferenceSession, video_ref: np.ndarray, keypoints: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
#     """
#     Detects the pieces in a video frame and returns the bounding boxes and their associated scores using an ONNX model.

#     This function preprocesses the input video frame, predicts the pieces using the given ONNX model, 
#     and extracts bounding boxes and scores for the detected pieces.

#     Args:
#         pieces_model_ref (onnxruntime.InferenceSession): The ONNX model session used for detecting chess pieces.
#         video_ref (np.ndarray): The input video frame as a NumPy array with shape (height, width, channels).
#         keypoints (np.ndarray): The keypoints for the video frame, typically used for identifying regions of interest.

#     Returns:
#         Tuple[np.ndarray, np.ndarray]: A tuple containing two elements:
#             - boxes (np.ndarray): An array of bounding boxes for detected pieces, with shape (N, 4) where N is the number of pieces.
#             - scores (np.ndarray): An array of confidence scores for each bounding box, with shape (N,).
#     """
#     frame_height, frame_width, _ = video_ref.shape

#     image4d, width, height, padding, roi = get_input(video_ref, keypoints)
#     inputs = {pieces_model_ref.get_inputs()[0].name: image4d} 

#     pieces_prediction = pieces_model_ref.run(None, inputs)
#     boxes, scores = get_boxes_and_scores(pieces_prediction[0], width, height, frame_width, frame_height, padding, roi)
    
#     del pieces_prediction
#     del image4d  

#     return boxes, scores





def predict_pieces(frame, ort_session):
    """
    Predict bounding boxes, class indices, and scores using the ONNX model.

    This function processes the input image, runs inference on an ONNX model, 
    and returns the predicted bounding boxes, class indices, and confidence scores.

    Args:
        image (numpy array): Input image for prediction. Expected shape is (height, width, channels).
        ort_session: ONNX Runtime InferenceSession object used to run inference on the ONNX model.

    Returns:
        tuple: A tuple containing the predictions, which typically include:
               - Bounding box coordinates (xc, yc, w, h)
               - Confidence scores for each box
               - Class indices indicating which object each bounding box corresponds to
    """
    preprocessed_image = frame

    # Get input and output information from the ONNX model
    model_inputs = ort_session.get_inputs()  # Get the input layers of the model
    model_outputs = ort_session.get_outputs()  # Get the output layers of the model

    # Run inference on the preprocessed image using the ONNX model
    predictions = ort_session.run(
        output_names=[output.name for output in model_outputs],  # Specify the model outputs to collect
        input_feed={model_inputs[0].name: preprocessed_image}  # Feed the preprocessed image to the model
    )

    # Extract the predicted values (bounding boxes, class indices, and scores) from the output
    pieces_predictions = predictions[0]

    return pieces_predictions


async def detect(pieces_model_ref, video_ref, keypoints):
    frame_height, frame_width, _ = video_ref.shape

    image4d, width, height, padding, roi = get_input(video_ref, keypoints)

    pieces_prediction = predict_pieces(image4d, pieces_model_ref)
    boxes, scores = get_boxes_and_scores(pieces_prediction, width, height, frame_width, frame_height, padding, roi)
    

    del pieces_prediction
    del image4d  

    return boxes, scores