from __future__ import annotations
import math
import random
from typing import List, Optional

from src.core.board import TriangleBoard
from src.core.utils import next_player, get_all_moves_for_player
from src.core.move import apply_move
from src.ai.utils import MovePath, clone_board, move_score, sigmoid

class MCTSNode:
    '''Nodes in the MCTS tree'''
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

def rollout(board: TriangleBoard, player: int, max_depth: int = 500) -> tuple[float, int]:
    '''Perform a rollout from the current board and return the result'''
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
            current_player = next_player(current_player)
            continue

        # bias chooses good moves
        if random.random() < 0.9: 
            top_moves = sorted(moves, key=move_score, reverse=True)[:5]
            move = max(top_moves, key=lambda m: move_score_final(sim_board, m, current_player))
        else:
            move = random.choice(moves)
        apply_move(sim_board, move)

        current_player = next_player(current_player)

    # heuristic
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

        # piece count
        score += my_count * 10
        score -= enemy_count * 6

        # mobility
        moves = 0
        for (r, c) in my_pieces:
            moves += len(board.get_all_moves(r, c))
        score += moves * 2

        scores[p] = score

    my_score = scores[player]
    opp_score = max(scores[p] for p in scores if p != player)

    diff = my_score - opp_score

    # sigmoid
    return sigmoid(diff / (abs(diff) + 10))

def backpropagate(node: MCTSNode, result: float, depth: int = 0):
    '''Update the value and number of visits for the node and all its ancestors.'''

    if result == 1.0:
        discount = 0.995 ** min(depth, 100)
    elif result == 0.0:
        discount = 1.0 - (0.995 ** min(depth, 100)) * 0.3
    else:
        discount = 1.0

    while node is not None:
        node.visits += 1
        node.value += result * discount
        node = node.parent

def choose_mcts_move(board: TriangleBoard, player: int, mode: str, simulations: int = 800) -> Optional[MovePath]:
    if mode != "mcts":
        raise ValueError(f"Invalid mode for choose_mcts_move: {mode}")

    root = MCTSNode(clone_board(board), player)

    for _ in range(simulations):
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
        result, depth = rollout(node.board, player, max_depth=800)

        # -------- BACKPROP --------
        backpropagate(node, result, depth)

    if not root.children:
        return None

    # choose the child with the most visits
    best_child = max(root.children, key=lambda n: n.visits + n.value / n.visits if n.visits > 0 else 0)
    return best_child.move