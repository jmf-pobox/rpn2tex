"""Error formatting for rpn2tex - provides context-aware error messages.

This module formats parse and lexer errors with source context,
similar to error output from compilers like gcc and rustc.
Compare with txt2tex/errors.py for the full implementation.

Key concepts demonstrated:
    - Source context extraction
    - Caret positioning for error location
    - User-friendly error messages
"""

from __future__ import annotations


class ErrorFormatter:
    """Formats parse errors with source context and helpful hints.

    Provides gcc/rustc-style error output with:
    - Line numbers and source context
    - Caret (^) pointing to error column
    - Clear error messages

    Attributes:
        source: The complete source text being parsed
        lines: Source text split into lines

    Example:
        >>> formatter = ErrorFormatter("5 3 @")
        >>> print(formatter.format_error("Unexpected character '@'", 1, 5))
        Error: Unexpected character '@'
        <BLANKLINE>
        1 | 5 3 @
            ^
    """

    source: str
    lines: list[str]

    def __init__(self, source: str) -> None:
        """Initialize formatter with source text.

        Args:
            source: The complete source text being parsed
        """
        self.source = source
        self.lines = source.splitlines()

    def format_error(
        self,
        message: str,
        line: int,
        column: int,
        *,
        context_lines: int = 1,
    ) -> str:
        """Format an error with source context.

        Args:
            message: The error message
            line: Line number (1-based)
            column: Column number (1-based)
            context_lines: Number of lines to show before/after error

        Returns:
            Formatted error string with context

        Example:
            >>> formatter = ErrorFormatter("5 3 + @ 2")
            >>> err = formatter.format_error("Unexpected '@'", 1, 7)
            >>> "^" in err
            True
        """
        parts: list[str] = []

        # Error header
        parts.append(f"Error: {message}")
        parts.append("")

        # Source context
        context = self._get_context(line, column, context_lines)
        parts.append(context)

        return "\n".join(parts)

    def _get_context(self, line: int, column: int, context_lines: int) -> str:
        """Extract source context around error position.

        Args:
            line: Error line number (1-based)
            column: Error column number (1-based)
            context_lines: Lines to show before/after

        Returns:
            Formatted context with line numbers and caret
        """
        # Convert to 0-based index
        error_idx = line - 1

        # Calculate range (clamped to valid indices)
        start_idx = max(0, error_idx - context_lines)
        end_idx = min(len(self.lines), error_idx + context_lines + 1)

        # Calculate line number width for alignment
        max_line_num = end_idx
        num_width = len(str(max_line_num))

        result_lines: list[str] = []

        for idx in range(start_idx, end_idx):
            line_num = idx + 1  # Convert back to 1-based
            line_content = self.lines[idx] if idx < len(self.lines) else ""

            # Format line with number
            prefix = f"{line_num:>{num_width}} | "
            result_lines.append(f"{prefix}{line_content}")

            # Add caret on error line
            if idx == error_idx:
                # Spaces for line number column, then position caret
                caret_prefix = " " * num_width + " | "
                # Position caret at column (1-based, so column-1 spaces)
                caret_pos = max(0, column - 1)
                caret_line = caret_prefix + " " * caret_pos + "^"
                result_lines.append(caret_line)

        return "\n".join(result_lines)
