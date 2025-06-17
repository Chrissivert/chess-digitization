import { useEffect, useState } from "react";

export function useWebSocket(url: string) {
  const [startFen, setStartFen] = useState<string | null>(null);
  const [moves, setMoves] = useState<string[]>([]);

  useEffect(() => {
    setStartFen(null);
    setMoves([]);

    const socket = new WebSocket(url);

    socket.onmessage = (event) => {
      if (event.data.startsWith("FEN:")) {
        const fen = event.data.slice(4);
        setStartFen(fen);
        setMoves([]); // reset moves when new fen arrives
      } else if (event.data === "RESET") {
        setMoves([]);
      } else if (event.data === "INVALID") {
        // handle invalid move if needed
      } else {
        setMoves((prevMoves) => [...prevMoves, event.data]);
      }
    };

    return () => socket.close();
  }, [url]);

  return { startFen, moves };
}
