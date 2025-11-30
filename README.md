# rpn2tex

An educational example demonstrating the architecture of [txt2tex](../README.md).

This minimal implementation converts **Reverse Polish Notation (RPN)** expressions to **LaTeX math mode**, showcasing the same pipeline architecture used in the full txt2tex system.

## Purpose

This project helps you understand the txt2tex codebase by providing:

1. A simplified implementation of the same concepts
2. A hands-on exercise to extend the functionality
3. Clear documentation explaining each component

## Architecture Overview

rpn2tex follows the same pipeline as txt2tex:

```
Input Text → Lexer → Tokens → Parser → AST → Generator → LaTeX
```

### File Correspondence

| rpn2tex File | txt2tex File | Purpose |
|--------------|--------------|---------|
| `tokens.py` | `tokens.py` | Token types and Token dataclass |
| `lexer.py` | `lexer.py` | Tokenizes input text |
| `ast_nodes.py` | `ast_nodes.py` | AST node definitions |
| `parser.py` | `parser.py` | Builds AST from tokens |
| `latex_gen.py` | `latex_gen.py` | Converts AST to LaTeX |
| `errors.py` | `errors.py` | Error formatting |
| `cli.py` | `cli.py` | Command-line interface |

### Key Differences

| Aspect | rpn2tex | txt2tex |
|--------|---------|---------|
| Parser type | Stack-based (RPN) | Recursive descent (infix) |
| Token types | ~6 | ~100+ |
| AST nodes | 2 | 30+ |
| Features | Basic arithmetic | Full Z notation |

## Installation

```bash
# From the rpn2tex directory
pip install -e .

# Or use hatch for development
cd rpn2tex
hatch shell
```

## Quick Start

### Command Line

```bash
# Convert RPN file to LaTeX
rpn2tex examples/basic.rpn

# Output: $5 + 3$

rpn2tex examples/complex.rpn

# Output: $( 2 + 3 ) \times 4$

# Save to file
rpn2tex examples/basic.rpn -o output.tex

# Read from stdin
echo "10 2 / 5 +" | rpn2tex -
```

### Python API

```python
from rpn2tex.lexer import Lexer
from rpn2tex.parser import Parser
from rpn2tex.latex_gen import LaTeXGenerator

# Pipeline: text → tokens → AST → LaTeX
text = "5 3 + 2 *"
tokens = Lexer(text).tokenize()
ast = Parser(tokens).parse()
latex = LaTeXGenerator().generate(ast)

print(latex)  # $( 5 + 3 ) \times 2$
```

## RPN Syntax Reference

