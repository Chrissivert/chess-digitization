import cv2, onnxruntime as ort
from typing import Optional
from logic.machine_learning.detection.run_detections import get_board_corners
from logic.machine_learning.board_state.map_pieces import get_payload
import logic.api.services.board_storage as storage
from logic.api.services import board_storage
import asyncio

async def process_video(
    piece_model_session: ort.InferenceSession,
    corner_ort_session: ort.InferenceSession,
    video: cv2.VideoCapture,
    board_id: int
) -> None:

    cap = video 
    if not cap.isOpened():
        print("Error: Cannot open camera.")
        return

    frame_counter = 0
    board_corners_ref: Optional[list] = None
    from logic.api.services.board_service import BoardService

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Error: Could not read frame.")
            break

        if frame_counter % 5 == 0:
            if board_corners_ref is None:
                board_corners_ref = await get_board_corners(
                    frame, piece_model_session, corner_ort_session
                )
                if board_corners_ref is None:
                    print("Corners not found.")
                    continue

            # Check if the board_id is registered before proceeding
            boards = board_storage.boards
            if board_id in boards:
                frame, payload = await get_payload(
                    piece_model_session, frame, board_corners_ref, board_id
                )
                if payload:
                    move = payload[1]["sans"][0]
                    print(f"Detected move: {move}")
                                        
                    boards = storage.boards
                    board_service = BoardService()
                    await board_service.send_move(board_id, move)
                    

            cv2.imshow("Chess Board Detection", cv2.resize(frame, (1280, 720)))
            cv2.waitKey(1)

        frame_counter += 1

    cap.release()
    cv2.destroyAllWindows()

async def prepare_to_run_video(board_id: int, video: cv2.VideoCapture):
    piece_session  = ort.InferenceSession("resources/models/480M_leyolo_pieces.onnx")
    corner_session = ort.InferenceSession("resources/models/480L_leyolo_xcorners.onnx")

    await process_video(piece_session, corner_session, video, board_id)


# quick manual test
if __name__ == "__main__":
    asyncio.run(prepare_to_run_video())
