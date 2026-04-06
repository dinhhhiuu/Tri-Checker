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

def draw_winner(screen, winner, *, flip: bool = True): # sau dấu * là keyword-only argument, chỉ có thể truyền bằng tên khi gọi hàm
    global _WINNER_FONT

    if _WINNER_FONT is None:
        _WINNER_FONT = pygame.font.SysFont(None, 48)

    # Dim the whole screen
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    screen.blit(overlay, (0, 0))

    # screen.fill((0, 0, 0))  # xóa màn hình (màu đen)

    # Winner panel + buttons
    _, btn_font, _ = _get_menu_fonts()

    text = _WINNER_FONT.render(f"Player {winner} wins!", True, COLORS[winner])
    restart_text = btn_font.render("Restart", True, (0, 0, 0))
    menu_text = btn_font.render("Menu", True, (0, 0, 0))

    padding = 24
    gap = 16
    btn_w, btn_h = 180, 54

    content_w = max(text.get_width(), btn_w * 2 + gap)
    panel_w = content_w + padding * 2
    panel_h = text.get_height() + gap + btn_h + padding * 2

    panel_rect = pygame.Rect(0, 0, panel_w, panel_h)
    panel_rect.center = (WIDTH // 2, HEIGHT // 2)

    panel = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
    panel.fill((30, 30, 30, 230))
    screen.blit(panel, panel_rect.topleft)
    pygame.draw.rect(screen, COLORS[winner], panel_rect, 3, border_radius=12)

    text_rect = text.get_rect(midtop=(panel_rect.centerx, panel_rect.top + padding))
    screen.blit(text, text_rect)

    buttons_top = text_rect.bottom + gap
    restart_rect = pygame.Rect(0, 0, btn_w, btn_h)
    menu_rect = pygame.Rect(0, 0, btn_w, btn_h)
    restart_rect.topleft = (panel_rect.left + padding, buttons_top)
    menu_rect.topright = (panel_rect.right - padding, buttons_top)

    _draw_button(screen, restart_rect, "Restart")
    _draw_button(screen, menu_rect, "Menu")

    if flip:
        pygame.display.flip()

    return restart_rect, menu_rect

def draw_pause(screen, *, flip: bool = True):
    """Draw pause overlay and return (continue_rect, menu_rect, quit_rect)."""

    title_font, _btn_font, small_font = _get_menu_fonts()

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    screen.blit(overlay, (0, 0))

    padding = 24
    gap = 14
    btn_w, btn_h = 220, 56

    title = title_font.render("Paused", True, (255, 255, 255))

    content_w = max(title.get_width(), btn_w)
    panel_w = content_w + padding * 2
    panel_h = title.get_height() + gap + (btn_h * 3) + (gap * 2) + padding * 2

    panel_rect = pygame.Rect(0, 0, panel_w, panel_h)
    panel_rect.center = (WIDTH // 2, HEIGHT // 2)

    panel = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
    panel.fill((30, 30, 30, 230))
    screen.blit(panel, panel_rect.topleft)
    pygame.draw.rect(screen, (255, 255, 0), panel_rect, 3, border_radius=12)

    title_rect = title.get_rect(midtop=(panel_rect.centerx, panel_rect.top + padding))
    screen.blit(title, title_rect)

    y = title_rect.bottom + gap
    continue_rect = pygame.Rect(0, 0, btn_w, btn_h)
    menu_rect = pygame.Rect(0, 0, btn_w, btn_h)
    quit_rect = pygame.Rect(0, 0, btn_w, btn_h)
    continue_rect.midtop = (panel_rect.centerx, y)
    menu_rect.midtop = (panel_rect.centerx, y + btn_h + gap)
    quit_rect.midtop = (panel_rect.centerx, y + (btn_h + gap) * 2)

    _draw_button(screen, continue_rect, "Continue")
    _draw_button(screen, menu_rect, "Menu")
    _draw_button(screen, quit_rect, "Quit")

    if flip:
        pygame.display.flip()

    return continue_rect, menu_rect, quit_rect

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

def draw_menu(screen, play_rect, setting_rect, exit_rect, *, continue_rect=None, flip: bool = True) -> None:
    title_font, _, _ = _get_menu_fonts()
    screen.fill((30, 30, 30))

    title = title_font.render("Triangle Board Game", True, (255, 255, 255))
    screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 180)))

    _draw_button(screen, play_rect, "Play")
    if continue_rect is not None:
        _draw_button(screen, continue_rect, "Continue")
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

def draw_hud(screen, player_modes, turn: int, *, flip: bool = False) -> None:
    """Draw current turn + player modes (top-left)."""

    _title_font, _btn_font, small_font = _get_menu_fonts()

    lines = [
        f"Turn: Player {turn}",
        f"P1: {player_modes.get(1, 'player')}",
        f"P2: {player_modes.get(2, 'player')}",
        f"P3: {player_modes.get(3, 'player')}",
    ]

    rendered = [small_font.render(line, True, (255, 255, 255)) for line in lines]

    pad = 10
    gap = 6
    w = max(s.get_width() for s in rendered) + pad * 2
    h = sum(s.get_height() for s in rendered) + gap * (len(rendered) - 1) + pad * 2

    rect = pygame.Rect(16, 16, w, h)

    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    panel.fill((30, 30, 30, 200))
    screen.blit(panel, rect.topleft)
    pygame.draw.rect(screen, (255, 255, 0), rect, 2, border_radius=10)

    y = rect.top + pad
    for surf in rendered:
        screen.blit(surf, (rect.left + pad, y))
        y += surf.get_height() + gap

    if flip:
        pygame.display.flip()

def draw_ai_path(screen, path, player: int, *, flip: bool = False) -> None:
    """Draw the path chosen by AI (or last auto-move)."""

    if not path or len(path) < 2:
        return

    color = COLORS.get(player, (255, 255, 0))
    points = [get_screen_pos(r, c) for (r, c) in path]

    # draw line
    pygame.draw.lines(screen, color, False, points, 4)

    # draw points (start/end bigger)
    for i, (x, y) in enumerate(points):
        if i == 0 or i == len(points) - 1:
            pygame.draw.circle(screen, color, (x, y), 10, 0)
            pygame.draw.circle(screen, (30, 30, 30), (x, y), 10, 2)
        else:
            pygame.draw.circle(screen, color, (x, y), 7, 0)
            pygame.draw.circle(screen, (30, 30, 30), (x, y), 7, 2)

    if flip:
        pygame.display.flip()


def draw_human_path(screen, path, player: int, *, flip: bool = False) -> None:
    """Draw the path chosen by a human (mouse move)."""

    if not path or len(path) < 2:
        return

    color = COLORS.get(player, (255, 255, 0))
    points = [get_screen_pos(r, c) for (r, c) in path]

    # outlined line for readability on the board
    pygame.draw.lines(screen, (30, 30, 30), False, points, 8)
    pygame.draw.lines(screen, color, False, points, 4)

    # draw points (start/end bigger)
    for i, (x, y) in enumerate(points):
        if i == 0 or i == len(points) - 1:
            pygame.draw.circle(screen, (30, 30, 30), (x, y), 12, 0)
            pygame.draw.circle(screen, color, (x, y), 10, 0)
            pygame.draw.circle(screen, (30, 30, 30), (x, y), 10, 2)
        else:
            pygame.draw.circle(screen, (30, 30, 30), (x, y), 9, 0)
            pygame.draw.circle(screen, color, (x, y), 7, 0)
            pygame.draw.circle(screen, (30, 30, 30), (x, y), 7, 2)

    if flip:
        pygame.display.flip()
    