[Reverse Polish Notation](https://en.wikipedia.org/wiki/Reverse_Polish_notation) places operators after their operands:

| Infix (Standard) | RPN | LaTeX Output |
|------------------|-----|--------------|
| `5 + 3` | `5 3 +` | `$5 + 3$` |
| `5 - 3` | `5 3 -` | `$5 - 3$` |
| `5 * 3` | `5 3 *` | `$5 \times 3$` |
| `6 / 2` | `6 2 /` | `$6 \div 2$` |
| `(2 + 3) * 4` | `2 3 + 4 *` | `$( 2 + 3 ) \times 4$` |
| `2 + 3 * 4` | `3 4 * 2 +` | `$2 + 3 \times 4$` |

### How RPN Works

RPN uses a stack to evaluate expressions:

```
Input: 2 3 + 4 *

Step 1: Push 2      Stack: [2]
Step 2: Push 3      Stack: [2, 3]
Step 3: + pops 2,3  Stack: [(2+3)]
Step 4: Push 4      Stack: [(2+3), 4]
Step 5: * pops all  Stack: [((2+3)*4)]

Result: (2 + 3) * 4
```

## Component Walkthrough

### 1. Tokens (`tokens.py`)

**Purpose**: Define the vocabulary of the language.

The **lexer produces tokens**, which are the atomic units of the language.

```python
class TokenType(Enum):
    NUMBER = auto()   # Numeric literals
    PLUS = auto()     # +
    MINUS = auto()    # -
    MULT = auto()     # *
    DIV = auto()      # /
    EOF = auto()      # End marker

@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    line: int
    column: int
```

**What does `auto()` do?**

`auto()` is a helper from Python's `enum` module that automatically generates unique values:

```python
NUMBER = auto()  # Gets value 1
PLUS = auto()    # Gets value 2
MINUS = auto()   # Gets value 3
# ... etc
```

The actual numeric values don't matter—you never compare `TokenType.PLUS == 2`. You only compare `token.type == TokenType.PLUS`. Using `auto()` prevents duplicate values and makes it easy to add/remove/reorder token types.

### 2. Lexer (`lexer.py`)

**Purpose**: Convert raw text into a stream of tokens.

**Input**: String of characters
**Output**: List of `Token` objects

```python
"5 3 +"
    ↓ Lexer
[Token(NUMBER, "5"), Token(NUMBER, "3"), Token(PLUS, "+"), Token(EOF, "")]
```

The lexer:
- Scans character by character
- Groups characters into meaningful units (tokens)
- Tracks position (line, column) for error reporting
- Ignores whitespace

```python
class Lexer:
    def tokenize(self) -> list[Token]:
        """Convert input text to token stream."""
        tokens: list[Token] = []
        while not self._at_end():
            self._skip_whitespace()
            if self._at_end():
                break
            tokens.append(self._scan_token())
        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens
```

**Key point**: The lexer doesn't validate syntax. It just produces tokens. `"5 +"` tokenizes successfully—the parser catches the missing operand.

### 3. AST Nodes (`ast_nodes.py`)

**Purpose**: Define the tree structure that represents parsed expressions.

The **parser produces AST nodes**. AST = Abstract Syntax Tree.

```python
@dataclass(frozen=True)
class Number(ASTNode):
    value: str

@dataclass(frozen=True)
class BinaryOp(ASTNode):
    operator: str
    left: Expr      # Child node
    right: Expr     # Child node
```

For input `2 3 + 4 *` (meaning `(2 + 3) * 4`), the AST is:

```
        BinaryOp(*)        ← root
        /        \
   BinaryOp(+)    Number(4)
   /        \
Number(2)  Number(3)
```

### 4. Parser (`parser.py`)

**Purpose**: Build an AST from tokens.

**Input**: List of `Token` objects
**Output**: AST root node (`Expr`)

```python
[Token(NUMBER, "5"), Token(NUMBER, "3"), Token(PLUS, "+")]
    ↓ Parser
BinaryOp(operator="+", left=Number("5"), right=Number("3"))
```

The parser:
- Consumes tokens according to grammar rules
- Builds tree structure representing the expression
- Validates syntax (e.g., `"5 +"` is invalid—missing operand)

```python
class Parser:
    def parse(self) -> Expr:
        """Convert tokens to AST using stack-based RPN parsing."""
        stack: list[Expr] = []
        for token in tokens:
            if token.type == TokenType.NUMBER:
                stack.append(Number(token.value))
            elif token.type in (PLUS, MINUS, MULT, DIV):
                right = stack.pop()
                left = stack.pop()
                stack.append(BinaryOp(op, left, right))
        return stack[0]
```

**Why separate lexer and parser?**

Separation of concerns:
- Lexer handles *lexical* structure (what are the words?)
- Parser handles *syntactic* structure (how do words combine?)

### 5. LaTeX Generator (`latex_gen.py`)

**Purpose**: Convert AST to LaTeX output.

**Input**: AST root node
**Output**: LaTeX string

Uses the **visitor pattern** with Python's `@singledispatchmethod`:

```python
class LaTeXGenerator:
    @singledispatchmethod
    def _visit(self, node: Expr) -> str:
        """Base case—raises error for unknown node types."""
        raise NotImplementedError(f"No visitor for {type(node).__name__}")

    @_visit.register
    def _visit_number(self, node: Number) -> str:
        """Called when node is a Number."""
        return node.value

    @_visit.register
    def _visit_binary_op(self, node: BinaryOp) -> str:
        """Called when node is a BinaryOp."""
        left = self._visit(node.left)    # Recursively visit children
        right = self._visit(node.right)
        return f"{left} {op_latex} {right}"
```

**How the visitor pattern works**:

1. `@singledispatchmethod` marks `_visit` as the dispatcher
2. `@_visit.register` registers handlers for specific types
3. Python dispatches based on the argument's type at runtime:
   - `_visit(Number(...))` → calls `_visit_number`
   - `_visit(BinaryOp(...))` → calls `_visit_binary_op`

**Why use the visitor pattern?**

Without it (bad—violates Open/Closed Principle):
```python
def generate(self, node):
    if isinstance(node, Number):
        return node.value
    elif isinstance(node, BinaryOp):
        ...
    elif isinstance(node, Exponent):  # Must modify for each new type!
        ...
```

With visitor pattern (good—extensible):
```python
@_visit.register
def _visit_exponent(self, node: Exponent) -> str:  # Just add new method!
    return f"{self._visit(node.base)}^{{{self._visit(node.exponent)}}}"
```

**Depth-first traversal**:

The visitor traverses the AST **depth-first** (children before parent):

```
_visit(BinaryOp(*))                      ← Start at root
  ├─ _visit(BinaryOp(+))                 ← Go left first (depth-first)
  │    ├─ _visit(Number(2)) → "2"
  │    ├─ _visit(Number(3)) → "3"
  │    └─ returns "2 + 3"
  ├─ _visit(Number(4)) → "4"             ← Then right
  └─ returns "( 2 + 3 ) \times 4"        ← Process parent last
```

This is **post-order** traversal: children are processed before parents. This is natural for code generation because you need the child strings before you can combine them.

### 6. Error Formatter (`errors.py`)

**Purpose**: Provide context-aware error messages with source location.

```
Error: Unexpected character '@'

1 | 5 3 @
        ^
```

Shows:
- Line number
- Source context
- Caret (^) pointing to exact error column

### 7. CLI (`cli.py`)

**Purpose**: Orchestrate the pipeline and handle I/O.

```python
def main():
    text = read_input()
    tokens = Lexer(text).tokenize()      # Text → Tokens
    ast = Parser(tokens).parse()          # Tokens → AST
    latex = LaTeXGenerator().generate(ast)  # AST → LaTeX
    write_output(latex)
```

## Code Style

This project follows txt2tex's type annotation conventions:

- **Function signatures**: Always fully annotated (parameters + return type)
- **Collection variables**: Explicit annotations (`tokens: list[Token] = []`)
- **Simple locals**: Use inference when type is clear from return type (`tokens = lexer.tokenize()`)

The type checkers (mypy, pyright) infer types from return annotations, so explicit local annotations are only needed when they add clarity.

## Development

### Running Tests

```bash
hatch run test
```

### Running Quality Checks

```bash
hatch run check       # lint + type + test
hatch run lint        # ruff check
hatch run format      # ruff format
hatch run type        # mypy strict mode
```

---

## Programming Exercises

The following features are intentionally **not implemented**. Use these exercises to practice extending the rpn2tex codebase, which will prepare you for contributing to txt2tex.

### Exercise 1: Add Exponentiation (`^`)

**Goal**: Support `2 3 ^` → `$2^{3}$`

**Difficulty**: Easy

**Steps**:

1. **tokens.py**: Add `CARET = auto()` to `TokenType`

2. **lexer.py**: Add case for `^` in `_scan_token()`:
   ```python
   if char == "^":
       self._advance()
       return Token(TokenType.CARET, "^", start_line, start_column)
   ```

3. **ast_nodes.py**: Add new node type:
   ```python
   @dataclass(frozen=True)
   class Exponent(ASTNode):
       base: Expr
       exponent: Expr
   ```
   Update the `Expr` type alias to include `Exponent`.

4. **parser.py**: Handle `CARET` token (similar to other binary operators)

5. **latex_gen.py**: Add visitor for `Exponent`:
   ```python
   @_visit.register
   def _visit_exponent(self, node: Exponent) -> str:
       base = self._visit(node.base)
       exp = self._visit(node.exponent)
       # Use braces for complex exponents
       return f"{base}^{{{exp}}}"
   ```

6. **tests/test_rpn2tex.py**: Add tests

**Test Cases**:
- `2 3 ^` → `$2^{3}$`
- `2 3 4 + ^` → `$2^{( 3 + 4 )}$` (complex exponent needs parens)

---

### Exercise 2: Add Square Root (`sqrt`)

**Goal**: Support `9 sqrt` → `$\sqrt{9}$`

**Difficulty**: Medium (introduces unary operators)

**Steps**:

1. **tokens.py**: Add `SQRT = auto()` to `TokenType`

2. **lexer.py**: Recognize the keyword `sqrt`:
   ```python
   # After scanning an identifier, check if it's "sqrt"
   if identifier == "sqrt":
       return Token(TokenType.SQRT, "sqrt", ...)
   ```
   
   **Hint**: You'll need to add identifier scanning similar to number scanning.

3. **ast_nodes.py**: Add new node:
   ```python
   @dataclass(frozen=True)
   class SquareRoot(ASTNode):
       operand: Expr
   ```

4. **parser.py**: Handle `SQRT` as a unary operator:
   ```python
   elif token.type == TokenType.SQRT:
       if len(stack) < 1:
           raise ParserError("sqrt requires one operand", token)
       operand = stack.pop()
       node = SquareRoot(..., operand=operand)
       stack.append(node)
   ```

5. **latex_gen.py**: Add visitor:
   ```python
   @_visit.register
   def _visit_sqrt(self, node: SquareRoot) -> str:
       operand = self._visit(node.operand)
       return f"\\sqrt{{{operand}}}"
   ```

**Test Cases**:
- `9 sqrt` → `$\sqrt{9}$`
- `2 3 + sqrt` → `$\sqrt{( 2 + 3 )}$`

---

### Exercise 3: Add Nth Root (`root`)

**Goal**: Support `8 3 root` → `$\sqrt[3]{8}$`

**Difficulty**: Hard (two operands, special LaTeX syntax)

**Steps**:

1. **tokens.py**: Add `ROOT = auto()`

2. **lexer.py**: Recognize `root` keyword

3. **ast_nodes.py**: Add node:
   ```python
   @dataclass(frozen=True)
   class NthRoot(ASTNode):
       radicand: Expr  # The value under the radical
       index: Expr     # The root index (e.g., 3 for cube root)
   ```

4. **parser.py**: Handle as binary operator:
   ```python
   # 8 3 root means: 3rd root of 8
   # So: radicand=8 (deeper in stack), index=3 (top of stack)
   index = stack.pop()
   radicand = stack.pop()
   node = NthRoot(..., radicand=radicand, index=index)
   ```

5. **latex_gen.py**: Generate proper LaTeX:
   ```python
   @_visit.register
   def _visit_nth_root(self, node: NthRoot) -> str:
       radicand = self._visit(node.radicand)
       index = self._visit(node.index)
       return f"\\sqrt[{index}]{{{radicand}}}"
   ```

**Test Cases**:
- `8 3 root` → `$\sqrt[3]{8}$`
- `16 4 root` → `$\sqrt[4]{16}$`
- `2 3 + 2 root` → `$\sqrt[2]{( 2 + 3 )}$`

---

## Next Steps

After completing these exercises, you're ready to explore txt2tex:

1. **Compare implementations**: See how txt2tex handles the same concepts at scale
2. **Study the parser**: txt2tex uses recursive descent instead of stack-based parsing
3. **Explore AST nodes**: txt2tex has 30+ node types for Z notation
4. **Read DESIGN.md**: Understand the architectural decisions

## License

MIT - Same as txt2tex

