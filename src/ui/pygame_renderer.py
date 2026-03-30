import pygame
from src.ui.config import WIDTH, HEIGHT, RADIUS, GAP, COLORS

_WINNER_FONT = None
_MENU_TITLE_FONT = None
_MENU_BUTTON_FONT = None
_MENU_SMALL_FONT = None

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
def draw(screen, board, selected, moves, *, flip: bool = True):
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

    if flip:
        pygame.display.flip()

# APPLY MOVE
def apply_move(board, path):
    ''' Swap piece from start to end '''
    start = path[0]
    end = path[-1]

    piece = board.board[start[0]][start[1]]
    board.board[start[0]][start[1]] = 0
    board.board[end[0]][end[1]] = piece

def draw_winner(screen, winner, *, flip: bool = True): # sau dấu * là keyword-only argument, chỉ có thể truyền bằng tên khi gọi hàm
    global _WINNER_FONT

    if _WINNER_FONT is None:
        _WINNER_FONT = pygame.font.SysFont(None, 48)

    # Dim the whole screen
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    screen.blit(overlay, (0, 0))

    # screen.fill((0, 0, 0))  # xóa màn hình (màu đen)

    # Winner panel
    text = _WINNER_FONT.render(f"Player {winner} wins!", True, COLORS[winner])
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))

    padding = 24
    panel_rect = text_rect.inflate(padding * 2, padding * 2)

    panel = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
    panel.fill((30, 30, 30, 230))
    screen.blit(panel, panel_rect.topleft)
    pygame.draw.rect(screen, COLORS[winner], panel_rect, 3, border_radius=12)

    screen.blit(text, text_rect)
    if flip:
        pygame.display.flip()


def _get_menu_fonts():
    global _MENU_TITLE_FONT, _MENU_BUTTON_FONT, _MENU_SMALL_FONT

    if _MENU_TITLE_FONT is None:
        _MENU_TITLE_FONT = pygame.font.SysFont(None, 56)
    if _MENU_BUTTON_FONT is None:
        _MENU_BUTTON_FONT = pygame.font.SysFont(None, 44)
    if _MENU_SMALL_FONT is None:
        _MENU_SMALL_FONT = pygame.font.SysFont(None, 34)

    return _MENU_TITLE_FONT, _MENU_BUTTON_FONT, _MENU_SMALL_FONT


def _draw_button(screen, rect: pygame.Rect, label: str) -> None:
    _, btn_font, _ = _get_menu_fonts()
    pygame.draw.rect(screen, (200, 200, 200), rect, border_radius=12)
    pygame.draw.rect(screen, (255, 255, 0), rect, 2, border_radius=12)
    text = btn_font.render(label, True, (0, 0, 0))
    screen.blit(text, text.get_rect(center=rect.center))


def draw_menu(screen, play_rect, setting_rect, exit_rect, *, flip: bool = True) -> None:
    title_font, _, _ = _get_menu_fonts()
    screen.fill((30, 30, 30))

    title = title_font.render("Triangle Board Game", True, (255, 255, 255))
    screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 180)))

    _draw_button(screen, play_rect, "Play")
    _draw_button(screen, setting_rect, "Setting")
    _draw_button(screen, exit_rect, "Exit")

    if flip:
        pygame.display.flip()


def draw_settings(screen, back_rect, mode_rects, player_modes, *, flip: bool = True) -> None:
    title_font, _, small_font = _get_menu_fonts()
    screen.fill((30, 30, 30))

    title = title_font.render("Settings", True, (255, 255, 255))
    screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 160)))

    # Back button
    pygame.draw.rect(screen, (200, 200, 200), back_rect, border_radius=10)
    pygame.draw.rect(screen, (255, 255, 0), back_rect, 2, border_radius=10)
    back_text = small_font.render("Back", True, (0, 0, 0))
    screen.blit(back_text, back_text.get_rect(center=back_rect.center))

    # Mode selectors
    hint = small_font.render("Click to change mode", True, (200, 200, 200))
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 105)))

    for p in (1, 2, 3):
        rect = mode_rects[p]
        pygame.draw.rect(screen, (200, 200, 200), rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 0), rect, 2, border_radius=10)
        label = f"Player {p}: {player_modes[p]}"
        txt = small_font.render(label, True, (0, 0, 0))
        screen.blit(txt, txt.get_rect(center=rect.center))

    if flip:
        pygame.display.flip()
    