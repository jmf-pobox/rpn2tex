"""Parser for rpn2tex - converts tokens into AST.

This module implements a stack-based RPN (Reverse Polish Notation) parser.
Compare with txt2tex/parser.py which uses recursive descent for infix notation.

RPN Parsing Algorithm:
    1. When you see a number, push it onto the stack
    2. When you see an operator, pop operands, create a node, push result
    3. At EOF, the stack should contain exactly one element: the AST root

Example:
    Input: "5 3 + 2 *"
    Stack evolution:
        5       -> [5]
        3       -> [5, 3]
        +       -> [5+3]
        2       -> [5+3, 2]
        *       -> [(5+3)*2]
    Result: BinaryOp("*", BinaryOp("+", 5, 3), 2)

Key concepts demonstrated:
    - Stack-based parsing (simpler than recursive descent)
    - Token consumption
    - AST construction
    - Error handling with token context
"""

from __future__ import annotations

from rpn2tex.ast_nodes import BinaryOp, Expr, Number
from rpn2tex.tokens import Token, TokenType


class ParserError(Exception):
    """Raised when parser encounters invalid input.

    Attributes:
        message: Description of the error
        token: The token where error occurred

    Example:
        >>> token = Token(TokenType.PLUS, "+", 1, 5)
        >>> raise ParserError("Not enough operands", token)
        ParserError: Not enough operands at line 1, column 5
    """

    message: str
    token: Token

    def __init__(self, message: str, token: Token) -> None:
        """Initialize parser error with token context."""
        super().__init__(f"{message} at line {token.line}, column {token.column}")
        self.message = message
        self.token = token


class Parser:
    """Stack-based RPN parser.

    Converts a token stream into an Abstract Syntax Tree.
    Uses a stack to accumulate operands and build expression trees
    when operators are encountered.

    Attributes:
        tokens: List of tokens to parse
        pos: Current position in token list

    Example:
        >>> from rpn2tex.lexer import Lexer
        >>> tokens = Lexer("5 3 +").tokenize()
        >>> ast = Parser(tokens).parse()
        >>> isinstance(ast, BinaryOp)
        True
    """

    tokens: list[Token]
    pos: int

    def __init__(self, tokens: list[Token]) -> None:
        """Initialize parser with token list.

        Args:
            tokens: List of tokens from lexer (must end with EOF)
        """
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> Expr:
        """Parse tokens into an AST.

        Returns:
            The root expression node of the AST.

        Raises:
            ParserError: If the input is invalid RPN.

        Example:
            >>> tokens = Lexer("2 3 + 4 *").tokenize()
            >>> ast = Parser(tokens).parse()
            >>> # Result: (2 + 3) * 4
        """
        stack: list[Expr] = []

        while not self._at_end():
            token: Token = self._current()

            if token.type == TokenType.NUMBER:
                # Push number onto stack
                num_node = Number(
                    line=token.line, column=token.column, value=token.value
                )
                stack.append(num_node)
                self._advance()

            elif token.type in (
                TokenType.PLUS,
                TokenType.MINUS,
                TokenType.MULT,
                TokenType.DIV,
            ):
                # Pop two operands and create binary operation
                if len(stack) < 2:
                    raise ParserError(
                        f"Operator '{token.value}' requires two operands", token
                    )

                right = stack.pop()
                left = stack.pop()

                # Map token type to operator string
                op_map = {
                    TokenType.PLUS: "+",
                    TokenType.MINUS: "-",
                    TokenType.MULT: "*",
                    TokenType.DIV: "/",
                }
                operator = op_map[token.type]

                op_node = BinaryOp(
                    line=token.line,
                    column=token.column,
                    operator=operator,
                    left=left,
                    right=right,
                )
                stack.append(op_node)
                self._advance()

            elif token.type == TokenType.EOF:
                break

            else:
                raise ParserError(f"Unexpected token '{token.value}'", token)

        # Validate final state
        if len(stack) == 0:
            eof_token = self.tokens[-1]
            raise ParserError("Empty expression", eof_token)

        if len(stack) > 1:
            # Find the first unconsumed operand for error location
            raise ParserError(
                f"Invalid RPN: {len(stack)} values remain on stack "
                "(missing operators?)",
                self.tokens[-1],
            )

        return stack[0]

    def _current(self) -> Token:
        """Get the current token."""
        return self.tokens[self.pos]

    def _at_end(self) -> bool:
        """Check if we've reached EOF."""
        return self.tokens[self.pos].type == TokenType.EOF

    def _advance(self) -> Token:
        """Consume and return current token, advance to next."""
        token = self.tokens[self.pos]
        if not self._at_end():
            self.pos += 1
        return token
