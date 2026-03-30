import pygame
import sys
from src.core.board import TriangleBoard
from src.ui.config import WIDTH, HEIGHT
from src.ui.pygame_renderer import get_cell_from_mouse, draw, apply_move, draw_winner, draw_menu, draw_settings

MODES = ("player", "random", "minimax", "mcts")

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

    clock = pygame.time.Clock()

    state = "menu"  # 'menu' | 'settings' | 'game'

    # settings (store only; not used for AI yet)
    player_modes = {1: "player", 2: "player", 3: "player"}

    # game state (created on Play)
    board = None
    selected = None
    valid_moves = []
    winner = None
    game_over = False

    def start_game():
        nonlocal board, selected, valid_moves, winner, game_over
        board = TriangleBoard()
        init_players(board)
        selected = None
        valid_moves = []
        winner = None
        game_over = False

    # Menu UI rects
    btn_w, btn_h = 280, 64
    btn_x = (WIDTH - btn_w) // 2
    btn_y0 = HEIGHT // 2 - 80
    play_rect = pygame.Rect(btn_x, btn_y0, btn_w, btn_h)
    setting_rect = pygame.Rect(btn_x, btn_y0 + 90, btn_w, btn_h)
    exit_rect = pygame.Rect(btn_x, btn_y0 + 180, btn_w, btn_h)

    # Settings UI rects
    back_rect = pygame.Rect(24, 24, 140, 52)
    mode_rects = {
        1: pygame.Rect(WIDTH // 2 - 220, HEIGHT // 2 - 60, 440, 52),
        2: pygame.Rect(WIDTH // 2 - 220, HEIGHT // 2 + 10, 440, 52),
        3: pygame.Rect(WIDTH // 2 - 220, HEIGHT // 2 + 80, 440, 52),
    }

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if state == "menu":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if play_rect.collidepoint(event.pos):
                        start_game()
                        state = "game"
                    elif setting_rect.collidepoint(event.pos):
                        state = "settings"
                    elif exit_rect.collidepoint(event.pos):
                        pygame.quit()
                        sys.exit()

            elif state == "settings":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if back_rect.collidepoint(event.pos):
                        state = "menu"
                        continue

                    for p in (1, 2, 3):
                        if mode_rects[p].collidepoint(event.pos):
                            current = player_modes[p]
                            idx = MODES.index(current) if current in MODES else 0
                            player_modes[p] = MODES[(idx + 1) % len(MODES)]
                            break

            elif state == "game":
                if game_over:
                    continue

                if event.type == pygame.MOUSEBUTTONDOWN:
                    cell = get_cell_from_mouse(event.pos, board)

                    if not cell:
                        continue

                    r, c = cell

                    # chọn quân (giữ logic hiện tại: chỉ cho Player 1)
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

        if state == "menu":
            draw_menu(screen, play_rect, setting_rect, exit_rect)
            clock.tick(60)
            continue

        if state == "settings":
            draw_settings(screen, back_rect, mode_rects, player_modes)
            clock.tick(60)
            continue

        # state == 'game'
        if not game_over:
            winner = board.check_winner()
            if winner:
                game_over = True

        draw(screen, board, selected, valid_moves, flip=False)
        if game_over and winner:
            draw_winner(screen, winner, flip=False)
        pygame.display.flip()

        clock.tick(60)

if __name__ == "__main__":
    main()