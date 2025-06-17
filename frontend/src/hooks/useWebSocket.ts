import { useEffect, useState } from "react";

/**
 * Custom React Hook: useWebSocket
 *
 * This hook establishes a WebSocket connection to the provided URL and listens for incoming messages.
 * It maintains a list of chess moves (as strings) and updates the state based on messages received.
 *
 * @param url - The WebSocket server URL
 * @returns an array of move strings representing the game's move history
 */

export function useWebSocket(url: string) {
  const [moves, setMoves] = useState<string[]>([]); // State to store list of received moves

  useEffect(() => {
    setMoves([]);  // Clear moves when component (re)mounts or URL changes
    const socket = new WebSocket(url); // Open a new WebSocket connection

    // Handle incoming messages from the server
    socket.onmessage = (event) => {
      switch (event.data) {
        case "RESET":
          // If a RESET signal is received, clear the move history
          setMoves([]);
          break;

        case "INVALID":
          // If an INVALID signal is received, do nothing (or optionally handle invalid move logic)e
          break;

        default:
          // For any other message, treat it as a valid move and append to the move list
          setMoves((prevMoves) => [...prevMoves, event.data]);
      }
    };

    // Cleanup function to close the WebSocket connection when the component unmounts or URL changes
    return () => socket.close();

  }, [url]);

  // Return the list of moves to the component using this hook
  return moves;
}

export function useFenWebSocket(url: string) {
  const [fen, setFen] = useState<string | null>(null);

  useEffect(() => {
    const socket = new WebSocket(url);

    socket.onmessage = (event) => {
      // The fen endpoint sends "FEN:<fenstring>"
      if (event.data.startsWith("FEN:")) {
        setFen(event.data.slice(4));
      }
    };

    return () => socket.close();
  }, [url]);

  return fen;
}