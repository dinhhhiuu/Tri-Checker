from __future__ import annotations
import math
import random
import time
from typing import List, Optional

from src.core.board import TriangleBoard
from src.core.utils import next_player, get_all_moves_for_player
from src.core.move import apply_move
from src.ai.utils import MovePath, clone_board, move_score, sigmoid

class MCTSNode:
    '''Node trong cây MCTS'''
    def __init__(self, board: TriangleBoard, player: int, parent=None, move=None):
        self.board = board
        self.player = player  

        self.parent = parent
        self.move = move

        self.children: List[MCTSNode] = []
        self.visits = 0
        self.value = 0.0 

        self.untried_moves = get_all_moves_for_player(board, player)

    def is_fully_expanded(self):
        return len(self.untried_moves) == 0

    def best_child(self, c=1.4):
        best_score = -float('inf')
        best_node = None

        for child in self.children:
            if child.visits == 0:
                return child

            exploit = child.value / child.visits
            explore = c * math.sqrt(math.log(self.visits) / child.visits)
            score = exploit + explore

            if score > best_score:
                best_score = score
                best_node = child

        return best_node

def rollout(board: TriangleBoard, player: int, max_depth: int = 100) -> tuple[float, int]:
    '''Thực hiện một rollout từ board hiện tại và trả về kết quả'''
    sim_board = clone_board(board)
    current_player = player

    for step in range(max_depth):
        winner = sim_board.check_winner()
        if winner is not None:
            if winner == player:
                return 1.0, step
            else:
                return 0.0, step

        moves = get_all_moves_for_player(sim_board, current_player)
        if not moves:
            # No moves available, current player loses
            return 0.0 if current_player == player else 1.0, step

        # Early evaluation if game is in late stages (few pieces left)
        total_pieces = sum(len(sim_board.get_all_pieces(p)) for p in [1, 2, 3])
        if total_pieces <= 6 and step > 10:  # Late game heuristic
            return evaluate_for_mcts(sim_board, player), step

        # Choose move randomly (standard MCTS rollout)
        move = random.choice(moves)
        apply_move(sim_board, move)

        current_player = next_player(current_player)

    # heuristic evaluation
    return evaluate_for_mcts(sim_board, player), max_depth

def move_score_final(board, move, player):
    # local
    s1 = move_score(move)

    # global
    new_board = clone_board(board)
    apply_move(new_board, move)
    s2 = evaluate_for_mcts(new_board, player)

    return s1 * 0.3 + s2 * 0.7

def evaluate_for_mcts(board: TriangleBoard, player: int) -> float:
    scores = {}

    for p in [1, 2, 3]:
        my_pieces = board.get_all_pieces(p)
        my_count = len(my_pieces)

        enemies = [e for e in [1,2,3] if e != p]
        enemy_count = sum(len(board.get_all_pieces(e)) for e in enemies)

        score = 0

        # piece count with higher weight
        score += my_count * 15
        score -= enemy_count * 8

        # mobility with jump bonus
        moves = 0
        jump_moves = 0
        for (r, c) in my_pieces:
            piece_moves = board.get_all_moves(r, c)
            moves += len(piece_moves)
            # Count jumps (paths longer than 2 positions)
            jump_moves += sum(1 for move in piece_moves if len(move) > 2)

        score += moves * 3
        score += jump_moves * 10  # Bonus for jump opportunities

        # Center control (lower rows are more valuable in triangular board)
        center_score = 0
        for (r, c) in my_pieces:
            # Weight pieces in lower rows more heavily
            row_weight = (r + 1) / board.size
            center_score += row_weight * 5
        score += center_score

        scores[p] = score

    my_score = scores[player]
    opp_score = max(scores[p] for p in scores if p != player)

    diff = my_score - opp_score

    # sigmoid with adjusted scaling
    return sigmoid(diff / (abs(diff) + 20))

def backpropagate(node: MCTSNode, result: float, depth: int = 0):
    '''Cập nhật giá trị và số lần visit cho node và tất cả ancestor của nó'''

    while node is not None:
        node.visits += 1
        node.value += result
        node = node.parent

def choose_mcts_move(board: TriangleBoard, player: int, mode: str, simulations: int = 2000, time_limit: float = 0.5) -> Optional[MovePath]:
    if mode != "mcts":
        raise ValueError(f"Invalid mode for choose_mcts_move: {mode}")

    root = MCTSNode(clone_board(board), player)
    start_time = time.time()

    sim_count = 0
    while sim_count < simulations and (time.time() - start_time) < time_limit:
        node = root

        # -------- SELECT --------
        while node.is_fully_expanded() and node.children:
            node = node.best_child()

        # -------- EXPAND --------
        if node.untried_moves:
            node.untried_moves.sort(key=move_score, reverse=True)
            move = node.untried_moves.pop(0)

            new_board = clone_board(node.board)
            apply_move(new_board, move)

            next_p = next_player(node.player)

            child = MCTSNode(new_board, next_p, parent=node, move=move)
            node.children.append(child)
            node = child

        # -------- SIMULATE --------
        result, depth = rollout(node.board, player, max_depth=100)

        # -------- BACKPROP --------
        backpropagate(node, result, depth)

        sim_count += 1

    if not root.children:
        return None

    # chọn move tốt nhất
    best_child = max(root.children, key=lambda n: n.visits + n.value / n.visits if n.visits > 0 else 0)
    return best_child.move