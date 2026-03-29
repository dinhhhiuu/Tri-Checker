from src.core.board import TriangleBoard

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

def test_jump_logic(board):
    # reset board
    board.board = [
        [0 for _ in range(r + 1)]
        for r in range(board.size)
    ]

    # đặt quân test
    board._set_piece(4, 2, 1)  # quân mình

    # tạo cầu nhảy
    board._set_piece(5, 2, 2)
    board._set_piece(6, 2, 2)

    board._set_piece(5, 3, 2)
    board._set_piece(7, 5, 2)

    board._set_piece(8, 5, 2)
    board._set_piece(8, 7, 2)

    print("=== TEST BOARD ===")
    board.print_board()

    print("\n=== JUMP PATHS ===")
    paths = board._get_jump_paths(4, 2)
    for p in paths:
        print(p)

    print("\n=== ALL MOVES ===")
    moves = board.get_all_moves(4, 2)
    for m in moves:
        print(m)

def test():   
    board = TriangleBoard()

    # init_players(board)
    # board.print_board()
    # board.get_board()
    # board.get_all_pieces(1)

    test_jump_logic(board)

if __name__ == "__main__":
    test()
