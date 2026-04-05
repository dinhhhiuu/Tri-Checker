import pygame
import sys

from src.core.board import TriangleBoard
from src.core.move import apply_move
from src.core.utils import next_player

from src.ui.config import WIDTH, HEIGHT, MODES
from src.ui.pygame_renderer import get_cell_from_mouse, draw, draw_winner, draw_menu, draw_settings, draw_pause, draw_hud, draw_ai_path, draw_human_path

from src.ai.random_ai import choose_random_move
from src.ai.minimax_ai import choose_minimax_move
from src.ai.mcts_ai import choose_mcts_move
from src.ai.ml_ai import choose_ml_move

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

    # settings (store only)
    player_modes = {1: "player", 2: "player", 3: "player"}

    # game state (created on Play)
    board = None
    selected = None
    valid_moves = []
    winner = None
    game_over = False
    turn = 1
    win_restart_rect = None
    win_menu_rect = None
    paused = False
    pause_continue_rect = None
    pause_menu_rect = None
    pause_quit_rect = None

    last_ai_path = None
    last_ai_player = None

    last_human_path = None
    last_human_player = None

    def start_game():
        nonlocal board, selected, valid_moves, winner, game_over, turn, win_restart_rect, win_menu_rect
        nonlocal paused, pause_continue_rect, pause_menu_rect, pause_quit_rect
        nonlocal last_ai_path, last_ai_player, last_human_path, last_human_player
        board = TriangleBoard()
        init_players(board)
        selected = None
        valid_moves = []
        winner = None
        game_over = False
        turn = 1
        win_restart_rect = None
        win_menu_rect = None
        paused = False
        pause_continue_rect = None
        pause_menu_rect = None
        pause_quit_rect = None

        last_ai_path = None
        last_ai_player = None

        last_human_path = None
        last_human_player = None

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
        human_moved_this_frame = False
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
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if win_restart_rect and win_restart_rect.collidepoint(event.pos):
                            start_game()
                        elif win_menu_rect and win_menu_rect.collidepoint(event.pos):
                            state = "menu"
                    continue

                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    paused = not paused
                    selected = None
                    valid_moves = []
                    continue

                if paused:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if pause_continue_rect and pause_continue_rect.collidepoint(event.pos):
                            paused = False
                        elif pause_menu_rect and pause_menu_rect.collidepoint(event.pos):
                            paused = False
                            state = "menu"
                        elif pause_quit_rect and pause_quit_rect.collidepoint(event.pos):
                            pygame.quit()
                            sys.exit()
                    continue

                # Only accept mouse input on the current player's turn,
                # and only if that player's mode is 'player'.
                if player_modes.get(turn, "player") != "player":
                    continue

                if event.type == pygame.MOUSEBUTTONDOWN:
                    cell = get_cell_from_mouse(event.pos, board)

                    if not cell:
                        continue

                    r, c = cell

                    # chọn quân (chỉ cho đúng player đang tới lượt)
                    if selected is None:
                        if board.board[r][c] == turn:
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
                            moved_player = turn
                            apply_move(board, chosen)
                            last_human_path = chosen
                            last_human_player = moved_player
                            turn = next_player(turn)
                            human_moved_this_frame = True
                            last_ai_path = None
                            last_ai_player = None

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
        if paused:
            draw(screen, board, selected, valid_moves, flip=False)
            if last_ai_path and last_ai_player:
                draw_ai_path(screen, last_ai_path, last_ai_player)
            elif last_human_path and last_human_player:
                draw_human_path(screen, last_human_path, last_human_player)
            draw_hud(screen, player_modes, turn)
            pause_continue_rect, pause_menu_rect, pause_quit_rect = draw_pause(screen, flip=False)
            pygame.display.flip()
            clock.tick(60)
            continue

        if not game_over:
            winner = board.check_winner()
            if winner:
                game_over = True

        # Apply non-player modes one move per frame.
        # If the human just moved, draw that move first (AI moves next frame)
        if not game_over and not human_moved_this_frame:
            mode = player_modes.get(turn, "player")

            # PLAYER -> không làm gì, chờ click
            if mode == "player":
                pass

            else:
                # When it's AI's turn, hide the last human path and only show AI path.
                last_human_path = None
                last_human_player = None

                move = None

                if mode == "random":
                    move = choose_random_move(board, turn, mode="random")

                elif mode == "minimax":
                    move = choose_minimax_move(board, turn, mode="minimax", depth=3, time_limit=0.3)

                elif mode == "mcts":
                    move = choose_mcts_move(board, turn, mode="mcts", simulations=2000, time_limit=0.3)

                elif mode == "ml":
                    move = choose_ml_move(board, turn, mode="ml")

                else:
                    raise ValueError(f"Unknown mode for player {turn}: {mode}")

                if move:
                    last_ai_path = move
                    last_ai_player = turn
                    apply_move(board, move)

                # reset UI state
                selected = None
                valid_moves = []

                # đổi lượt
                turn = next_player(turn)

        draw(screen, board, selected, valid_moves, flip=False)
        if last_ai_path and last_ai_player:
            draw_ai_path(screen, last_ai_path, last_ai_player)
        elif last_human_path and last_human_player:
            draw_human_path(screen, last_human_path, last_human_player)
        draw_hud(screen, player_modes, turn)
        if game_over and winner:
            win_restart_rect, win_menu_rect = draw_winner(screen, winner, flip=False)
        pygame.display.flip()

        clock.tick(60)


if __name__ == "__main__":
    main()