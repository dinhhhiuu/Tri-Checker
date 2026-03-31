---

agent: agent
model: GPT-5.3-Codex (copilot)
---

## Task: Build a 3-Player Triangle Board Game with Capture Mechanics (Python + Pygame + AI + ML)

### Objective

Develop a turn-based triangular board game inspired by Star Checkers, modified with **capture mechanics**.
The game supports 3 players (1 human + 2 AI), includes multiple AI strategies, and integrates Machine Learning for board evaluation.

---

### Game Setup

#### Board

* Use a triangular board layout.
* Board size: 10 rows (triangle shape).
* Total 3 players:

  * Player 1 (Human)
  * Player 2 (AI)
  * Player 3 (AI)
* Each player starts with 10 pieces positioned in 3 corners:

  * Top (Player 1)
  * Bottom-left (Player 2)
  * Bottom-right (Player 3)

---

### Game Mechanics

* Turn-based gameplay:

  ```
  Player 1 → Player 2 → Player 3 → repeat
  ```

#### Movement Rules

1. Move to adjacent empty cell.
2. Jump over a neighboring piece into an empty cell.
3. Allow multi-jump (chain jumps in a single turn).
4. Movement directions follow triangular grid adjacency.

---

### Capture Rules (IMPORTANT)

* Jumping over a piece behaves as follows:

| Type of Piece Jumped Over | Result                                              |
| ------------------------- | --------------------------------------------------- |
| Same player (ally)        | No effect                                           |
| Opponent piece            | Opponent piece is **captured (removed from board)** |

* Capture occurs **during each jump step**, including multi-jump chains.

---

### Win Condition (MODIFIED)

* A player wins when:

```
They are the LAST player with at least one remaining piece.
```

* The game ends immediately when only one player has pieces left.

---

### User Interface (Pygame)

* Render triangular board using coordinate mapping.
* Display 3 different piece colors.
* Mouse interaction:

  * Click to select a piece
  * Click a valid position to move
* Highlight:

  * Selected piece
  * All reachable path positions (including multi-jump)
* Display winner clearly when game ends.

---

### AI Requirements

#### 1. Random AI

* Select a random valid move from all possible moves.

---

#### 2. Minimax AI

* Implement depth-limited Minimax.
* Adapt for **3-player turn cycle**.
* Evaluation function should consider:

  * Number of remaining pieces (IMPORTANT)
  * Potential captures
  * Mobility (number of valid moves)

---

#### 3. Monte Carlo Tree Search (MCTS)

* Implement:

  * Selection
  * Expansion
  * Simulation (random playout)
  * Backpropagation
* Support multi-player environment.
* Reward:

  * +1 for win
  * 0 for loss

---

### Machine Learning Requirement

#### Goal

Train a model to evaluate board states based on winning probability.

---

#### Data Generation (Self-play)

* Simulate games using AI (Random / MCTS).
* For each state, store:

  * Flattened board state
  * Game outcome (win = 1, loss = 0)

---

#### Model Training

* Use a lightweight model (e.g., `MLPClassifier` from scikit-learn).
* Input: board state vector
* Output: probability of winning

---

#### Integration

* Replace Minimax evaluation with:

  ```
  model.predict(board_state)
  ```
* Ensure inference is fast enough for real-time gameplay.

---

### Architecture Requirements

Organize code into modules:

* `board.py` → board structure and game rules
* `moves.py` → move generation and jump logic
* `game.py` → turn handling and game state
* `ai/`

  * `random_ai.py`
  * `minimax_ai.py`
  * `mcts_ai.py`
* `ml/`

  * `generate_data.py`
  * `train_model.py`
  * `model_loader.py`
* `ui/`

  * `pygame_renderer.py`

---

### Save / Load Feature

* Save game state to JSON file.
* Load saved game and resume.

---

### Constraints

* Use Python and Pygame.
* Use scikit-learn for ML.
* Limit AI computation:

  * Minimax depth ≤ 3
  * MCTS simulations ≤ 1000
* Ensure smooth gameplay (no frame freezing).

---

### Success Criteria

* Game runs smoothly without lag.
* Human interaction is responsive.
* Turn system works correctly (3 players).
* Capture mechanics work correctly.
* Multi-jump with capture works.
* AI behaves correctly.
* ML model is trained and used.
* Winner detection is accurate.
* Save/load works.

---

### Optional Enhancements

* Difficulty levels:

  * Easy: Random
  * Medium: Minimax
  * Hard: MCTS + ML
* Animations for movement and capture
* Sound effects
* UI polish

---

### Expected Output

* Fully functional Python + Pygame project
* 3-player gameplay with capture mechanics
* AI (Random, Minimax, MCTS)
* ML pipeline (data → training → inference)
* Clean, modular, extensible codebase
