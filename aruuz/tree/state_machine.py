"""
State machine for special meter detection.

This module implements state machines for detecting special meters
like Hindi and Zamzama meters.
"""

# State transition tables for different meter types

# Hindi meter transition table
# Maps input code ("-" or "=") to state transitions based on current state
_HINDI_METER_TRANSITION = {
    "-": [2, 4, -1, 0, 5, -1, 7, -1],
    "=": [1, 0, 3, -1, 6, 1, -1, 0]
}

# Zamzama meter transition table
_ZAMZAMA_METER_TRANSITION = {
    "-": [1, 2, -1, -1],
    "=": [3, -1, 0, 0]
}

# Original Hindi meter transition table
_ORIGINAL_HINDI_METER_TRANSITION = {
    "-": [-1, 2, 3, -1],
    "=": [1, 0, -1, 1]
}


def _next_state(transition: dict, code: str, state: int) -> int:
    """
    Get next state from transition table.
    
    Args:
        transition: Dictionary mapping codes to state transition arrays
        code: Input code ("-" or "=")
        state: Current state index
        
    Returns:
        Next state value, or -1 if transition is invalid or out of bounds
    """
    try:
        return transition[code][state]
    except (KeyError, IndexError):
        return -1


def hindi_meter(code: str, state: int) -> int:
    """
    Get next state for Hindi meter state machine.
    
    Args:
        code: Input code ("-" for short syllable, "=" for long syllable)
        state: Current state (0-7)
        
    Returns:
        Next state, or -1 if transition is invalid
    """
    return _next_state(_HINDI_METER_TRANSITION, code, state)


def zamzama_meter(code: str, state: int) -> int:
    """
    Get next state for Zamzama meter state machine.
    
    Args:
        code: Input code ("-" for short syllable, "=" for long syllable)
        state: Current state (0-3)
        
    Returns:
        Next state, or -1 if transition is invalid
    """
    return _next_state(_ZAMZAMA_METER_TRANSITION, code, state)


def original_hindi_meter(code: str, state: int) -> int:
    """
    Get next state for Original Hindi meter state machine.
    
    Args:
        code: Input code ("-" for short syllable, "=" for long syllable)
        state: Current state (0-3)
        
    Returns:
        Next state, or -1 if transition is invalid
    """
    return _next_state(_ORIGINAL_HINDI_METER_TRANSITION, code, state)
