import json
import os
import sys

import pygame

from src.ai.mcts_ai import choose_mcts_move
from src.ai.minimax_ai import choose_minimax_move
from src.ai.random_ai import choose_random_move
from src.core.board import TriangleBoard
from src.core.move import apply_move
from src.core.utils import init_players, is_valid_move_for_player, next_player
from src.network import ClientSession, DEFAULT_PORT, HostSession
from src.network.session import deserialize_path, serialize_path
from src.ui.config import DEFAULT_NETWORK_HOST, HEIGHT, MODES, WIDTH
from src.ui.pygame_renderer import (
    draw,
    draw_ai_path,
    draw_hud,
    draw_human_path,
    draw_lobby,
    draw_menu,
    draw_pause,
    draw_settings,
    draw_winner,
    get_cell_from_mouse,
)

# Lazy import để tránh numpy/joblib làm chậm startup
def choose_ml_move(board, player, **kwargs):
    from src.ai.ml_ai import choose_ml_move as _choose_ml_move
    return _choose_ml_move(board, player, **kwargs)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Triangle Board Game")

    clock = pygame.time.Clock()
    save_path = os.path.join("data", "savegame.json")

    state = "menu"
    game_mode = "local"
    settings_player_modes = {1: "player", 2: "player", 3: "player"}
    game_player_modes = dict(settings_player_modes)
    active_players = [1, 2, 3]
    local_player_id = None
    network_session = None
    network_match_ready = True
    network_notice = None
    waiting_for_server = False  # True sau khi gửi move, chờ server trả state
    menu_status = None
    settings_active_input = None
    network_host = DEFAULT_NETWORK_HOST
    network_port = str(DEFAULT_PORT)

    # Lobby state
    lobby_rooms: list = []
    lobby_notice: str | None = None
    lobby_input_room_id: str = ""
    lobby_room_input_active: bool = False
    lobby_join_btn_rect = None
    lobby_toggle_rect = None
    lobby_p3_ai_rect = None
    lobby_room_rects: list = []
    lobby_create_max_players: int = 2
    lobby_p3_ai_mode: str = "human"   # human / random / minimax

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

    def delete_save() -> None:
        try:
            if os.path.exists(save_path):
                os.remove(save_path)
        except OSError:
            pass

    def close_network_session() -> None:
        nonlocal network_match_ready, network_notice, network_session

        if network_session is not None:
            network_session.close()
            network_session = None

        network_match_ready = True
        network_notice = None

    def clear_runtime_state() -> None:
        nonlocal selected, valid_moves, winner, game_over, turn
        nonlocal win_restart_rect, win_menu_rect, paused
        nonlocal pause_continue_rect, pause_menu_rect, pause_quit_rect
        nonlocal last_ai_path, last_ai_player, last_human_path, last_human_player

        selected = None
        valid_moves = []
        winner = None
        game_over = False
        turn = active_players[0]
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

    def parse_network_port() -> int:
        value = int((network_port or str(DEFAULT_PORT)).strip())
        if not 1 <= value <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return value

    def reset_game(active_player_list, player_mode_map) -> None:
        nonlocal board, active_players, game_player_modes

        active_players = list(active_player_list)
        game_player_modes = dict(player_mode_map)
        board = TriangleBoard()
        init_players(board, active_players)
        clear_runtime_state()

    def start_local_game() -> None:
        nonlocal game_mode, local_player_id, menu_status

        close_network_session()
        game_mode = "local"
        local_player_id = None
        menu_status = None
        reset_game([1, 2, 3], settings_player_modes)
        delete_save()

    def start_network_host_game() -> bool:
        nonlocal game_mode, local_player_id, network_match_ready, network_notice
        nonlocal network_session, menu_status

        close_network_session()
        try:
            network_session = HostSession(port=parse_network_port())
        except Exception as exc:
            network_session = None
            menu_status = f"Cannot host online game: {exc}"
            return False

        game_mode = "network_host"
        local_player_id = 1
        network_match_ready = False
        network_notice = "Waiting for client"
        menu_status = None
        reset_game([1, 2], {1: "player", 2: "player"})
        return True

    def start_network_client_game() -> bool:
        nonlocal game_mode, local_player_id, network_match_ready, network_notice
        nonlocal network_session, menu_status

        close_network_session()
        try:
            host = (network_host or DEFAULT_NETWORK_HOST).strip()
            network_session = ClientSession(host=host, port=parse_network_port())
        except Exception as exc:
            network_session = None
            menu_status = f"Cannot join online game: {exc}"
            return False

        game_mode = "network_client"
        local_player_id = None          # assigned by server after joining a room
        network_match_ready = False
        network_notice = "Connecting..."
        menu_status = None
        reset_game([1, 2], {1: "player", 2: "player"})
        return True

    def restart_network_host_game() -> None:
        reset_game([1, 2], {1: "player", 2: "player"})

    def save_game_if_needed() -> None:
        if game_mode != "local":
            return
        if state != "game":
            return
        if board is None:
            return
        if game_over or winner:
            return

        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
        payload = {
            "board_size": int(board.size),
            "board": board.board,
            "turn": int(turn),
            "player_modes": {str(k): str(v) for k, v in game_player_modes.items()},
        }
        tmp_path = save_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as file_obj:
            json.dump(payload, file_obj)
        os.replace(tmp_path, save_path)

    def load_game_from_save() -> bool:
        nonlocal board, turn, game_mode, local_player_id, game_player_modes
        nonlocal active_players, menu_status

        if not os.path.exists(save_path):
            return False

        try:
            with open(save_path, "r", encoding="utf-8") as file_obj:
                data = json.load(file_obj)
        except (OSError, json.JSONDecodeError):
            return False

        try:
            size = int(data.get("board_size", 10))
            loaded_board = data.get("board")
            loaded_turn = int(data.get("turn", 1))
            loaded_modes = data.get("player_modes", {})
        except Exception:
            return False

        if not isinstance(loaded_board, list):
            return False

        close_network_session()
        game_mode = "local"
        local_player_id = None
        menu_status = None
        active_players = [1, 2, 3]
        board = TriangleBoard(size)
        board.board = loaded_board
        game_player_modes = {
            int(key): (value if value in MODES else "player")
            for key, value in loaded_modes.items()
            if str(key).isdigit()
        }
        for player in (1, 2, 3):
            game_player_modes.setdefault(player, "player")
        clear_runtime_state()
        turn = loaded_turn
        return True

    def build_network_state_payload() -> dict:
        return {
            "type": "state",
            "board_size": int(board.size),
            "board": board.board,
            "turn": int(turn),
            "winner": winner,
            "game_over": game_over,
            "active_players": list(active_players),
            "match_ready": bool(network_session is not None and network_session.has_client()),
            "last_move_path": serialize_path(last_human_path) if last_human_path else [],
            "last_move_player": last_human_player,
        }

    def broadcast_network_state() -> None:
        if game_mode == "network_host" and network_session is not None:
            network_session.send(build_network_state_payload())

    def sync_from_network_state(payload: dict) -> None:
        nonlocal board, turn, winner, game_over, active_players
        nonlocal network_match_ready, network_notice
        nonlocal selected, valid_moves, last_human_path, last_human_player
        nonlocal last_ai_path, last_ai_player

        size = int(payload.get("board_size", 10))
        incoming_board = payload.get("board")
        incoming_players = payload.get("active_players", [1, 2])

        if board is None or board.size != size:
            board = TriangleBoard(size)

        if isinstance(incoming_board, list):
            board.board = incoming_board

        active_players = [int(player) for player in incoming_players]
        turn = int(payload.get("turn", active_players[0]))
        winner = payload.get("winner")
        game_over = bool(payload.get("game_over", False))
        network_match_ready = bool(payload.get("match_ready", True))

        # Cập nhật player modes: AI slots từ server hiển thị đúng tên
        ai_slots = payload.get("ai_slots", {})
        for pid in active_players:
            str_pid = str(pid)
            if str_pid in ai_slots:
                game_player_modes[pid] = ai_slots[str_pid]
            else:
                game_player_modes.setdefault(pid, "player")

        status_text = payload.get("status_text")
        if isinstance(status_text, str) and status_text:
            network_notice = status_text

        path = deserialize_path(payload.get("last_move_path", []))
        player = payload.get("last_move_player")
        if path and player is not None:
            last_human_path = path
            last_human_player = int(player)
        else:
            last_human_path = None
            last_human_player = None

        last_ai_path = None
        last_ai_player = None
        selected = None
        valid_moves = []

    btn_w, btn_h = 300, 56
    btn_gap = 16
    btn_x = (WIDTH - btn_w) // 2
    btn_y0 = 150
    play_rect = pygame.Rect(btn_x, btn_y0, btn_w, btn_h)
    join_rect = pygame.Rect(btn_x, btn_y0 + (btn_h + btn_gap) * 1, btn_w, btn_h)
    continue_rect = pygame.Rect(btn_x, btn_y0 + (btn_h + btn_gap) * 2, btn_w, btn_h)
    setting_rect = pygame.Rect(btn_x, btn_y0 + (btn_h + btn_gap) * 3, btn_w, btn_h)
    exit_rect = pygame.Rect(btn_x, btn_y0 + (btn_h + btn_gap) * 4, btn_w, btn_h)

    back_rect = pygame.Rect(24, 24, 140, 52)
    mode_rects = {
        1: pygame.Rect(WIDTH // 2 - 220, 220, 440, 52),
        2: pygame.Rect(WIDTH // 2 - 220, 292, 440, 52),
        3: pygame.Rect(WIDTH // 2 - 220, 364, 440, 52),
    }
    host_input_rect = pygame.Rect(WIDTH // 2 - 220, 506, 440, 50)
    port_input_rect = pygame.Rect(WIDTH // 2 - 220, 588, 440, 50)

    # Lobby screen geometry
    lobby_back_rect = pygame.Rect(24, 24, 100, 40)
    lobby_create_rect = pygame.Rect(435, 310, 320, 52)
    lobby_join_input_rect = pygame.Rect(28, 530, 248, 44)

    while True:
        human_moved_this_frame = False
        network_broadcast_required = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game_if_needed()
                close_network_session()
                pygame.quit()
                sys.exit()

            if state == "menu":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if play_rect.collidepoint(event.pos):
                        start_local_game()
                        state = "game"
                    elif join_rect.collidepoint(event.pos):
                        if start_network_client_game():
                            state = "lobby"
                    elif continue_rect.collidepoint(event.pos):
                        if load_game_from_save():
                            state = "game"
                        else:
                            start_local_game()
                            state = "game"
                    elif setting_rect.collidepoint(event.pos):
                        settings_active_input = None
                        state = "settings"
                    elif exit_rect.collidepoint(event.pos):
                        save_game_if_needed()
                        close_network_session()
                        pygame.quit()
                        sys.exit()

            elif state == "settings":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if back_rect.collidepoint(event.pos):
                        settings_active_input = None
                        state = "menu"
                        continue

                    if host_input_rect.collidepoint(event.pos):
                        settings_active_input = "host"
                        continue

                    if port_input_rect.collidepoint(event.pos):
                        settings_active_input = "port"
                        continue

                    settings_active_input = None
                    for player in (1, 2, 3):
                        if mode_rects[player].collidepoint(event.pos):
                            current = settings_player_modes[player]
                            idx = MODES.index(current) if current in MODES else 0
                            settings_player_modes[player] = MODES[(idx + 1) % len(MODES)]
                            break

                elif event.type == pygame.KEYDOWN and settings_active_input:
                    if event.key == pygame.K_ESCAPE:
                        settings_active_input = None
                    elif event.key == pygame.K_BACKSPACE:
                        if settings_active_input == "host":
                            network_host = network_host[:-1]
                        else:
                            network_port = network_port[:-1]
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_TAB):
                        settings_active_input = "port" if settings_active_input == "host" else None
                    else:
                        if settings_active_input == "host":
                            if event.unicode and event.unicode in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-":
                                network_host = (network_host + event.unicode)[:64]
                        else:
                            if event.unicode and event.unicode.isdigit():
                                network_port = (network_port + event.unicode)[:5]

            elif state == "lobby":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if lobby_back_rect.collidepoint(event.pos):
                        close_network_session()
                        lobby_rooms = []
                        lobby_notice = None
                        lobby_input_room_id = ""
                        lobby_room_input_active = False
                        state = "menu"
                        continue

                    if lobby_create_rect.collidepoint(event.pos):
                        if network_session is not None:
                            try:
                                ai_slots = {3: lobby_p3_ai_mode} if lobby_create_max_players == 3 and lobby_p3_ai_mode != "human" else None
                                network_session.create_room(max_players=lobby_create_max_players, ai_slots=ai_slots)
                                lobby_notice = f"Creating {lobby_create_max_players}-player room..."
                            except OSError:
                                close_network_session()
                                menu_status = "Lost connection to server."
                                state = "menu"
                        continue

                    if lobby_toggle_rect and lobby_toggle_rect.collidepoint(event.pos):
                        lobby_create_max_players = 3 if lobby_create_max_players == 2 else 2
                        if lobby_create_max_players == 2:
                            lobby_p3_ai_mode = "human"
                        continue

                    if lobby_p3_ai_rect and lobby_create_max_players == 3 and lobby_p3_ai_rect.collidepoint(event.pos):
                        cycle = ["human", "random", "minimax", "mcts", "ml"]
                        lobby_p3_ai_mode = cycle[(cycle.index(lobby_p3_ai_mode) + 1) % len(cycle)]
                        continue

                    if lobby_join_btn_rect and lobby_join_btn_rect.collidepoint(event.pos):
                        if network_session is not None and lobby_input_room_id.strip():
                            try:
                                network_session.join_room(lobby_input_room_id.strip())
                                lobby_notice = f"Joining room {lobby_input_room_id.upper()}..."
                            except OSError:
                                close_network_session()
                                menu_status = "Lost connection to server."
                                state = "menu"
                        continue

                    # Click a room in the list to join it
                    for i, rect in enumerate(lobby_room_rects):
                        if rect.collidepoint(event.pos) and i < len(lobby_rooms):
                            room = lobby_rooms[i]
                            if room.get("players", 99) < room.get("max_players", 2) and network_session is not None:
                                try:
                                    network_session.join_room(room["room_id"])
                                    lobby_notice = f"Joining room {room['room_id']}..."
                                except OSError:
                                    close_network_session()
                                    menu_status = "Lost connection to server."
                                    state = "menu"
                            break

                    if lobby_join_input_rect.collidepoint(event.pos):
                        lobby_room_input_active = True
                        continue
                    lobby_room_input_active = False

                elif event.type == pygame.KEYDOWN and lobby_room_input_active:
                    if event.key == pygame.K_ESCAPE:
                        lobby_room_input_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        lobby_input_room_id = lobby_input_room_id[:-1]
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        if network_session is not None and lobby_input_room_id.strip():
                            try:
                                network_session.join_room(lobby_input_room_id.strip())
                                lobby_notice = f"Joining room {lobby_input_room_id.upper()}..."
                            except OSError:
                                close_network_session()
                                menu_status = "Lost connection to server."
                                state = "menu"
                        lobby_room_input_active = False
                    else:
                        allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
                        if event.unicode and event.unicode in allowed:
                            lobby_input_room_id = (lobby_input_room_id + event.unicode.upper())[:8]

            elif state == "game":
                if board is None:
                    continue

                if game_over:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if win_restart_rect and win_restart_rect.collidepoint(event.pos):
                            if game_mode == "local":
                                start_local_game()
                            elif game_mode == "network_host":
                                restart_network_host_game()
                                network_broadcast_required = True
                            elif game_mode == "network_client" and network_session is not None:
                                try:
                                    network_session.send({"type": "restart"})
                                except OSError:
                                    close_network_session()
                                    menu_status = "Lost connection to server."
                                    state = "menu"
                        elif win_menu_rect and win_menu_rect.collidepoint(event.pos):
                            if game_mode != "local":
                                close_network_session()
                                menu_status = "Online match closed."
                            state = "menu"
                    continue

                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if game_mode == "local":
                        paused = not paused
                        selected = None
                        valid_moves = []
                    else:
                        close_network_session()
                        menu_status = "Online match closed."
                        state = "menu"
                    continue

                if paused:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if pause_continue_rect and pause_continue_rect.collidepoint(event.pos):
                            paused = False
                        elif pause_menu_rect and pause_menu_rect.collidepoint(event.pos):
                            save_game_if_needed()
                            paused = False
                            state = "menu"
                        elif pause_quit_rect and pause_quit_rect.collidepoint(event.pos):
                            save_game_if_needed()
                            pygame.quit()
                            sys.exit()
                    continue

                current_mode = game_player_modes.get(turn, "player")
                is_local_turn = game_mode == "local" and current_mode == "player"
                is_host_turn = (
                    game_mode == "network_host"
                    and local_player_id == turn
                    and network_session is not None
                    and network_session.has_client()
                )
                is_client_turn = (
                    game_mode == "network_client"
                    and local_player_id == turn
                    and network_match_ready
                    and not waiting_for_server
                )

                if not (is_local_turn or is_host_turn or is_client_turn):
                    continue

                if event.type == pygame.MOUSEBUTTONDOWN:
                    cell = get_cell_from_mouse(event.pos, board)
                    if not cell:
                        continue

                    row, col = cell
                    if selected is None:
                        if board.board[row][col] == turn:
                            selected = (row, col)
                            valid_moves = board.get_all_moves(row, col)
                    else:
                        chosen = None
                        for path in valid_moves:
                            if path[-1] == (row, col):
                                chosen = path
                                break

                        if chosen:
                            moved_player = turn
                            if game_mode == "network_client":
                                try:
                                    network_session.send({"type": "move", "path": serialize_path(chosen)})
                                    waiting_for_server = True
                                except OSError:
                                    close_network_session()
                                    menu_status = "Lost connection to host."
                                    state = "menu"
                            else:
                                apply_move(board, chosen)
                                last_human_path = chosen
                                last_human_player = moved_player
                                last_ai_path = None
                                last_ai_player = None
                                turn = next_player(turn, active_players)
                                human_moved_this_frame = True
                                if game_mode == "network_host":
                                    network_broadcast_required = True

                        selected = None
                        valid_moves = []

        if state == "menu":
            draw_menu(
                screen,
                play_rect,
                join_rect,
                setting_rect,
                exit_rect,
                continue_rect=continue_rect,
                status_text=menu_status,
            )
            clock.tick(60)
            continue

        if state == "settings":
            draw_settings(
                screen,
                back_rect,
                mode_rects,
                settings_player_modes,
                host_input_rect,
                port_input_rect,
                network_host,
                network_port,
                settings_active_input,
            )
            clock.tick(60)
            continue

        # ── Lobby: poll server for room list updates and welcome ───────────
        if state == "lobby" and network_session is not None:
            for net_evt in network_session.poll_events():
                evt_type = net_evt.get("type")
                if evt_type == "server_disconnected":
                    close_network_session()
                    menu_status = "Server disconnected."
                    lobby_rooms = []
                    state = "menu"
                    break
                if evt_type == "server_message":
                    payload = net_evt.get("payload", {})
                    ptype = payload.get("type")
                    if ptype == "lobby":
                        lobby_rooms = payload.get("rooms", [])
                        lobby_notice = None
                    elif ptype == "welcome":
                        local_player_id = int(payload.get("player_id", 1))
                        lobby_notice = payload.get("message", "")
                    elif ptype == "state":
                        # Server sent game state → we're in a room now
                        sync_from_network_state(payload)
                        state = "game"
                        break
                    elif ptype == "error":
                        lobby_notice = payload.get("message", "Error")

        if state == "lobby":
            row_y = 148
            lobby_room_rects = []
            for _ in lobby_rooms:
                lobby_room_rects.append(pygame.Rect(22, row_y, 370, 44))
                row_y += 52

            lobby_join_btn_rect, lobby_toggle_rect, lobby_p3_ai_rect = draw_lobby(
                screen,
                lobby_rooms,
                lobby_notice,
                lobby_input_room_id,
                lobby_room_input_active,
                lobby_create_rect,
                lobby_join_input_rect,
                lobby_back_rect,
                lobby_room_rects,
                create_max_players=lobby_create_max_players,
                toggle_players_rect=lobby_toggle_rect,
                p3_ai_mode=lobby_p3_ai_mode,
                toggle_p3_ai_rect=lobby_p3_ai_rect,
            )
            clock.tick(60)
            continue

        if game_mode == "network_host" and network_session is not None:
            for network_event in network_session.poll_events():
                event_type = network_event.get("type")
                if event_type == "client_connected":
                    network_match_ready = True
                    network_notice = "Client connected"
                    network_broadcast_required = True
                elif event_type == "client_disconnected":
                    close_network_session()
                    menu_status = "Client disconnected."
                    state = "menu"
                    break
                elif event_type == "client_message":
                    payload = network_event.get("payload", {})
                    if payload.get("type") != "move":
                        continue
                    if turn != 2 or game_over:
                        network_broadcast_required = True
                        continue

                    path = deserialize_path(payload.get("path", []))
                    if is_valid_move_for_player(board, 2, path):
                        apply_move(board, path)
                        last_human_path = path
                        last_human_player = 2
                        last_ai_path = None
                        last_ai_player = None
                        selected = None
                        valid_moves = []
                        turn = next_player(turn, active_players)
                    network_broadcast_required = True

        elif game_mode == "network_client" and network_session is not None:
            for network_event in network_session.poll_events():
                event_type = network_event.get("type")
                if event_type == "server_disconnected":
                    close_network_session()
                    menu_status = "Server disconnected."
                    state = "menu"
                    break
                if event_type == "server_message":
                    payload = network_event.get("payload", {})
                    payload_type = payload.get("type")
                    if payload_type == "welcome":
                        assigned_player = payload.get("player_id")
                        if assigned_player is not None:
                            local_player_id = int(assigned_player)
                        message = payload.get("message")
                        if isinstance(message, str) and message:
                            network_notice = message
                    elif payload_type == "state":
                        sync_from_network_state(payload)
                        waiting_for_server = False
                    elif payload_type == "lobby":
                        # Received fresh lobby list while in game → ignore
                        pass
                    elif payload_type in {"info", "error"}:
                        message = payload.get("message")
                        if isinstance(message, str) and message:
                            network_notice = message
                        waiting_for_server = False

        if state == "menu":
            draw_menu(
                screen,
                play_rect,
                join_rect,
                setting_rect,
                exit_rect,
                continue_rect=continue_rect,
                status_text=menu_status,
            )
            clock.tick(60)
            continue

        if paused:
            draw(screen, board, selected, valid_moves, flip=False)
            if last_ai_path and last_ai_player:
                draw_ai_path(screen, last_ai_path, last_ai_player)
            elif last_human_path and last_human_player:
                draw_human_path(screen, last_human_path, last_human_player)
            draw_hud(screen, game_player_modes, turn, active_players=active_players)
            pause_continue_rect, pause_menu_rect, pause_quit_rect = draw_pause(screen, flip=False)
            pygame.display.flip()
            clock.tick(60)
            continue

        if not game_over and game_mode != "network_client":
            winner = board.check_winner()
            if winner:
                game_over = True
                delete_save()
                if game_mode == "network_host":
                    network_broadcast_required = True

        if not game_over and game_mode in {"local", "network_host"} and not human_moved_this_frame:
            mode = game_player_modes.get(turn, "player")
            if mode != "player":
                last_human_path = None
                last_human_player = None
                move = None

                if mode == "random":
                    move = choose_random_move(board, turn, mode="random")
                elif mode == "minimax":
                    move = choose_minimax_move(board, turn, mode="minimax", depth=3)
                elif mode == "mcts":
                    move = choose_mcts_move(board, turn, mode="mcts", simulations=100)
                elif mode == "ml":
                    move = choose_ml_move(board, turn, mode="ml")
                else:
                    raise ValueError(f"Unknown mode for player {turn}: {mode}")

                if move:
                    last_ai_path = move
                    last_ai_player = turn
                    apply_move(board, move)

                selected = None
                valid_moves = []
                turn = next_player(turn, active_players)
                if game_mode == "network_host":
                    network_broadcast_required = True

        if network_broadcast_required and game_mode == "network_host" and network_session is not None:
            broadcast_network_state()

        network_status = None
        if game_mode in {"network_host", "network_client"} and network_session is not None:
            network_status = network_session.status
            if network_notice:
                network_status = f"{network_status} | {network_notice}"

        draw(screen, board, selected, valid_moves, flip=False)
        if last_ai_path and last_ai_player:
            draw_ai_path(screen, last_ai_path, last_ai_player)
        elif last_human_path and last_human_player:
            draw_human_path(screen, last_human_path, last_human_player)
        draw_hud(
            screen,
            game_player_modes,
            turn,
            active_players=active_players,
            network_status=network_status,
            local_player=local_player_id,
        )
        if game_over and winner:
            win_restart_rect, win_menu_rect = draw_winner(screen, winner, flip=False)
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()