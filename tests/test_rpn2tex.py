"""Tests for rpn2tex - demonstrates usage of each module.

These tests serve as both validation and documentation of the rpn2tex API.
Run with: hatch run test

Compare with txt2tex/tests/ for comprehensive test patterns.
"""

import pytest

from rpn2tex.ast_nodes import BinaryOp, Number
from rpn2tex.errors import ErrorFormatter
from rpn2tex.latex_gen import LaTeXGenerator
from rpn2tex.lexer import Lexer, LexerError
from rpn2tex.parser import Parser, ParserError
from rpn2tex.tokens import TokenType


class TestLexer:
    """Test the lexer module."""

    def test_single_number(self) -> None:
        """Lexer tokenizes a single number."""
        tokens = Lexer("42").tokenize()
        assert len(tokens) == 2
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "42"
        assert tokens[1].type == TokenType.EOF

    def test_decimal_number(self) -> None:
        """Lexer tokenizes decimal numbers."""
        tokens = Lexer("3.14").tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "3.14"

    def test_negative_number(self) -> None:
        """Lexer tokenizes negative numbers."""
        tokens = Lexer("-5").tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "-5"

    def test_negative_number2(self) -> None:
        """Lexer tokenizes negative numbers."""
        tokens = Lexer("-3.14").tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "-3.14"

    def test_operators(self) -> None:
        """Lexer tokenizes all operators."""
        tokens = Lexer("+ - * /").tokenize()
        types = [t.type for t in tokens[:-1]]  # Exclude EOF
        assert types == [
            TokenType.PLUS,
            TokenType.MINUS,
            TokenType.MULT,
            TokenType.DIV,
        ]

    def test_simple_expression(self) -> None:
        """Lexer tokenizes '5 3 +' correctly."""
        tokens = Lexer("5 3 +").tokenize()
        assert len(tokens) == 4
        assert tokens[0].value == "5"
        assert tokens[1].value == "3"
        assert tokens[2].type == TokenType.PLUS

    def test_position_tracking(self) -> None:
        """Lexer tracks line and column positions."""
        tokens = Lexer("5 3 +").tokenize()
        assert tokens[0].line == 1
        assert tokens[0].column == 1
        assert tokens[1].column == 3
        assert tokens[2].column == 5

    def test_multiline(self) -> None:
        """Lexer handles multiline input."""
        tokens = Lexer("5\n3\n+").tokenize()
        assert tokens[0].line == 1
        assert tokens[1].line == 2
        assert tokens[2].line == 3

    def test_invalid_character(self) -> None:
        """Lexer raises error for invalid characters."""
        with pytest.raises(LexerError) as exc_info:
            Lexer("5 @").tokenize()
        assert "Unexpected character '@'" in str(exc_info.value)


class TestParser:
    """Test the parser module."""

    def test_single_number(self) -> None:
        """Parser handles single number."""
        tokens = Lexer("42").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, Number)
        assert ast.value == "42"

    def test_simple_addition(self) -> None:
        """Parser handles '5 3 +' -> 5 + 3."""
        tokens = Lexer("5 3 +").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "+"
        assert isinstance(ast.left, Number)
        assert ast.left.value == "5"
        assert isinstance(ast.right, Number)
        assert ast.right.value == "3"

    def test_compound_expression(self) -> None:
        """Parser handles '2 3 + 4 *' -> (2 + 3) * 4."""
        tokens = Lexer("2 3 + 4 *").tokenize()
        ast = Parser(tokens).parse()
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "*"
        # Left operand is (2 + 3)
        assert isinstance(ast.left, BinaryOp)
        assert ast.left.operator == "+"
        # Right operand is 4
        assert isinstance(ast.right, Number)
        assert ast.right.value == "4"

    def test_all_operators(self) -> None:
        """Parser handles all four operators."""
        for op_char, op_token in [("+", "+"), ("-", "-"), ("*", "*"), ("/", "/")]:
            tokens = Lexer(f"5 3 {op_char}").tokenize()
            ast = Parser(tokens).parse()
            assert isinstance(ast, BinaryOp)
            assert ast.operator == op_token

    def test_empty_input(self) -> None:
        """Parser raises error for empty input."""
        tokens = Lexer("").tokenize()
        with pytest.raises(ParserError) as exc_info:
            Parser(tokens).parse()
        assert "Empty expression" in str(exc_info.value)

    def test_not_enough_operands(self) -> None:
        """Parser raises error when operator lacks operands."""
        tokens = Lexer("5 +").tokenize()
        with pytest.raises(ParserError) as exc_info:
            Parser(tokens).parse()
        assert "requires two operands" in str(exc_info.value)

    def test_too_many_operands(self) -> None:
        """Parser raises error when values remain on stack."""
        tokens = Lexer("5 3 2").tokenize()
        with pytest.raises(ParserError) as exc_info:
            Parser(tokens).parse()
        assert "remain on stack" in str(exc_info.value)


