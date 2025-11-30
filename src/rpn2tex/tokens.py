"""Token types and definitions for rpn2tex lexer.

This module defines the token types recognized by the RPN lexer.
Compare with txt2tex/tokens.py for the full implementation.

Token Types:
    NUMBER: Numeric literals (integers and decimals)
    PLUS: Addition operator (+)
    MINUS: Subtraction operator (-)
    MULT: Multiplication operator (*)
    DIV: Division operator (/)
    EOF: End of file marker

Exercise tokens (not implemented):
    CARET: Exponentiation operator (^)
    SQRT: Square root function (sqrt)
    ROOT: Nth root function (root)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    """Token types for rpn2tex lexer.

    Each token type represents a distinct lexical element in RPN expressions.
    """

    # Literals
    NUMBER = auto()  # Numeric values: 5, 3.14, -2

    # Operators
    PLUS = auto()  # + (addition)
    MINUS = auto()  # - (subtraction)
    MULT = auto()  # * (multiplication)
    DIV = auto()  # / (division)

    # Exercise: Add CARET, SQRT, ROOT token types here
    # See README.md for implementation hints

    # Special
    EOF = auto()  # End of input


@dataclass(frozen=True)
class Token:
    """A lexical token with type, value, and position.

    Attributes:
        type: The token type (from TokenType enum)
        value: The string value of the token
        line: Line number (1-based) where token appears
        column: Column number (1-based) where token starts

    Example:
        >>> Token(TokenType.NUMBER, "42", 1, 5)
        Token(NUMBER, '42', 1:5)
    """

    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"
