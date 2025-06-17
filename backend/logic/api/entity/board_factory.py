from logic.api.entity.board import Board

class BoardFactory:
  """ Factory class for creating Board objects. """
    
  def create_boards(self, board_count:int, fen: str) -> dict[int, Board]:
    """ Create a dictionary of Board objects. """
    print(fen)
    boards = {i: Board(i, fen) for i in range(1, (board_count + 1))}
    return boards