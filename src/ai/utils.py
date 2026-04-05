import math
from typing import List, Tuple
from copy import deepcopy

from src.core.board import TriangleBoard

MovePath = List[Tuple[int, int]]

def clone_board(board: TriangleBoard) -> TriangleBoard:
    ''' Clone board to avoid modifying the original board when applying moves in AI algorithms '''
    new_board = TriangleBoard(board.size)
    new_board.board = deepcopy(board.board)
    return new_board

def move_score(move: MovePath) -> float:
    '''Đánh giá một move path dựa trên độ dài và số lần jump'''
    # độ dài path
    length = len(move)

    # số lần jump (mỗi bước >1 ô là jump)
    jumps = 0
    for i in range(1, len(move)):
        r1, c1 = move[i-1]
        r2, c2 = move[i]
        if abs(r2 - r1) == 2 or abs(c2 - c1) == 2:
            jumps += 1

    return length + jumps * 2  # trọng số jump mạnh hơn

def sigmoid(x):
    return 1 / (1 + math.exp(-x))