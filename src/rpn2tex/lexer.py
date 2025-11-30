"""Lexer for rpn2tex - converts text into tokens.

This module tokenizes RPN (Reverse Polish Notation) expressions.
Compare with txt2tex/lexer.py for the full implementation.

The lexer converts input text like "5 3 +" into a stream of tokens:
    [Token(NUMBER, "5"), Token(NUMBER, "3"), Token(PLUS, "+"), Token(EOF, "")]

Key concepts demonstrated:
    - Character-by-character scanning
    - Position tracking (line, column)
    - Token generation
    - Error handling with position information
"""

from __future__ import annotations

from rpn2tex.tokens import Token, TokenType


class LexerError(Exception):
    """Raised when lexer encounters invalid input.

    Attributes:
        message: Description of the error
        line: Line number where error occurred (1-based)
        column: Column number where error occurred (1-based)

    Example:
        >>> raise LexerError("Unexpected character '@'", 1, 5)
        LexerError: Line 1, column 5: Unexpected character '@'
    """

    message: str
    line: int
    column: int

    def __init__(self, message: str, line: int, column: int) -> None:
        """Initialize lexer error with position."""
        super().__init__(f"Line {line}, column {column}: {message}")
        self.message = message
        self.line = line
        self.column = column


class Lexer:
    """Tokenizes RPN input text.

    The lexer scans input character by character, producing tokens for:
        - Numbers (integers and decimals)
        - Operators (+, -, *, /)
        - EOF marker

    Whitespace is used as a delimiter and is otherwise ignored.

    Attributes:
        text: The input text to tokenize
        pos: Current position in text (0-based)
        line: Current line number (1-based)
        column: Current column number (1-based)

    Example:
        >>> lexer = Lexer("5 3 +")
        >>> tokens = lexer.tokenize()
        >>> [t.type.name for t in tokens]
        ['NUMBER', 'NUMBER', 'PLUS', 'EOF']
    """

    text: str
    pos: int
    line: int
    column: int

    def __init__(self, text: str) -> None:
        """Initialize lexer with input text.

        Args:
            text: The RPN expression to tokenize
        """
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> list[Token]:
        """Tokenize the entire input text.

        Returns:
            List of tokens, ending with EOF token.

        Raises:
            LexerError: If an invalid character is encountered.

        Example:
            >>> Lexer("2 3 + 4 *").tokenize()
            [Token(NUMBER, '2', 1:1), Token(NUMBER, '3', 1:3), ...]
        """
        tokens: list[Token] = []

        while not self._at_end():
            self._skip_whitespace()
            if self._at_end():
                break
            tokens.append(self._scan_token())

        # Add EOF token
        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens

    def _at_end(self) -> bool:
        """Check if we've reached the end of input."""
        return self.pos >= len(self.text)

    def _peek(self) -> str:
        """Look at current character without consuming it."""
        if self._at_end():
            return ""
        return self.text[self.pos]

    def _advance(self) -> str:
        """Consume and return the current character."""
        char = self.text[self.pos]
        self.pos += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def _skip_whitespace(self) -> None:
        """Skip over whitespace characters."""
        while not self._at_end() and self._peek() in " \t\n\r":
            self._advance()

    def _scan_token(self) -> Token:
        """Scan and return the next token.

        Returns:
            The next token from the input.

        Raises:
            LexerError: If an invalid character is encountered.
        """
        start_line = self.line
        start_column = self.column
        char = self._peek()

        # Single-character operators
        if char == "+":
            self._advance()
            return Token(TokenType.PLUS, "+", start_line, start_column)
        if char == "-":
            # Could be negative number or subtraction operator
            # In RPN, standalone "-" is always subtraction
            # Negative numbers are written as "0 5 -" or handled specially
            self._advance()
            # Check if this is a negative number (digit follows immediately)
            if not self._at_end() and self._peek().isdigit():
                # It's a negative number
                return self._scan_number("-", start_line, start_column)
            return Token(TokenType.MINUS, "-", start_line, start_column)
        if char == "*":
            self._advance()
            return Token(TokenType.MULT, "*", start_line, start_column)
        if char == "/":
            self._advance()
            return Token(TokenType.DIV, "/", start_line, start_column)

        # Numbers
        if char.isdigit():
            return self._scan_number("", start_line, start_column)

        # Unknown character
        raise LexerError(f"Unexpected character '{char}'", start_line, start_column)

    def _scan_number(self, prefix: str, start_line: int, start_column: int) -> Token:
        """Scan a numeric literal.

        Args:
            prefix: Any prefix already consumed (e.g., "-" for negatives)
            start_line: Line where number started
            start_column: Column where number started

        Returns:
            A NUMBER token.
        """
        value = prefix

        # Integer part
        while not self._at_end() and self._peek().isdigit():
            value += self._advance()

        # Decimal part (optional)
        if not self._at_end() and self._peek() == ".":
            value += self._advance()  # consume '.'
            while not self._at_end() and self._peek().isdigit():
                value += self._advance()

        return Token(TokenType.NUMBER, value, start_line, start_column)
