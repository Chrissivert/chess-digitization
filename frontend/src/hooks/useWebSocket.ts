import { useEffect, useState } from "react";

export function useWebSocket(url: string) {
  const [moves, setMoves] = useState<string[]>([]);
  const [fen, setFen] = useState<string | null>(null);  // new state for FEN

  useEffect(() => {
    setMoves([]);
    setFen(null);

    const socket = new WebSocket(url);

    socket.onmessage = (event) => {
      const data = event.data;

      if (data.startsWith("FEN:")) {
        // Extract FEN string and update fen state
        setFen(data.slice(4));
      } else if (data === "RESET") {
        setMoves([]);
        setFen(null);
      } else if (data === "INVALID") {
        // handle invalid move if needed
      } else if (data.startsWith("MOVE:")) {
        // Extract move string and append it to moves
        setMoves((prevMoves) => [...prevMoves, data.slice(5)]);
      } else {
        // fallback: treat it as move if no prefix
        setMoves((prevMoves) => [...prevMoves, data]);
      }
    };

    return () => socket.close();
  }, [url]);

  // Return both fen and moves to be used by your component
  return { fen, moves };
}
