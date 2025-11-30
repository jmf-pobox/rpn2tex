"""AST node definitions for rpn2tex parser.

This module defines the Abstract Syntax Tree (AST) nodes used to represent
parsed RPN expressions. Compare with txt2tex/ast_nodes.py for the full
implementation with many more node types.

AST nodes are immutable dataclasses that represent the structure of
mathematical expressions. Each node carries position information for
error reporting.

Node Types:
    Number: Numeric literals (5, 3.14, -2)
    BinaryOp: Binary operations (a + b, x * y)

Exercise nodes (not implemented):
    Exponent: Exponentiation (base^exponent)
    SquareRoot: Square root (√x)
    NthRoot: Nth root (ⁿ√x)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ASTNode:
    """Base class for all AST nodes.

    All AST nodes track their position in source for error reporting.

    Attributes:
        line: Line number (1-based) where node appears
        column: Column number (1-based) where node starts
    """

    line: int
    column: int


@dataclass(frozen=True)
class Number(ASTNode):
    """Numeric literal node.

    Represents integer and decimal numbers in expressions.

    Attributes:
        value: The string representation of the number

    Example:
        >>> Number(line=1, column=1, value="42")
        Number(line=1, column=1, value='42')
    """

    value: str


@dataclass(frozen=True)
class BinaryOp(ASTNode):
    """Binary operation node.

    Represents operations with two operands: +, -, *, /

    Attributes:
        operator: The operator string ("+", "-", "*", "/")
        left: The left operand expression
        right: The right operand expression

    Example:
        >>> # Represents "5 + 3"
        >>> BinaryOp(
        ...     line=1, column=3,
        ...     operator="+",
        ...     left=Number(1, 1, "5"),
        ...     right=Number(1, 3, "3")
        ... )
    """

    operator: str
    left: Expr
    right: Expr


# Exercise: Add Exponent, SquareRoot, and NthRoot node types here.
# See README.md for implementation hints.


# Type alias for all expression types.
# Exercise: Add new node types to this union when implementing exercises.
Expr = Number | BinaryOp
