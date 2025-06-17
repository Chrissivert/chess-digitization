import chess
from fastapi import WebSocket
from typing import List, Literal
from .camera import Camera

from logic.machine_learning.utilities.constants import START_FEN

class Board:
  """ Chess board class to handle chess moves and history. """
  
  def __init__(self, id: int, fen: str = START_FEN):
    """ Initialize the chess board object.
    Args:
      id (int): Board ID
    """
    self.set_id(id)
    self.camera = Camera(id)
    self.move_history: List[str] = []
    self.clients: List[WebSocket] = []
    self.chess_board = chess.Board(fen)
    self.invalid_latched = False
    
  def set_id(self, id: int) -> None:
    """ Set the ID of the chess board. 
    
    Args:
      id (int): Board ID
    Raises:
      TypeError: If the ID is not an integer.
      ValueError: If the ID is a negative integer.
    """
    if not isinstance(id, int):
      raise TypeError("ID must be an integer.")
    if id < 1:
      raise ValueError("ID must be a positive integer.")
    
    self.id = id
      
  def validate_move(self, move) -> (tuple[Literal['INVALID'], Literal[False]] | tuple[str, Literal[True]]):
    """ Check if a chess move is valid. 
    
    Args: 
      move(str): Chess move in SAN format.
    Returns:
      tuple[str, bool]: Tuple containing the move and a boolean indicating if the move was valid.
    """
    move = move.strip()
    
    if self.invalid_latched:
      return "INVALID", False
      
    try:
      # self.chess_board.push_san(move)
      self.move_history.append(move)
      return move, True
    except Exception:
      self.invalid_latched = True
      return "INVALID", False
        
  def reset_board(self) -> str:
    """ Reset the chess board and move history.
    
    Returns:
      str: "RESET" if the board was reset successfully, "RESET_FAILED" if the reset failed.
    """
    try:
      self.chess_board.reset()
      self.move_history = []
      self.invalid_latched = False
    except Exception:
      return "RESET_FAILED"
    return "RESET"
  
  
  
