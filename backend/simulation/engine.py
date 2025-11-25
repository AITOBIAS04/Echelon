import chess
import chess.engine
import hashlib
import os
import sys

def get_provable_game_seed(server_seed, client_seed, nonce):
    combined_string = f"{server_seed}-{client_seed}-{nonce}"
    game_hash = hashlib.sha256(combined_string.encode()).hexdigest()
    return game_hash

def run_provable_chess_match(server_seed, client_seed, nonce):
    
    STOCKFISH_PATH = "/Users/tobyharber/Downloads/stockfish/stockfish-macos-m1-apple-silicon"
    
    if not os.path.exists(STOCKFISH_PATH):
        return "ERROR: Stockfish not found"

    game_hash = get_provable_game_seed(server_seed, client_seed, nonce)
    hash_as_int = int(game_hash, 16)
    agent_a_is_white = (hash_as_int % 2 == 0)

    try:
        engine_a = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
        engine_b = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    except Exception as e:
        return f"ERROR: Engine failed to load: {e}"

    skill_level = (hash_as_int // 10) % 20 + 1
    engine_a.configure({"Skill Level": skill_level})
    engine_b.configure({"Skill Level": skill_level})
    
    board = chess.Board()
    
    while not board.is_game_over():
        if (board.turn == chess.WHITE and agent_a_is_white) or \
           (board.turn == chess.BLACK and not agent_a_is_white):
            
            # --- MODIFIED LINE ---
            result = engine_a.play(board, chess.engine.Limit(depth=2))
        else:
            # --- MODIFIED LINE ---
            result = engine_b.play(board, chess.engine.Limit(depth=2))
        
        board.push(result.move)

    game_result = board.result()

    engine_a.quit()
    engine_b.quit()
    
    return game_result

if __name__ == "__main__":
    
    if len(sys.argv) != 4:
        print("ERROR: Invalid arguments. Required: server_seed client_seed nonce")
        sys.exit(1)
        
    SERVER_SEED = sys.argv[1]
    CLIENT_SEED = sys.argv[2]
    NONCE = sys.argv[3]
    
    final_result = run_provable_chess_match(SERVER_SEED, CLIENT_SEED, NONCE)
    print(final_result)