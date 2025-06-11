import chess
import chess.pgn

def get_moves_from_pgn(board: chess.Board) -> str:
    """Convert board history to PGN string."""
    game = chess.pgn.Game.from_board(board)
    exporter = chess.pgn.StringExporter(headers=False, variations=False, comments=False)
    
    pgn = game.accept(exporter)
    return pgn.replace("\n", " ").replace("\r", "")

def make_update_payload(board: chess.Board, greedy: bool = False) -> dict:
    """Generate the payload containing board state, moves, and other details."""
    moves = get_moves_from_pgn(board)  # Assuming you have this function
    fen = board.fen()
    last_move = board.peek().uci() if board.move_stack else ""

    payload: dict = {
        "moves": moves,
        "fen": fen,
        "lastMove": last_move,
        "greedy": greedy
    }

    return payload