"""Command-line interface for rpn2tex.

This module provides the CLI entry point that orchestrates
the pipeline: read → tokenize → parse → generate → write.
Compare with txt2tex/cli.py for the full implementation.

Usage:
    rpn2tex input.rpn              # Output to stdout
    rpn2tex input.rpn -o out.tex   # Output to file
    echo "5 3 +" | rpn2tex -       # Read from stdin

Key concepts demonstrated:
    - argparse argument parsing
    - Error handling with exit codes
    - Pipeline orchestration
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rpn2tex.errors import ErrorFormatter
from rpn2tex.latex_gen import LaTeXGenerator
from rpn2tex.lexer import Lexer, LexerError
from rpn2tex.parser import Parser, ParserError


def main() -> int:
    """Main entry point for rpn2tex CLI.

    Returns:
        Exit code: 0 for success, 1 for error.
    """
    parser = argparse.ArgumentParser(
        description="Convert RPN expressions to LaTeX math mode",
        prog="rpn2tex",
        epilog="Example: rpn2tex input.rpn -o output.tex",
    )
    parser.add_argument(
        "input",
        type=str,
        help="Input RPN file (use '-' for stdin)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output LaTeX file (default: stdout)",
    )

    args = parser.parse_args()

    # Read input
    try:
        if args.input == "-":
            text = sys.stdin.read()
        else:
            input_path = Path(args.input)
            text = input_path.read_text()
    except FileNotFoundError:
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        return 1
    except PermissionError:
        print(f"Error: Permission denied reading: {args.input}", file=sys.stderr)
        return 1
    except IsADirectoryError:
        print(f"Error: Expected a file, got a directory: {args.input}", file=sys.stderr)
        return 1

    # Process: tokenize → parse → generate
    formatter = ErrorFormatter(text)
    try:
        # Tokenize
        lexer = Lexer(text)
        tokens = lexer.tokenize()

        # Parse
        parser_obj = Parser(tokens)
        ast = parser_obj.parse()

        # Generate LaTeX
        generator = LaTeXGenerator()
        latex = generator.generate(ast)

    except LexerError as e:
        formatted = formatter.format_error(e.message, e.line, e.column)
        print(formatted, file=sys.stderr)
        return 1
    except ParserError as e:
        formatted = formatter.format_error(e.message, e.token.line, e.token.column)
        print(formatted, file=sys.stderr)
        return 1

    # Write output
    if args.output is not None:
        try:
            args.output.write_text(latex + "\n")
            print(f"Generated: {args.output}", file=sys.stderr)
        except PermissionError:
            print(f"Error: Permission denied writing: {args.output}", file=sys.stderr)
            return 1
        except IsADirectoryError:
            print(f"Error: Cannot write to directory: {args.output}", file=sys.stderr)
            return 1
    else:
        print(latex)

    return 0


if __name__ == "__main__":
    sys.exit(main())
