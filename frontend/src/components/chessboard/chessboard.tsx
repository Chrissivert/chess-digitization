import "./chessboard.css";

import { forwardRef, useImperativeHandle, useEffect, useState, useRef } from "react";
import { Chess } from "chess.ts";
import Tile from "../tile/tile";
import { useWebSocket } from "../../hooks/useWebSocket";
import { useFenWebSocket } from "../../hooks/useWebSocket";

interface Piece {
  image: string;
  x: number;
  y: number;
}

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

interface ChessboardProps {
  id: string | undefined;
}

export interface ChessboardHandle {
  getMoves: () => string[];
  getFEN: () => string;
  getPGN: () => string;
}

const Chessboard = forwardRef<ChessboardHandle, ChessboardProps>(({ id }, ref) => {
  const fenFromWebSocket = useFenWebSocket(`ws://localhost:8000/fen/${id}`);
  const moves = useWebSocket(`ws://localhost:8000/moves/${id}`);

  const [pieces, setPieces] = useState<Piece[]>([]);
  const [moveList, setMoveList] = useState<string[]>([]);
  const [lastMoveSquares, setLastMoveSquares] = useState<string[]>([]);
  const chessRef = useRef<Chess | null>(null);

  // Initialize chess only when fenFromWebSocket is valid (not null/undefined)
  useEffect(() => {
    if (!fenFromWebSocket) {
      return;
    }

    // Initialize chess instance with the current FEN
    chessRef.current = new Chess(fenFromWebSocket);
    const chess = chessRef.current;

    setPieces(generatePositionFromFen(chess.fen()));
    setMoveList([]);
    setLastMoveSquares([]);

    // Expose move handler for console debugging
    (window as any).makeMove = (notation: string) => {
      if (!chessRef.current) return;
      const move = chessRef.current.move(notation);
      if (move) {
        setPieces(generatePositionFromFen(chessRef.current.fen()));
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
  }, [fenFromWebSocket]);

  // Handle moves received from WebSocket once chess is initialized
  useEffect(() => {
    if (!chessRef.current) return;
    if (!moves || moves.length === 0) {
      setMoveList([]);
      setLastMoveSquares([]);
      setPieces(generatePositionFromFen(chessRef.current.fen()));
      return;
    }

    const chess = chessRef.current;
    // Reset chess to initial position before applying moves
    chess.load(fenFromWebSocket || chess.fen());

    const validSanMoves: string[] = [];

    console.log("Received moves from WebSocket:", moves);
    console.log("Current FEN:", chess.fen());
    console.log(validSanMoves)

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
  }, [moves, fenFromWebSocket]);

  useImperativeHandle(ref, () => ({
    getMoves: () => moveList,
    getFEN: () => chessRef.current?.fen() || "",
    getPGN: () => chessRef.current?.pgn() || "",
  }));

  if (!fenFromWebSocket) {
    // Optionally render a loading state while waiting for FEN
    return <div>Loading chessboard...</div>;
  }

  const verticalAxis = ["1", "2", "3", "4", "5", "6", "7", "8"];
  const horizontalAxis = ["a", "b", "c", "d", "e", "f", "g", "h"];
  const board = [];

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

  return <div id="chessboard">{board}</div>;
});

export default Chessboard;
