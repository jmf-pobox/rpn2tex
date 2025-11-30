"""LaTeX generator for rpn2tex - converts AST to LaTeX.

This module converts the AST into LaTeX math mode output.
Compare with txt2tex/latex_gen.py for the full implementation.

Key concepts demonstrated:
    - Visitor pattern using @singledispatchmethod
    - Operator precedence for parenthesization
    - LaTeX math mode output

The generator produces infix notation from the parsed RPN tree:
    Input RPN: "5 3 + 2 *"
    AST: BinaryOp("*", BinaryOp("+", 5, 3), 2)
    Output: "$( 5 + 3 ) \\times 2$"
"""

from __future__ import annotations

from functools import singledispatchmethod
from typing import ClassVar

from rpn2tex.ast_nodes import BinaryOp, Expr, Number


class LaTeXGenerator:
    """Converts rpn2tex AST to LaTeX source code.

    Uses the visitor pattern via @singledispatchmethod to handle
    different node types. Manages operator precedence to insert
    parentheses only where needed.

    Class Attributes:
        BINARY_OPS: Mapping from operator strings to LaTeX commands
        PRECEDENCE: Operator precedence levels (higher = tighter binding)

    Example:
        >>> from rpn2tex.lexer import Lexer
        >>> from rpn2tex.parser import Parser
        >>> tokens = Lexer("5 3 +").tokenize()
        >>> ast = Parser(tokens).parse()
        >>> latex = LaTeXGenerator().generate(ast)
        >>> print(latex)
        $5 + 3$
    """

    # Operator to LaTeX mapping
    BINARY_OPS: ClassVar[dict[str, str]] = {
        "+": "+",
        "-": "-",
        "*": r"\times",
        "/": r"\div",
    }

    # Operator precedence (higher = binds tighter)
    # Addition/subtraction: level 1
    # Multiplication/division: level 2
    PRECEDENCE: ClassVar[dict[str, int]] = {
        "+": 1,
        "-": 1,
        "*": 2,
        "/": 2,
    }

    def generate(self, ast: Expr) -> str:
        """Generate LaTeX from AST.

        Args:
            ast: The root expression node

        Returns:
            LaTeX string wrapped in math delimiters ($...$)

        Example:
            >>> ast = BinaryOp(1, 1, "+", Number(1, 1, "5"), Number(1, 3, "3"))
            >>> LaTeXGenerator().generate(ast)
            '$5 + 3$'
        """
        content = self._visit(ast)
        return f"${content}$"

    @singledispatchmethod
    def _visit(self, node: Expr) -> str:
        """Visit an AST node and generate LaTeX.

        This is the dispatcher for the visitor pattern.
        Specific node types are handled by registered implementations.

        Args:
            node: The AST node to visit

        Returns:
            LaTeX string for the node

        Raises:
            NotImplementedError: For unhandled node types
        """
        raise NotImplementedError(f"No visitor for {type(node).__name__}")

    @_visit.register
    def _visit_number(self, node: Number) -> str:
        """Generate LaTeX for a number literal.

        Args:
            node: The Number node

        Returns:
            The number value as a string
        """
        return node.value

    @_visit.register
    def _visit_binary_op(self, node: BinaryOp) -> str:
        """Generate LaTeX for a binary operation.

        Handles operator precedence by adding parentheses around
        lower-precedence sub-expressions.

        Args:
            node: The BinaryOp node

        Returns:
            LaTeX string with appropriate parentheses

        Example:
            >>> # For "5 3 + 2 *" -> (5 + 3) * 2
            >>> # The addition needs parens because * has higher precedence
        """
        op_latex = self.BINARY_OPS[node.operator]
        my_precedence = self.PRECEDENCE[node.operator]

        # Generate left operand, adding parens if needed
        left = self._visit(node.left)
        if self._needs_parens(node.left, my_precedence, is_right=False):
            left = f"( {left} )"

        # Generate right operand, adding parens if needed
        right = self._visit(node.right)
        if self._needs_parens(node.right, my_precedence, is_right=True):
            right = f"( {right} )"

        return f"{left} {op_latex} {right}"

    def _needs_parens(
        self, child: Expr, parent_precedence: int, *, is_right: bool
    ) -> bool:
        """Determine if a child expression needs parentheses.

        Parentheses are needed when:
        1. Child has lower precedence than parent
        2. Child has equal precedence and is on the right side
           (for left-associative operators like -)

        Args:
            child: The child expression
            parent_precedence: Precedence of the parent operator
            is_right: True if child is the right operand

        Returns:
            True if parentheses are needed

        Example:
            >>> # 5 - (3 - 2) needs parens on right
            >>> # (5 - 3) - 2 doesn't need parens (left-associative)
        """
        if not isinstance(child, BinaryOp):
            return False

        child_precedence = self.PRECEDENCE[child.operator]

        # Lower precedence always needs parens
        if child_precedence < parent_precedence:
            return True

        # Equal precedence on right side needs parens for non-commutative operators
        # (handles left-associativity of - and /)
        return (
            child_precedence == parent_precedence
            and is_right
            and child.operator in ("-", "/")
        )


# Exercise: Add visitors for Exponent, SquareRoot, and NthRoot here.
# See README.md for implementation hints.
