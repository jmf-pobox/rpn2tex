"""rpn2tex - Convert RPN expressions to LaTeX math mode.

This is an educational example demonstrating the txt2tex architecture:
    tokens.py → lexer.py → ast_nodes.py → parser.py → latex_gen.py → cli.py

Example:
    >>> from rpn2tex.lexer import Lexer
    >>> from rpn2tex.parser import Parser
    >>> from rpn2tex.latex_gen import LaTeXGenerator
    >>> tokens = Lexer("5 3 +").tokenize()
    >>> ast = Parser(tokens).parse()
    >>> latex = LaTeXGenerator().generate(ast)
    >>> print(latex)
    $5 + 3$
"""

from rpn2tex.__version__ import __version__

__all__ = ["__version__"]
