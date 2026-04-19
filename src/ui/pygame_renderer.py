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

def draw_menu(screen, play_rect, join_rect, setting_rect, exit_rect, *, continue_rect=None, status_text=None, flip: bool = True) -> None:
    title_font, _, small_font = _get_menu_fonts()
    screen.fill((30, 30, 30))

    title = title_font.render("Triangle Board Game", True, (255, 255, 255))
    screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 200)))

    _draw_button(screen, play_rect, "Play")
    _draw_button(screen, join_rect, "Join Online")
    if continue_rect is not None:
        _draw_button(screen, continue_rect, "Continue")
    _draw_button(screen, setting_rect, "Setting")
    _draw_button(screen, exit_rect, "Exit")

    if status_text:
        status = small_font.render(status_text, True, (255, 220, 120))
        screen.blit(status, status.get_rect(center=(WIDTH // 2, HEIGHT - 34)))

    if flip:
        pygame.display.flip()

def draw_lobby(
    screen,
    rooms: list,
    notice: str | None,
    input_room_id: str,
    room_input_active: bool,
    create_rect,
    join_rect,
    back_rect,
    room_rects: list,
    *,
    create_max_players: int = 2,
    toggle_players_rect=None,
    p3_ai_mode: str = "human",
    toggle_p3_ai_rect=None,
    flip: bool = True,
) -> tuple:
    """Draw the online lobby screen.
    Returns (join_btn_rect, toggle_players_rect, toggle_p3_ai_rect).
    """
    title_font, btn_font, small_font = _get_menu_fonts()
    screen.fill((20, 20, 28))

    # ── Title ──────────────────────────────────────────────────────────────
    title = title_font.render("Online Lobby", True, (255, 255, 255))
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 48)))

    # Back button
    pygame.draw.rect(screen, (70, 70, 80), back_rect, border_radius=8)
    pygame.draw.rect(screen, (160, 160, 180), back_rect, 1, border_radius=8)
    back_text = small_font.render("<  Back", True, (210, 210, 210))
    screen.blit(back_text, back_text.get_rect(center=back_rect.center))

    # Notice / status bar
    if notice:
        notice_color = (255, 200, 60) if "error" not in notice.lower() else (255, 80, 80)
        ntxt = small_font.render(notice, True, notice_color)
        screen.blit(ntxt, ntxt.get_rect(center=(WIDTH // 2, 82)))

    # ══════════════════════════════════════════════════════════════════════
    # LEFT PANEL  — Available Rooms
    # ══════════════════════════════════════════════════════════════════════
    left_panel = pygame.Rect(12, 100, 390, 488)
    panel_surf = pygame.Surface(left_panel.size, pygame.SRCALPHA)
    panel_surf.fill((35, 35, 48, 220))
    screen.blit(panel_surf, left_panel.topleft)
    pygame.draw.rect(screen, (70, 70, 100), left_panel, 1, border_radius=12)

    lp_title = small_font.render("Available Rooms", True, (180, 180, 220))
    screen.blit(lp_title, lp_title.get_rect(midleft=(left_panel.left + 16, left_panel.top + 20)))
    pygame.draw.line(screen, (70, 70, 100),
                     (left_panel.left + 10, left_panel.top + 38),
                     (left_panel.right - 10, left_panel.top + 38))

    if not rooms:
        empty_txt = small_font.render("No open rooms yet", True, (100, 100, 120))
        screen.blit(empty_txt, empty_txt.get_rect(center=(left_panel.centerx, left_panel.top + 120)))
    else:
        for room, rect in zip(rooms, room_rects):
            mx = room.get("max_players", 2)
            cur = room.get("players", 0)
            is_open = cur < mx
            bg = (45, 90, 160) if is_open else (55, 55, 65)
            pygame.draw.rect(screen, bg, rect, border_radius=8)
            pygame.draw.rect(screen, (100, 140, 220) if is_open else (80, 80, 90), rect, 1, border_radius=8)
            rid = small_font.render(room["room_id"], True, (255, 255, 255))
            screen.blit(rid, rid.get_rect(midleft=(rect.left + 14, rect.centery)))
            slots_txt = small_font.render(
                f"{cur}/{mx} players",
                True, (180, 210, 255) if is_open else (140, 140, 150),
            )
            screen.blit(slots_txt, slots_txt.get_rect(midright=(rect.right - 14, rect.centery)))

    # Join by Room ID (bottom of left panel)
    pygame.draw.line(screen, (70, 70, 100),
                     (left_panel.left + 10, join_rect.top - 32),
                     (left_panel.right - 10, join_rect.top - 32))
    id_label = small_font.render("Join by Room ID", True, (180, 180, 220))
    screen.blit(id_label, id_label.get_rect(midleft=(join_rect.left, join_rect.top - 16)))

    border_color = (100, 180, 255) if room_input_active else (70, 70, 100)
    pygame.draw.rect(screen, (45, 45, 60), join_rect, border_radius=8)
    pygame.draw.rect(screen, border_color, join_rect, 2, border_radius=8)
    placeholder = input_room_id if input_room_id else ("Room ID..." if not room_input_active else "")
    id_color = (220, 220, 220) if input_room_id else (100, 100, 120)
    id_val = small_font.render(placeholder, True, id_color)
    screen.blit(id_val, id_val.get_rect(midleft=(join_rect.left + 12, join_rect.centery)))

    join_btn_rect = pygame.Rect(join_rect.right + 10, join_rect.top, 110, join_rect.height)
    jbg = (40, 100, 200) if input_room_id else (50, 50, 70)
    pygame.draw.rect(screen, jbg, join_btn_rect, border_radius=8)
    pygame.draw.rect(screen, (80, 130, 220) if input_room_id else (70, 70, 90), join_btn_rect, 1, border_radius=8)
    jbtxt = small_font.render("Join", True, (220, 220, 220))
    screen.blit(jbtxt, jbtxt.get_rect(center=join_btn_rect.center))

    # ══════════════════════════════════════════════════════════════════════
    # RIGHT PANEL  — Create Room
    # ══════════════════════════════════════════════════════════════════════
    right_panel = pygame.Rect(418, 100, 370, 310)
    rp_surf = pygame.Surface(right_panel.size, pygame.SRCALPHA)
    rp_surf.fill((35, 35, 48, 220))
    screen.blit(rp_surf, right_panel.topleft)
    pygame.draw.rect(screen, (70, 70, 100), right_panel, 1, border_radius=12)

    rp_title = small_font.render("Create Room", True, (180, 180, 220))
    screen.blit(rp_title, rp_title.get_rect(midleft=(right_panel.left + 16, right_panel.top + 20)))
    pygame.draw.line(screen, (70, 70, 100),
                     (right_panel.left + 10, right_panel.top + 38),
                     (right_panel.right - 10, right_panel.top + 38))

    # Players label + 2P/3P tabs
    tab_y = right_panel.top + 56
    tab2 = pygame.Rect(right_panel.left + 114, tab_y, 76, 34)
    tab3 = pygame.Rect(right_panel.left + 200, tab_y, 76, 34)
    toggle_rect = tab2 if create_max_players == 3 else tab3

    pl_label = small_font.render("Players", True, (160, 160, 190))
    screen.blit(pl_label, pl_label.get_rect(midleft=(right_panel.left + 16, tab2.centery)))

    for tab, players in ((tab2, 2), (tab3, 3)):
        active = create_max_players == players
        bg = (50, 100, 200) if active else (45, 45, 65)
        border = (100, 160, 255) if active else (70, 70, 100)
        pygame.draw.rect(screen, bg, tab, border_radius=8)
        pygame.draw.rect(screen, border, tab, 2, border_radius=8)
        tab_txt = small_font.render(f"{players}P", True, (255, 255, 255) if active else (150, 150, 170))
        screen.blit(tab_txt, tab_txt.get_rect(center=tab.center))

    # P3 mode selector (only when 3P)
    p3_btn_rect = toggle_p3_ai_rect or pygame.Rect(right_panel.left + 114, right_panel.top + 112, 200, 34)
    if create_max_players == 3:
        p3_label = small_font.render("Player 3", True, (160, 160, 190))
        screen.blit(p3_label, p3_label.get_rect(midleft=(right_panel.left + 16, p3_btn_rect.centery)))
        ai_color_map = {"human": (45, 45, 65), "random": (35, 90, 40), "minimax": (75, 30, 95), "mcts": (30, 65, 110), "ml": (100, 65, 15)}
        ai_label_map = {"human": "Player", "random": "Random", "minimax": "Minimax", "mcts": "MCTS", "ml": "ML"}
        p3_color = ai_color_map.get(p3_ai_mode, (45, 45, 65))
        pygame.draw.rect(screen, p3_color, p3_btn_rect, border_radius=8)
        pygame.draw.rect(screen, (120, 120, 160), p3_btn_rect, 1, border_radius=8)
        p3_txt = small_font.render(ai_label_map.get(p3_ai_mode, "Player  ▾"), True, (220, 220, 220))
        screen.blit(p3_txt, p3_txt.get_rect(center=p3_btn_rect.center))

    # Create button
    pygame.draw.rect(screen, (28, 130, 55), create_rect, border_radius=10)
    pygame.draw.rect(screen, (70, 190, 90), create_rect, 2, border_radius=10)
    ctxt = small_font.render("Create Room", True, (255, 255, 255))
    screen.blit(ctxt, ctxt.get_rect(center=create_rect.center))

    if flip:
        pygame.display.flip()

    return join_btn_rect, toggle_rect, p3_btn_rect


def draw_settings(screen, back_rect, mode_rects, player_modes, host_rect, port_rect, network_host, network_port, active_input=None, *, flip: bool = True) -> None:
    title_font, _, small_font = _get_menu_fonts()
    screen.fill((30, 30, 30))

    title = title_font.render("Settings", True, (255, 255, 255))
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 72)))

    # Back button
    pygame.draw.rect(screen, (200, 200, 200), back_rect, border_radius=10)
    pygame.draw.rect(screen, (255, 255, 0), back_rect, 2, border_radius=10)
    back_text = small_font.render("Back", True, (0, 0, 0))
    screen.blit(back_text, back_text.get_rect(center=back_rect.center))

    # Mode selectors
    local_title = small_font.render("Local Game Modes", True, (255, 255, 255))
    screen.blit(local_title, local_title.get_rect(center=(WIDTH // 2, 150)))

    hint = small_font.render("Click a player row to change AI or human mode", True, (200, 200, 200))
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, 186)))

    for p in (1, 2, 3):
        rect = mode_rects[p]
        pygame.draw.rect(screen, (200, 200, 200), rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 0), rect, 2, border_radius=10)
        label = f"Player {p}: {player_modes[p]}"
        txt = small_font.render(label, True, (0, 0, 0))
        screen.blit(txt, txt.get_rect(center=rect.center))

    _cursor_visible = (pygame.time.get_ticks() // 500) % 2 == 0

    host_label = small_font.render("Server IP  (click to edit)", True, (220, 220, 220))
    screen.blit(host_label, (host_rect.left, 480))
    h_rect = pygame.Rect(host_rect.left, 506, host_rect.width, host_rect.height)
    pygame.draw.rect(screen, (200, 200, 200), h_rect, border_radius=10)
    pygame.draw.rect(screen, (255, 255, 0) if active_input == "host" else (120, 120, 120), h_rect, 2, border_radius=10)
    host_display = (network_host or "") + ("|" if active_input == "host" and _cursor_visible else "")
    host_value = small_font.render(host_display, True, (0, 0, 0))
    screen.blit(host_value, host_value.get_rect(midleft=(h_rect.left + 14, h_rect.centery)))

    port_label = small_font.render("Port  (default 5000)", True, (220, 220, 220))
    screen.blit(port_label, (port_rect.left, 568))
    p_rect = pygame.Rect(port_rect.left, 588, port_rect.width, port_rect.height)
    pygame.draw.rect(screen, (200, 200, 200), p_rect, border_radius=10)
    pygame.draw.rect(screen, (255, 255, 0) if active_input == "port" else (120, 120, 120), p_rect, 2, border_radius=10)
    port_display = (network_port or "") + ("|" if active_input == "port" and _cursor_visible else "")
    port_value = small_font.render(port_display, True, (0, 0, 0))
    screen.blit(port_value, port_value.get_rect(midleft=(p_rect.left + 14, p_rect.centery)))

    if flip:
        pygame.display.flip()

def draw_hud(screen, player_modes, turn: int, *, active_players=None, network_status=None, local_player=None, room_id=None, flip: bool = False) -> None:
    """Draw current turn + player modes (top-left)."""

    _title_font, _btn_font, small_font = _get_menu_fonts()

    if active_players is None:
        active_players = [1, 2, 3]

    lines = [f"Turn: Player {turn}"]

    if local_player is not None:
        lines.append(f"You: Player {local_player}")

    for player in active_players:
        lines.append(f"P{player}: {player_modes.get(player, 'player')}")

    # network_status intentionally not shown in HUD

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


def draw_room_id(screen, room_id: str):
    """Draw the room_id at the top-right corner of the screen (không viền)."""
    if not room_id:
        return
    _, _, small_font = _get_menu_fonts()
    text = small_font.render(f"Room: {room_id}", True, (255, 255, 255))
    pad = 10
    w, h = text.get_width() + pad * 2, text.get_height() + pad * 2
    rect = pygame.Rect(WIDTH - w - 16, 16, w, h)
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    panel.fill((30, 30, 30, 200))
    screen.blit(panel, rect.topleft)
    # Không vẽ viền nữa
    screen.blit(text, (rect.left + pad, rect.top + pad))

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
    