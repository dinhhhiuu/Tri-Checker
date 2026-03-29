import pygame
from src.ui.config import WIDTH, RADIUS, GAP, COLORS

# MAP BOARD TO SCREEN
def get_screen_pos(row, col):
    start_x = WIDTH // 2
    start_y = 100

    x = start_x + (col - row / 2) * GAP
    y = start_y + row * GAP

    return int(x), int(y)

# FIND CELL FROM CLICK
def get_cell_from_mouse(pos, board):
    mx, my = pos

    for r in range(board.size):
        for c in range(r + 1):
            x, y = get_screen_pos(r, c)

            if (mx - x)**2 + (my - y)**2 <= RADIUS**2:
                return (r, c)

    return None

# DRAW
def draw(screen, board, selected, moves):
    screen.fill((30, 30, 30))

    for r in range(board.size):
        for c in range(r + 1):
            x, y = get_screen_pos(r, c)
            piece = board.board[r][c]

            pygame.draw.circle(screen, COLORS[piece], (x, y), RADIUS)

    # highlight selected
    if selected:
        x, y = get_screen_pos(*selected)
        pygame.draw.circle(screen, (0,255,0), (x,y), RADIUS+5, 3)

    # highlight moves
    for path in moves:
        for (r, c) in path[1:]:   # bỏ điểm đầu
            x, y = get_screen_pos(r, c)
            pygame.draw.circle(screen, (255, 255, 0), (x, y), 8)

    pygame.display.flip()

# APPLY MOVE
def apply_move(board, path):
    ''' Swap piece from start to end '''
    start = path[0]
    end = path[-1]

    piece = board.board[start[0]][start[1]]
    board.board[start[0]][start[1]] = 0
    board.board[end[0]][end[1]] = piece
    