import "./evalBar.css";

import React from "react";

/**
 * EvalBar Component
 *
 * Visually represents a chess engine's evaluation for a given board state.
 * The bar fills from bottom to top to indicate White's advantage,
 * or from top to bottom for Black's advantage.
 */

/**
 * Props for the EvalBar component
 * - `evaluation`: Numeric centipawn evaluation, string for "N/A", or null if not available
 * - `mate`: Number representing "mate in N" (positive for White, negative for Black), or null
 * - `id`: Optional identifier (not used internally but may be passed from a parent)
 */
interface EvalBarProps {
  evaluation: string | number | null;
  mate: number | null;
  id: string | undefined;
}
const EvalBar: React.FC<EvalBarProps> = ({ evaluation, mate }) => {
  const isMate = mate !== null && mate !== 0; // Determine if there's a mate, if mate is provided and is a valid number

  /**
   * Choose the text to display inside the evaluation bar:
   * - If a mate is detected, show M1, M3, -M2, etc.
   * - If evaluation is a number, show the numeric value
   * - Otherwise, render an empty string
   */
  const displayValue = isMate 
  ? `${mate! > 0 ? '' : '-'}M${Math.abs(mate!)}`
  : (evaluation !== null && typeof evaluation === 'number' ? evaluation.toString() : "");

  /**
   * Calculate the percentage of the bar to fill from the bottom (White's advantage).
   * - Mate in 1 → 100% or 0% instantly
   * - Evaluation is clamped to [-10, 10] and mapped to [0%, 100%] with 0 eval = 50%
   * - If invalid or unavailable, default to 50% (neutral)
   */
  const whitePercentage = (() => {
    if (isMate) {
      return mate! > 0 ? 100 : 0;
    }
  
    if (evaluation === null || typeof evaluation !== 'number') return 50;
  
    const clamped = Math.max(-10, Math.min(10, evaluation));
    return 50 + clamped * 5;
  })();
  

const useBlackText = whitePercentage > 50;

  return (
    <div className="eval-bar">
      <div
        className="white-bar"
        style={{ height: `${whitePercentage}%` }}
      />
      <div
        className="black-bar"
        style={{ height: `${100 - whitePercentage}%` }}
      />
      <div className={`eval-text ${useBlackText ? 'black-text' : 'white-text'}`}>
        {displayValue}
      </div>
    </div>
  );
};



export default EvalBar;
