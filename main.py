import pygame
import sys
from src.core.board import TriangleBoard
from src.ui.config import WIDTH, HEIGHT
from src.ui.pygame_renderer import get_cell_from_mouse, draw, apply_move

# INIT PLAYER POSITIONS
def init_players(board):
    # Player 1 (top)
    for r in range(4):
        for c in range(r + 1):
            board._set_piece(r, c, 1)

    # Player 2 (bottom-left)
    for r in range(6, 10):
        for c in range(0, r - 5):
            board._set_piece(r, c, 2)

    # Player 3 (bottom-right)
    for r in range(6, 10):
        for c in range(6, r + 1):
            board._set_piece(r, c, 3)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Triangle Board Game")

    board = TriangleBoard()
    init_players(board)

    selected = None
    valid_moves = []

    while True:
        draw(screen, board, selected, valid_moves)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                cell = get_cell_from_mouse(event.pos, board)

                if not cell:
                    continue

                r, c = cell

                # chọn quân
                if selected is None:
                    if board.board[r][c] == 1:
                        selected = (r, c)
                        valid_moves = board.get_all_moves(r, c)

                else:
                    # check click vào move
                    chosen = None

                    for path in valid_moves:
                        if (r, c) in path[1:]:   # click vào bất kỳ điểm trong path
                            idx = path.index((r, c))
                            chosen = path[:idx + 1]   # cắt path tới điểm đó
                            break

                    if chosen:
                        apply_move(board, chosen)

                    selected = None
                    valid_moves = []

if __name__ == "__main__":
    main()