class TestLaTeXGenerator:
    """Test the LaTeX generator module."""

    def test_single_number(self) -> None:
        """Generator outputs number in math mode."""
        ast = Number(line=1, column=1, value="42")
        latex = LaTeXGenerator().generate(ast)
        assert latex == "$42$"

    def test_simple_addition(self) -> None:
        """Generator outputs a + b correctly."""
        ast = BinaryOp(
            line=1,
            column=1,
            operator="+",
            left=Number(1, 1, "5"),
            right=Number(1, 3, "3"),
        )
        latex = LaTeXGenerator().generate(ast)
        assert latex == "$5 + 3$"

    def test_multiplication_symbol(self) -> None:
        """Generator uses \\times for multiplication."""
        ast = BinaryOp(
            line=1,
            column=1,
            operator="*",
            left=Number(1, 1, "5"),
            right=Number(1, 3, "3"),
        )
        latex = LaTeXGenerator().generate(ast)
        assert latex == r"$5 \times 3$"

    def test_division_symbol(self) -> None:
        """Generator uses \\div for division."""
        ast = BinaryOp(
            line=1,
            column=1,
            operator="/",
            left=Number(1, 1, "6"),
            right=Number(1, 3, "2"),
        )
        latex = LaTeXGenerator().generate(ast)
        assert latex == r"$6 \div 2$"

    def test_precedence_parens(self) -> None:
        """Generator adds parentheses for precedence."""
        # (5 + 3) * 2 - addition needs parens
        inner = BinaryOp(
            line=1,
            column=1,
            operator="+",
            left=Number(1, 1, "5"),
            right=Number(1, 3, "3"),
        )
        outer = BinaryOp(
            line=1,
            column=5,
            operator="*",
            left=inner,
            right=Number(1, 7, "2"),
        )
        latex = LaTeXGenerator().generate(outer)
        assert latex == r"$( 5 + 3 ) \times 2$"

    def test_no_unnecessary_parens(self) -> None:
        """Generator omits unnecessary parentheses."""
        # 5 * 3 + 2 - no parens needed (correct precedence)
        inner = BinaryOp(
            line=1,
            column=1,
            operator="*",
            left=Number(1, 1, "5"),
            right=Number(1, 3, "3"),
        )
        outer = BinaryOp(
            line=1,
            column=5,
            operator="+",
            left=inner,
            right=Number(1, 7, "2"),
        )
        latex = LaTeXGenerator().generate(outer)
        assert latex == r"$5 \times 3 + 2$"


class TestErrorFormatter:
    """Test the error formatter module."""

    def test_basic_error(self) -> None:
        """ErrorFormatter formats basic error with context."""
        formatter = ErrorFormatter("5 3 @")
        result = formatter.format_error("Unexpected character '@'", 1, 5)
        assert "Unexpected character '@'" in result
        assert "5 3 @" in result
        assert "^" in result

    def test_caret_position(self) -> None:
        """ErrorFormatter positions caret correctly."""
        formatter = ErrorFormatter("5 3 @")
        result = formatter.format_error("Error", 1, 5)
        lines = result.split("\n")
        # Find the caret line
        caret_line = next(ln for ln in lines if "^" in ln and "|" in ln)
        # Count position after "| "
        caret_idx = caret_line.index("^") - caret_line.index("|") - 2
        assert caret_idx == 4  # 0-indexed column 4 = 1-indexed column 5


class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_full_pipeline_simple(self) -> None:
        """Full pipeline: '5 3 +' -> '$5 + 3$'."""
        text = "5 3 +"
        tokens = Lexer(text).tokenize()
        ast = Parser(tokens).parse()
        latex = LaTeXGenerator().generate(ast)
        assert latex == "$5 + 3$"

    def test_full_pipeline_compound(self) -> None:
        """Full pipeline: '2 3 + 4 *' -> '$( 2 + 3 ) \\times 4$'."""
        text = "2 3 + 4 *"
        tokens = Lexer(text).tokenize()
        ast = Parser(tokens).parse()
        latex = LaTeXGenerator().generate(ast)
        assert latex == r"$( 2 + 3 ) \times 4$"

    def test_full_pipeline_complex(self) -> None:
        """Full pipeline: '10 2 / 3 + 4 2 * -' -> complex expression.

        Evaluates to: ((10 / 2) + 3) - (4 * 2)
        """
        text = "10 2 / 3 + 4 2 * -"
        tokens = Lexer(text).tokenize()
        ast = Parser(tokens).parse()
        latex = LaTeXGenerator().generate(ast)
        # Should have division and multiplication symbols
        assert r"\div" in latex
        assert r"\times" in latex
