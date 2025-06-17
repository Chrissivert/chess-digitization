from fastapi import APIRouter, WebSocket
import logic.api.services.board_storage as storage

router = APIRouter()

@router.websocket("/moves/{board_id}")
async def websocket_endpoint(websocket: WebSocket, board_id: int) -> None:
  """ Sends chess moves and history.
  
  Args:
    websocket (WebSocket): WebSocket connection
    board_id (int): Board ID
  """
  await websocket.accept()
  if board_id not in storage.boards:
    await websocket.close()
    return
    
  storage.boards[board_id].clients.append(websocket)
  try:
    await websocket.send_text(f"FEN:{storage.boards[board_id].chess_board.fen()}")
    
    for move in storage.boards[board_id].move_history:
      await websocket.send_text(move)
    while True:
      await websocket.receive_text()
  except Exception:
    if websocket in storage.boards[board_id].clients:
      storage.boards[board_id].clients.remove(websocket)
