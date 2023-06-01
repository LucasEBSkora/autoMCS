from __future__ import annotations
from typing import Any

import berserk
import chess
import random
import states

def atoi(value: any, default: int = 0) -> int:
    try:
        return int(value)
    except ValueError:
        return default

with open("./lichess.token") as f:
    token = f.read()

print(token)
session = berserk.TokenSession(token=token)
client = berserk.Client(session)

def handle_lichess_gameState(state: states.GameState, event: dict[str, Any], board: chess.Board, color_id: int, game_id: str):
    moves = event['moves'].split()
    
    while len(moves) > len(board.move_stack):
        board.push_uci(moves[-(len(moves) - len(board.move_stack))])
        print(board)
    
    # Has draw offer to handle
    if event.get("bdraw") and color_id == 0:
        state = states.GameState.WHANDLING_DRAW
    elif event.get("wdraw") and color_id == 1:
        state = states.GameState.BHANDLING_DRAW
    # Has takeback offer to handle
    elif event.get("btakeback") and color_id == 0:
        client.board.decline_takeback(game_id)
    elif event.get("wtakeback") and color_id == 1:
        client.board.decline_takeback(game_id)
    
    if len(event["moves"]) < len(board.move_stack):
        while len(event["moves"]) < len(board.move_stack): board.pop()
        return states.handle_transition(state, states.GameAction.ACCEPT)

    # User's turn
    if len(event["moves"].split()) % 2 == color_id:
        state = handle_user_choice(state, board, game_id)
    elif (state in [states.GameState.BHANDLING_DRAW, states.GameState.BHANDLING_TAKEBACK, states.GameState.WHANDLING_DRAW, states.GameState.WHANDLING_TAKEBACK]
        and not any(x in event.keys() for x in ["bdraw", "wdraw", "btakeback", "wtakeback"])):
        state = states.handle_transition(state, states.GameAction.DECLINE)
    else:
        state = states.handle_transition(state, states.GameAction.MOVE)
    return state

def print_choices_menu(state: states.GameState) -> None:
    print(state.value)
    actions = states.TRANSITIONS[state].keys()
    for i, action in enumerate(actions):
        print(f"{i + 1} - {action.value}")

def handle_user_choice(state: states.GameState, board: chess.Board, game_id) -> states.GameState:
    print_choices_menu(state)
    while (opt := atoi(input("Choose your action: "))) not in range(1, len(states.TRANSITIONS[state].keys()) + 1):
        print("Please, choose a valid action (only the action number)!")
        print_choices_menu(state)
    
    action = list(states.TRANSITIONS[state].keys())[opt - 1]
    
    if action == states.GameAction.MOVE:
        handle_move(board, game_id)
    elif action == states.GameAction.OFFER_DRAW:
        client.board.offer_draw(game_id)
    elif action == states.GameAction.OFFER_TAKEBACK:
        client.board.offer_takeback(game_id)
    elif action == states.GameAction.ACCEPT:
        if state in [states.GameState.BHANDLING_DRAW, states.GameState.WHANDLING_DRAW]:
            client.board.accept_draw(game_id)
        else:
            client.board.accept_takeback(game_id)
            board.pop()
            board.pop()
            print(board)
    elif action == states.GameAction.DECLINE:
        if state in [states.GameState.BHANDLING_DRAW, states.GameState.WHANDLING_DRAW]:
            client.board.decline_draw(game_id)
        else:
            client.board.decline_takeback(game_id)
    elif action == states.GameAction.RESIGN:
        client.board.resign_game(game_id)

    return states.handle_transition(state, action)

def is_legal_move(board: chess.Board, move: str):
    try:
        return board.is_legal(chess.Move.from_uci(move))
    except chess.InvalidMoveError:
        print("Invalid UCI move string!")
        return False

def handle_move(board: chess.Board, game_id: str):
    move = input("Make your move: ")
    while not is_legal_move(board, move):
        move = input("Make a legal move: ")
    board.push_uci(move)
    print(board)
    client.board.make_move(game_id, move)

def create_new_game_ai():
    color = random.choice(["black", "white"])
    while int(level := input("Select AI level [1-8]: ")) not in range(1, 9): pass
    game = client.challenges.create_ai(level=level, color=color)
    game_id = game["id"]
    state = states.start_game()
    print(f"https://lichess.org/{game_id}")
    game_stream = client.board.stream_game_state(game_id)
    full_game = next(game_stream) 
    print(full_game)
    board = chess.Board(game["fen"])
    print(board)
    color_id = 1 if color == "black" else 0 
    print("---------------------------")

    try:
        # In case of the first state already has a move
        if len(full_game["state"]["moves"].split()) == 1: 
            states.push_state(states.GameState.BLACKS_TURN)
            state = states.GameState.BLACKS_TURN
        
        state = handle_lichess_gameState(state, full_game["state"], board, color_id, game_id)
        states.push_state(state)

        for event in game_stream:
            print(event)
            if event["type"] == "gameState":
                if event["status"] == "started":
                    state = handle_lichess_gameState(state, event, board, color_id, game_id)
                    states.push_state(state)
        print(state.value)
    except Exception as err:
        client.board.resign_game(game_id)
        print(f"Error occured: {err}")
        print("Game aborted")

def create_new_game_player():
    color = random.choice(["black", "white"])
    # while int(level := input("Select AI level [1-8]: ")) not in range(1, 9): pass
    stream = client.board.stream_incoming_events()
    client.board.seek(time=15, increment=60, color=color)
    for e in stream:
        if e["type"] == "gameStart":
            game = e["game"]
            game_id = game["id"]
            state = states.start_game()
            print(f"https://lichess.org/{game_id}")
            game_stream = client.board.stream_game_state(game_id)
            full_game = next(game_stream) 
            print(full_game)
            board = chess.Board(game["fen"])
            print(board)
            color_id = 1 if color == "black" else 0 
            print("---------------------------")

            try:
                # In case of the first state already has a move
                if len(full_game["state"]["moves"].split()) == 1: 
                    states.push_state(states.GameState.BLACKS_TURN)
                    state = states.GameState.BLACKS_TURN
                
                state = handle_lichess_gameState(state, full_game["state"], board, color_id, game_id)
                states.push_state(state)

                for event in game_stream:
                    print(event)
                    if event["type"] == "gameState":
                        if event["status"] == "started":
                            state = handle_lichess_gameState(state, event, board, color_id, game_id)
                            states.push_state(state)
                print(state.value)
            except Exception as err:
                client.board.resign_game(game_id)
                print(f"Error occured: {err}")
                print("Game aborted")

def print_menu() -> str:
    return input("1- New game against AI\n2- New game against player\n3- Quit\n")

def main() -> None:
    while (opt := print_menu()) != "3":
        if opt == "1": create_new_game_ai()
        if opt == "2": create_new_game_player()

if __name__ == "__main__":
    main()