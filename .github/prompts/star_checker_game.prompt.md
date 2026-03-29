---
agent: agent
model: GPT-5.3-Codex (copilot)
---

## Task: Build a 3-Player Star Checkers Game (Triangle Board) with AI and Machine Learning (Python + Pygame)

### Objective

Develop a turn-based board game inspired by Star Checkers variant using Python and Pygame. The game must support 3 players (1 human + 2 AI), include multiple AI strategies, and integrate a Machine Learning component for board evaluation.

---

### Game Setup

#### Board

* Use a triangular board layout (not square grid).
* Each corner of the triangle represents a player’s starting zone.
* Total 3 players:

  * Player 1 (Human)
  * Player 2 (AI)
  * Player 3 (AI)
* Each player starts with 10 pieces in their own corner.

---

### Game Mechanics

* Turn-based gameplay: Player → AI1 → AI2 → repeat.
* No capturing mechanics.
* Valid moves:

  1. Move to adjacent empty cell.
  2. Jump over any piece (own or opponent) into an empty cell.
  3. Allow multi-jump (chain jumps in a single turn).
* Pieces can jump in any valid direction allowed by the triangular grid.

---

### Win Condition

* A player wins when all 10 pieces reach the target corner (opposite side of the triangle).

---

### User Interface (Pygame)

* Render triangular board visually (using coordinates or offset grid).
* Display 3 types of pieces with different colors.
* Mouse interaction (for human player):

  * Click to select a piece
  * Click to move
* Highlight:

  * Selected piece
  * Valid moves
* Display winner at end of game.

---

### AI Requirements

#### 1. Random AI

* Select a random valid move.

#### 2. Minimax AI

* Implement Minimax with depth limit.
* Evaluation function should consider:

  * Distance to target zone
  * Piece clustering / blocking
* Adapt Minimax for multi-player (3-player turn cycle).

#### 3. Monte Carlo Tree Search (MCTS)

* Implement:

  * Selection
  * Expansion
  * Simulation (random rollout)
  * Backpropagation
* Support multi-player simulation.
* Run multiple simulations per move.

---

### Machine Learning Requirement

#### Goal

Use Machine Learning to evaluate board states and improve AI performance.

---

#### Data Generation (Self-play)

* Simulate games using AI (Random / MCTS).
* For each move, store:

  * Board state (flattened representation)
  * Game result (win = 1, others = 0 or -1)

---

#### Model Training

* Use a simple model (e.g., MLPClassifier from scikit-learn).
* Input: board state
* Output: score or win probability

---

#### Integration

* Replace Minimax evaluation function with ML prediction:

  * model.predict(board_state)
* Ensure inference is fast.

---

### Architecture Requirements

Organize code into modules:

* board.py → board structure (triangular grid)
* moves.py → move generation and jump logic
* game.py → turn handling (3 players)
* ai/

  * random_ai.py
  * minimax_ai.py
  * mcts_ai.py
* ml/

  * generate_data.py
  * train_model.py
  * model_loader.py
* ui/

  * pygame_renderer.py

---

### Save / Load Feature

* Save game state to JSON.
* Load saved game and continue playing.

---

### Constraints

* Use Python and Pygame only.
* Use lightweight ML (scikit-learn).
* Avoid long computation time (limit AI depth and simulations).
* Ensure clean and modular code.

---

### Success Criteria

* Game runs without crashes.
* Human player can interact smoothly.
* 3-player turn system works correctly.
* All AI types function correctly.
* Multi-jump logic works.
* ML model is trained and used.
* Win condition is correctly detected.
* Save/load works.

---

### Optional Enhancements

* Difficulty levels (Easy = Random, Medium = Minimax, Hard = MCTS + ML)
* Basic animations
* Sound effects
* UI improvements

---

### Expected Output

* Fully functional Python + Pygame project
* 3-player gameplay (1 human + 2 AI)
* Integrated AI (Random, Minimax, MCTS)
* Machine Learning pipeline (data → training → inference)
* Modular and extensible codebase