import chess
import numpy as np
from typing import Dict, List, Optional
from logic.machine_learning.utilities.constants import LABEL_MAP

class MoveData(Dict):
    sans: List[str]
    from_: List[int]
    to: List[int]
    targets: List[Optional[int]]

def get_piece_idx(board: chess.Board, move: chess.Move) -> Optional[int]:
    """
    Returns the label index of the piece involved in a move.

    Args:
        board (chess.Board): The current board state.
        move (chess.Move): The move being analyzed.

    Returns:
        Optional[int]: The index from LABEL_MAP corresponding to the piece symbol,
                       or None if no piece was found at the source square.
    """
    piece = board.piece_at(move.from_square)
    if not piece:
        return None

    piece_symbol = piece.symbol()

    # Handle promotion case
    if move.promotion:
        piece_symbol = chess.Piece(move.promotion, piece.color).symbol()

    return LABEL_MAP.get(piece_symbol)


def get_data(board: chess.Board, move: chess.Move) -> MoveData:
    """
    Gathers data for a single move, including from/to squares and piece identity.
    Handles special moves such as castling and en passant.
    """
    from_square_idx = move.from_square
    to_square_idx = move.to_square

    from_squares = [from_square_idx]
    to_squares = [to_square_idx]
    targets = [get_piece_idx(board, move)]

    move_data: MoveData = {
        "sans": [board.san(move)],
        "from_": from_squares,
        "to": to_squares,
        "targets": targets
    }
    return move_data


def combine_data(move1_data: MoveData, move2_data: MoveData) -> MoveData:
    """
    Combines data from two sequential moves, avoiding overlapping squares.

    Args:
        move1_data (MoveData): Output of get_data for the first move.
        move2_data (MoveData): Output of get_data for the second move.

    Returns:
        MoveData: A merged move data dictionary with cleaned `from`, `to`, and `targets` lists.
    """
    bad_squares = move2_data["from_"] + move2_data["to"]
    from1 = [x for x in move1_data["from_"] if x not in bad_squares]
    
    to1 = []
    targets1 = []
    for i in range(len(move1_data["to"])):
        if move1_data["to"][i] in bad_squares:
            continue
        to1.append(move1_data["to"][i])
        targets1.append(move1_data["targets"][i])
    
    from_combined = from1 + move2_data["from_"]
    to_combined = to1 + move2_data["to"]
    targets_combined = targets1 + move2_data["targets"]
    
    data: MoveData = {
        "sans": [move1_data["sans"][0], move2_data["sans"][0]],
        "from_": from_combined,
        "to": to_combined,
        "targets": targets_combined
    }
    
    return data


def get_moves_pairs(board: chess.Board) -> List[Dict[str, object]]:
    """
    Generates all legal move pairs from the current board position.

    For each legal move (move1), all legal responses (move2) are computed
    and returned along with combined move data.

    Args:
        board (chess.Board): The current chess position.

    Returns:
        List[Dict[str, object]]: List of dictionaries with structure:
            - 'move1': data from the first move
            - 'move2': data from the second move (or None if no legal replies)
            - 'moves': combined move data (or None if no legal replies)
    """
    moves_pairs = []
    
    for move1 in list(board.legal_moves):  
        move1_data = get_data(board, move1)  
        board.push(move1)  # Make the first move
        done = True

        for move2 in list(board.legal_moves):  
            move2_data = get_data(board, move2)
            moves_data = combine_data(move1_data, move2_data)
            moves_pairs.append({
                "move1": move1_data,
                "move2": move2_data,
                "moves": moves_data
            })
            done = False  

        if done:  
            moves_pairs.append({
                "move1": move1_data,
                "move2": None,
                "moves": None
            })

        board.pop()  # Undo the first move
    
    return moves_pairs


def san_to_lan(board: chess.Board, san: str) -> str:
    """
    Converts a SAN move string to a LAN format by pushing the move to the board and then converting it.

    Args:
        board (chess.Board): A chess board object (e.g., from python-chess).
        san (str): A move in SAN (Standard Algebraic Notation) format.

    Returns:
        str: The corresponding move in LAN (Long Algebraic Notation) format.
    """
    board.push_san(san)
    history = board.move_stack
    lan = history[-1].uci()
    board.pop()
    return lan


def calculate_move_score(state: np.ndarray, move: MoveData, from_thr: float = 0.6, to_thr: float = 0.6) -> float:
    """
    Calculates the score for a given move based on the state of the game.

    Args:
        state (np.ndarray): The current game state (64x12 array).
        move (MoveData): A dictionary containing information about the move ('from', 'to', and 'targets').
        from_thr (float): Threshold for scoring the 'from' squares. Default is 0.6.
        to_thr (float): Threshold for scoring the 'to' squares. Default is 0.6.

    Returns:
        float: The calculated score for the move.
    """
    score = 0
    for square in move['from_']:
        score += 1 - max(state[int(square)]) - from_thr
    
    for i in range(len(move['to'])):
        score += state[move['to'][i]][move['targets'][i]] - to_thr
    
    return score
