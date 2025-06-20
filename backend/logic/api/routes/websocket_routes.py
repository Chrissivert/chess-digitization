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
    for move in storage.boards[board_id].move_history:
      await websocket.send_text(move)
    while True:
      await websocket.receive_text()
  except Exception:
    if websocket in storage.boards[board_id].clients:
      storage.boards[board_id].clients.remove(websocket)
      
      
      
@router.websocket("/fen/{board_id}")
async def websocket_fen_only(websocket: WebSocket, board_id: int) -> None:
    """ Sends only the current FEN string over WebSocket.
    
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
        # Send the initial FEN stored in the board, not the current chess_board position
        initial_fen = storage.boards[board_id].first_fen
        await websocket.send_text(f"FEN:{initial_fen}")
        print(f"WebSocket connected for board {board_id}, sending initial FEN: {initial_fen}")

        # Keep connection open waiting for messages (to keep alive)
        while True:
            await websocket.receive_text()
    except Exception:
        if websocket in storage.boards[board_id].clients:
            storage.boards[board_id].clients.remove(websocket)
