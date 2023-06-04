from __future__ import annotations
from enum import Enum
from typing import Callable

class GameState(Enum):
	WHITES_TURN        = "White's turn!"
	BLACKS_TURN        = "Black's turn!"
	WHANDLING_DRAW     = "Black offered a draw!"
	WHANDLING_TAKEBACK = "Black offered a takeback!"
	BHANDLING_DRAW     = "White offered a draw!"
	BHANDLING_TAKEBACK = "White offered a takeback!"
	WHITE_WINS         = "White wins!"
	BLACK_WINS         = "Black wins!"
	DRAW               = "Draw!"

class GameAction(Enum):
	MOVE           = "Move"
	OFFER_DRAW     = "Offer draw"
	OFFER_TAKEBACK = "Offer takeback"
	ACCEPT         = "Accept"
	DECLINE        = "Decline"
	RESIGN         = "Resign"

TRANSITIONS: dict[GameState, dict[GameAction, Callable[[], GameState]]] = {
	GameState.WHITES_TURN: {
		GameAction.MOVE:           lambda: GameState.BLACKS_TURN,
		GameAction.OFFER_DRAW:     lambda: GameState.BHANDLING_DRAW,
		GameAction.OFFER_TAKEBACK: lambda: GameState.BHANDLING_TAKEBACK,
		GameAction.RESIGN:         lambda: GameState.BLACK_WINS,
	},
	GameState.BLACKS_TURN: {
		GameAction.MOVE:           lambda: GameState.WHITES_TURN,
		GameAction.OFFER_DRAW:     lambda: GameState.WHANDLING_DRAW,
		GameAction.OFFER_TAKEBACK: lambda: GameState.WHANDLING_TAKEBACK,
		GameAction.RESIGN:         lambda: GameState.WHITE_WINS,
	},
	GameState.WHANDLING_DRAW: {
		GameAction.ACCEPT:  lambda: GameState.DRAW,
		GameAction.DECLINE: lambda: _state_history[-2:][0], # maintain last state
	},
	GameState.BHANDLING_DRAW: {
		GameAction.ACCEPT:  lambda: GameState.DRAW,
		GameAction.DECLINE: lambda: _state_history[-2:][0], # maintain last state
	},
	GameState.WHANDLING_TAKEBACK: {
		GameAction.ACCEPT:  lambda: GameState.BLACKS_TURN,
		GameAction.DECLINE: lambda: _state_history[-2:][0], # maintain last state
	},
	GameState.BHANDLING_TAKEBACK: {
		GameAction.ACCEPT:  lambda: GameState.WHITES_TURN,
		GameAction.DECLINE: lambda: _state_history[-2:][0], # maintain last state
	},
	GameState.DRAW:       {},
	GameState.WHITE_WINS: {},
	GameState.BLACK_WINS: {},
}

_state_history = []

def start_game() -> GameState:
	_state_history.clear()
	_state_history.append(GameState.WHITES_TURN)
	return _state_history[0]

def handle_transition(state: GameState, action: GameAction) -> GameState:
	if action not in TRANSITIONS[state].keys():
		raise ValueError(f"Invalid `{action}` action for state: {state}. This error should never happen, so it's certainly a bug")
	return TRANSITIONS[state].get(action)()

def push_state(state: GameState) -> None:
	_state_history.append(state)