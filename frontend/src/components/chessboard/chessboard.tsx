import "./chessboard.css";

import { forwardRef, useImperativeHandle, useEffect, useState, useRef } from "react";
import { Chess } from "chess.ts";
import Tile from "../tile/tile";
import { useWebSocket } from "../../hooks/useWebSocket";
import { useFenWebSocket } from "../../hooks/useWebSocket";


/**
 * Chessboard Component
 *
 * This component renders a full chessboard UI and manages game state using `chess.ts`.
 * It receives move updates via WebSocket, updates board position accordingly,
 * highlights the most recent move, and exposes its move list to parent components via ref.
 */

// Represents a single piece's position and image
interface Piece {
  image: string;
  x: number;
  y: number;
}

/**
 * Converts a FEN string into an array of Piece objects.
 * Maps chess notation characters to piece image paths and coordinates.
 * The y-coordinate is flipped to align with visual board orientation.
 */

function generatePositionFromFen(fen: string): Piece[] {
  const board = fen.split(" ")[0];
  const rows = board.split("/");
  const pieceMap: { [key: string]: string } = {
    p: "pawn_b", P: "pawn_w",
    r: "rook_b", R: "rook_w",
    n: "knight_b", N: "knight_w",
    b: "bishop_b", B: "bishop_w",
    q: "queen_b", Q: "queen_w",
    k: "king_b", K: "king_w",
  };

  const pieces: Piece[] = [];

  // Parse the FEN rows (from top to bottom)
  for (let y = 0; y < rows.length; y++) {
    let x = 0;
    for (const char of rows[y]) {
      if (isNaN(Number(char))) {
        const image = `/assets/images/${pieceMap[char]}.svg`;
        pieces.push({ image, x, y: 7 - y }); // Flip y to match board orientation
        x++;
      } else {
        x += parseInt(char);
      }
    }
  }

  return pieces;
}

/**
 * Props for Chessboard
 * - `id`: Unique ID for the board, used in WebSocket connection
 */
interface ChessboardProps {
  id: string | undefined;
}

/**
 * Ref interface exposed by the Chessboard component.
 *
 * This allows parent components to access certain chess game data
 * directly through the component's reference using `useImperativeHandle`.
 *
 * Methods exposed:
 * - `getMoves()`: Returns a list of SAN (Standard Algebraic Notation) moves
 * - `getFEN()`: Returns the current board state in Forsyth–Edwards Notation
 * - `getPGN()`: Returns the full move history in PGN (Portable Game Notation) format
 */
export interface ChessboardHandle {
  getMoves: () => string[];
  getFEN: () => string;
  getPGN: () => string;
}

const Chessboard = forwardRef<ChessboardHandle, ChessboardProps>(({ id }, ref) => {
  const [pieces, setPieces] = useState<Piece[]>([]);
  const [moveList, setMoveList] = useState<string[]>([]);
  const [lastMoveSquares, setLastMoveSquares] = useState<string[]>([]);
  const moves = useWebSocket(`ws://localhost:8000/moves/${id}`);
  const fenFromWebSocket = useFenWebSocket(`ws://localhost:8000/fen/${id}`);

  console.log(fenFromWebSocket);
  console.log("fenfromwebsocket")

   const START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
  const chessRef = useRef(new Chess(fenFromWebSocket ?? START_FEN));

  console.log(chessRef.current.fen());
  console.log("chessref current fen")

  const chess = chessRef.current;


  /**
   * Expose internal chess game data to the parent component via `ref`.
   *
   * This allows external access to:
   * - The move history
   * - The current FEN string
   * - The full PGN history
   */
  useImperativeHandle(ref, () => ({
    getMoves: () => moveList,
    getFEN: () => chess.fen(),
    getPGN: () => chess.pgn(),
  }));
  
  /**
   * Initializes the board on first render using the current FEN from `chess.ts`.
   * Also exposes a helper `makeMove` function to the browser console for debugging.
   * 
   * NOTE: Used for testing the board manually through console input.
   */
  useEffect(() => {
    setPieces(generatePositionFromFen(chess.fen()));

    // Expose move handler for console
    (window as any).makeMove = (notation: string) => {
      const move = chess.move(notation);
      if (move) {
        setPieces(generatePositionFromFen(chess.fen()));
        setMoveList((prev) => [...prev, move.san]);

        let highlights: string[] = [];

        if (move.san === "O-O") {
          highlights = [move.from, move.color === "w" ? "h1" : "h8"];
        } else if (move.san === "O-O-O") {
          highlights = [move.from, move.color === "w" ? "a1" : "a8"];
        } else {
          highlights = [move.from, move.to];
        }

        setLastMoveSquares(highlights);
      } else {
        console.warn("Illegal move:", notation);
      }
    };
  }, []);

  /**
   * Apply all moves received from the WebSocket.
   * Valid moves are added to the move list and used to update the board.
   * The most recent move's squares are tracked for highlighting.
   */
  useEffect(() => {
    chess.load(chess.fen()); // Reset the chess instance to the starting position

    console.log(chess.fen());
    console.log("See above");

    if (!moves || moves.length === 0) {
      setMoveList([]);
      setLastMoveSquares([]);
      setPieces(generatePositionFromFen(chess.fen()));
      return;
    }

    const validSanMoves: string[] = [];

    // Attempt to apply each move to the chess instance
    moves.forEach((notation) => {
      const move = chess.move(notation);
      if (move) {
        validSanMoves.push(move.san);
      } else {
        console.warn("Illegal move from WebSocket:", notation);
      }
    });

    setMoveList(validSanMoves);

    if (validSanMoves.length > 0) {
      const history = chess.history({ verbose: true });
      const move = history[history.length - 1];
      if (move) {
        let highlights: string[] = [];

        if (move.san === "O-O") {
          highlights = [move.from, move.color === "w" ? "h1" : "h8"];
        } else if (move.san === "O-O-O") {
          highlights = [move.from, move.color === "w" ? "a1" : "a8"];
        } else {
          highlights = [move.from, move.to];
        }

        setLastMoveSquares(highlights);
      }
      setPieces(generatePositionFromFen(chess.fen()));
    }
  }, [moves]);

  const verticalAxis = ["1", "2", "3", "4", "5", "6", "7", "8"];
  const horizontalAxis = ["a", "b", "c", "d", "e", "f", "g", "h"];
  const board = [];


   /**
   * Generates the full 8x8 chessboard as a grid of tiles.
   * Each tile receives a piece image if one exists at its (x, y) coordinate.
   */
  for (let j = verticalAxis.length - 1; j >= 0; j--) {
    for (let i = 0; i < horizontalAxis.length; i++) {
      const number = j + i + 2;
      let image = undefined;

      pieces.forEach((p) => {
        if (p.x === i && p.y === j) {
          image = p.image;
        }
      });

      const square = `${horizontalAxis[i]}${verticalAxis[j]}`;
      const isHighlighted = lastMoveSquares.includes(square);

      board.push(
        <Tile
          key={`${j},${i}`}
          image={image}
          number={number}
          highlight={isHighlighted}
        />
      );
    }
  }

  return (
    <div id="chessboard">
      {board}
    </div>
  );
});

export default Chessboard;