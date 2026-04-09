import argparse
from enum import Enum
from typing import Optional


class TokenType(Enum):
    NAME = 0
    EQ = 1
    LPAREN = 3
    RPAREN = 4
    LBRACE = 5
    RBRACE = 6
    COMMA = 7
    FLOAT = 8
    INT = 9
    MINUS = 10
    NEWLINE = 11
    STAR = 12
    PLUS = 13
    CARET = 14
    SLASH = 15
    COLON = 16
    EOF = 17
    LSQUARE = 18
    RSQUARE = 19
    SEMI = 20


# A subset of openscad's tokens, plus tokens for David McCooey's visual
# polyhedra files
class Token:
    def __init__(
        self, ttype: TokenType, lexeme: Optional[str], pos: int, line: int, column: int
    ) -> None:
        self.ttype = ttype
        self.lexeme = lexeme
        self.pos = pos
        self.line = line
        self.column = column

    def literal(self) -> str:
        match self.ttype:
            case TokenType.NAME | TokenType.FLOAT | TokenType.INT:
                return str(self.lexeme)
            case TokenType.EQ:
                return "="
            case TokenType.LPAREN:
                return "("
            case TokenType.RPAREN:
                return ")"
            case TokenType.LBRACE:
                return "{"
            case TokenType.RBRACE:
                return "}"
            case TokenType.LSQUARE:
                return "["
            case TokenType.RSQUARE:
                return "]"
            case TokenType.COMMA:
                return ","
            case TokenType.MINUS:
                return "-"
            case TokenType.NEWLINE:
                return "\n"
            case TokenType.STAR:
                return "*"
            case TokenType.PLUS:
                return "+"
            case TokenType.CARET:
                return "^"
            case TokenType.SLASH:
                return "/"
            case TokenType.COLON:
                return ":"
            case TokenType.EOF:
                return "\0"
            case TokenType.SEMI:
                return ";"
            case _:
                raise ValueError(f"Bad token type: {self.ttype}")

    def __str__(self) -> str:
        return f"{self.pos} {self.ttype} {self.lexeme}"


class VisualPolyhedron:
    def __init__(
        self,
        name: str,
        vertex_tokenstream: dict[str, list[Token]],
        faces: list[list[str]],
        constant_exacts: dict[str, list[Token]],
        constant_floats: dict[str, float],
        constant_sequence: list[str],
    ) -> None:
        self.vertex_tokenstream = vertex_tokenstream

        self.faces = faces
        self.name = name

        self.constant_exacts = constant_exacts
        self.constant_floats = constant_floats
        self.constant_sequence = constant_sequence

        self.vertices: list[list[float]] = self.evaluate_vertices()

    def evaluate_vertices(self) -> list[list[float]]:
        vertices: list[list[float]] = []
        for vertex, token_list in self.vertex_tokenstream.items():
            evaluated: list[float] = []
            neg = 1
            for token in token_list:
                match token.ttype:
                    case TokenType.LSQUARE | TokenType.RSQUARE:
                        continue
                    case TokenType.COMMA:
                        neg = 1
                    case TokenType.MINUS:
                        neg = -1
                    case TokenType.FLOAT | TokenType.INT:
                        evaluated.append(neg * float(token.literal()))
                    case TokenType.NAME:
                        lexeme = token.lexeme
                        assert lexeme is not None
                        evaluated.append(neg * self.constant_floats[lexeme])
                    case _:
                        raise ValueError(
                            "Bad token encountered while evaluating vertices"
                        )

            vertices.append(evaluated)
        return vertices

    def to_obj(self, filepath: str) -> None:
        vertices = self.vertices
        faces = self.faces

        with open(filepath, "w") as f:
            for v in vertices:
                f.write(f"v {v[0]} {v[1]} {v[2]}\n")

            for face in faces:
                # OBJ faces are 1-indexed
                face_str = " ".join(str(int(v) + 1) for v in face)
                f.write(f"f {face_str}\n")


# Lex Visual Polyhedra files
class VisualPolyhedraLexer:
    def __init__(self) -> None:
        self.tokenstream: list[Token] = []
        self.pos: int = 0

    @staticmethod
    def munch_num(input: str, pos: int, line: int, column: int) -> tuple[Token, int]:
        lexeme = ""
        offset = 0
        while pos + offset < len(input) and input[pos + offset].isnumeric():
            lexeme += input[pos + offset]
            offset += 1

        if pos + offset >= len(input) or input[pos + offset] != ".":
            return (Token(TokenType.INT, lexeme, pos, line, column), offset)
        offset += 1
        lexeme += "."

        while pos + offset < len(input) and input[pos + offset].isnumeric():
            lexeme += input[pos + offset]
            offset += 1

        return (Token(TokenType.FLOAT, lexeme, pos, line, column), offset)

    @staticmethod
    def munch_name(input: str, pos: int, line: int, column: int) -> tuple[Token, int]:
        if pos >= len(input) or not input[pos].isalpha():
            raise Exception(f"Cannot parse name at position {pos}")

        lexeme = input[pos]
        offset = 1

        while pos + offset < len(input) and input[pos + offset].isalnum():
            lexeme += input[pos + offset]
            offset += 1

        return (Token(TokenType.NAME, lexeme, pos, line, column), offset)

    def lex(self, input: str):
        i = 0
        line = 1
        column = 1
        while i < len(input):
            match input[i]:
                case "(":
                    self.tokenstream.append(
                        Token(TokenType.LPAREN, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case ")":
                    self.tokenstream.append(
                        Token(TokenType.RPAREN, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case "{":
                    self.tokenstream.append(
                        Token(TokenType.LBRACE, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case "}":
                    self.tokenstream.append(
                        Token(TokenType.RBRACE, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case "[":
                    self.tokenstream.append(
                        Token(TokenType.LSQUARE, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case "]":
                    self.tokenstream.append(
                        Token(TokenType.RSQUARE, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case "=":
                    self.tokenstream.append(Token(TokenType.EQ, None, i, line, column))
                    i += 1
                    column += 1
                case "-":
                    self.tokenstream.append(
                        Token(TokenType.MINUS, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case ",":
                    self.tokenstream.append(
                        Token(TokenType.COMMA, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case "*":
                    self.tokenstream.append(
                        Token(TokenType.STAR, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case "+":
                    self.tokenstream.append(
                        Token(TokenType.PLUS, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case "/":
                    self.tokenstream.append(
                        Token(TokenType.SLASH, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case "^":
                    self.tokenstream.append(
                        Token(TokenType.CARET, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case ":":
                    self.tokenstream.append(
                        Token(TokenType.COLON, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case ";":
                    self.tokenstream.append(
                        Token(TokenType.SEMI, None, i, line, column)
                    )
                    i += 1
                    column += 1
                case "\n":
                    self.tokenstream.append(
                        Token(TokenType.NEWLINE, None, i, line, column)
                    )
                    i += 1
                    line += 1
                    column = 1
                case " " | "\t":
                    i += 1
                    column += 1
                case "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9":
                    (tok, offset) = self.munch_num(input, i, line, column)
                    self.tokenstream.append(tok)
                    i += offset
                    column += offset
                case _:
                    (tok, offset) = self.munch_name(input, i, line, column)
                    self.tokenstream.append(tok)
                    i += offset
                    column += offset
        self.tokenstream.append(Token(TokenType.EOF, None, i, line, column))

    def get(self) -> Token:
        token = self.tokenstream[self.pos]
        self.pos += 1
        return token

    def peek(self, i: int) -> Token:
        assert i >= 0
        assert self.pos + i <= len(self.tokenstream)
        token = self.tokenstream[self.pos + i - 1]
        return token


# Constant definitions in visual polyhedra files can be followed by a 'where'
# block. This flag tells the parser that we are currently reading 'where'
# constants.
class ConstantRegion(Enum):
    DEF = 0
    WHERE = 1


# Parse visual polyhedra files to Polyhedron objects
class VisualPolyhedraParser:
    def __init__(self, input: str) -> None:
        self.lexer = VisualPolyhedraLexer()
        self.lexer.lex(input)

        self.vertices: dict[str, list[Token]] = {}
        self.faces: list[list[str]] = []
        self.name: str = ""

        self.constant_exacts: dict[str, list[Token]] = {}
        self.constant_floats: dict[str, float] = {}
        self.constant_def_sequence: list[str] = []
        self.constant_where_sequence: list[str] = []
        self.constant_sequence: list[str] = []

    def syntax_error(self):
        token = self.lexer.peek(0)
        raise Exception(f"Snytax Eorrr at position {token.pos}")

    @staticmethod
    def is_expression_ttype(ttype: TokenType) -> bool:
        match ttype:
            case (
                TokenType.INT
                | TokenType.NAME
                | TokenType.STAR
                | TokenType.PLUS
                | TokenType.MINUS
                | TokenType.LPAREN
                | TokenType.RPAREN
                | TokenType.SLASH
                | TokenType.CARET
            ):
                return True
            case _:
                return False

    def expect(self, ttype: TokenType) -> Token:
        token = self.lexer.get()
        if token.ttype != ttype:
            raise Exception(
                f"Expected {ttype} at line {token.line} and column {token.column}, found {token.ttype}"
            )

        return token

    def expect_expression(self) -> Token:
        token = self.lexer.get()
        if not self.is_expression_ttype(token.ttype):
            raise Exception(
                f"Expected expression token at position {token.pos}, found {token.ttype}"
            )

        return token

    def linebreak(self):
        self.expect(TokenType.NEWLINE)
        while self.lexer.peek(1).ttype == TokenType.NEWLINE:
            self.expect(TokenType.NEWLINE)

    # name_def := names* \n
    def name_def(self):
        names = []
        while self.lexer.peek(1).ttype in {
            TokenType.NAME,
            TokenType.LPAREN,
            TokenType.RPAREN,
        }:
            match self.lexer.peek(1).ttype:
                case TokenType.NAME:
                    names.append(self.expect(TokenType.NAME).lexeme)
                case TokenType.LPAREN:
                    self.expect(TokenType.LPAREN)
                case TokenType.RPAREN:
                    self.expect(TokenType.RPAREN)
        self.linebreak()
        self.name = "_".join(names).lower()

    # constant_def := name = float \n
    # constant_def := name = float = [int|name|*|(|)|+|/|*|^] \n
    # constant_def := name = [int|name|*|(|)|+|/|^] \n
    def constant_def(self, region: ConstantRegion):
        token = self.expect(TokenType.NAME)
        const = token.lexeme
        assert const is not None
        floatv: float = 0.0
        exactv: list[Token] = []

        self.expect(TokenType.EQ)
        ttype = self.lexer.peek(1).ttype
        if ttype == TokenType.FLOAT:
            floatv = float(self.expect(TokenType.FLOAT).literal())
            ttype = self.lexer.peek(1).ttype

            if ttype == TokenType.NEWLINE:
                pass
            elif ttype == TokenType.EQ:
                self.expect(TokenType.EQ)
                while self.is_expression_ttype(self.lexer.peek(1).ttype):
                    exactv.append(self.expect_expression())
            else:
                self.syntax_error()

        elif self.is_expression_ttype(ttype):
            while self.is_expression_ttype(self.lexer.peek(1).ttype):
                exactv.append(self.expect_expression())

        self.linebreak()

        if region == ConstantRegion.DEF and const not in self.constant_def_sequence:
            self.constant_def_sequence.append(const)
        elif (
            region == ConstantRegion.WHERE and const not in self.constant_where_sequence
        ):
            self.constant_where_sequence.append(const)
        if const not in self.constant_exacts:
            self.constant_exacts[const] = exactv
        if const not in self.constant_floats:
            self.constant_floats[const] = float(floatv)

    # where_block := WHERE: constant_block
    def where_block(self):
        t1 = self.lexer.peek(1)
        t2 = self.lexer.peek(2)
        if (
            t1.ttype == TokenType.NAME
            and t1.lexeme == "WHERE"
            and t2.ttype == TokenType.COLON
        ):
            self.expect(TokenType.NAME)
            self.expect(TokenType.COLON)
            self.constant_block(ConstantRegion.WHERE)

    # value := -? [name|int|float]
    def value(self) -> list[Token]:
        token_list = []
        if self.lexer.peek(1).ttype == TokenType.MINUS:
            token_list.append(self.expect(TokenType.MINUS))

        ttype = self.lexer.peek(1).ttype
        match ttype:
            case TokenType.NAME:
                token_list.append(self.expect(TokenType.NAME))
            case TokenType.INT:
                token_list.append(self.expect(TokenType.INT))
            case TokenType.FLOAT:
                token_list.append(self.expect(TokenType.FLOAT))
            case _:
                self.syntax_error()
        return token_list

    # vertex_def := name = (value, value, value) \n
    def vertex_def(self):
        token_list = []
        name_token = self.expect(TokenType.NAME)
        name = name_token.lexeme
        assert name is not None
        self.expect(TokenType.EQ)
        self.expect(TokenType.LPAREN)
        token_list.append(Token(TokenType.LSQUARE, None, -1, -1, -1))
        token_list += self.value()
        token_list.append(self.expect(TokenType.COMMA))
        token_list += self.value()
        token_list.append(self.expect(TokenType.COMMA))
        token_list += self.value()
        self.expect(TokenType.RPAREN)
        token_list.append(Token(TokenType.RSQUARE, None, -1, -1, -1))
        self.linebreak()

        self.vertices[name] = token_list

    # face_def := { [int,]* int } \n
    def face_def(self):
        face = []
        self.expect(TokenType.LBRACE)
        while (
            self.lexer.peek(1).ttype == TokenType.INT
            and self.lexer.peek(2).ttype == TokenType.COMMA
        ):
            face.append(self.expect(TokenType.INT).lexeme)
            self.expect(TokenType.COMMA)
        face.append(self.expect(TokenType.INT).lexeme)
        self.expect(TokenType.RBRACE)
        self.linebreak()

        self.faces.append(face)

    # constant_block := constant_def*
    def constant_block(self, region: ConstantRegion):
        t1 = self.lexer.peek(1).ttype
        t2 = self.lexer.peek(2).ttype
        t3 = self.lexer.peek(3).ttype
        t4 = self.lexer.peek(4).ttype
        t5 = self.lexer.peek(5).ttype
        t6 = self.lexer.peek(6).ttype
        while (
            t1 == TokenType.NAME
            and t2 == TokenType.EQ
            and (t3 == TokenType.FLOAT or self.is_expression_ttype(t3))
            and (
                t4 == TokenType.EQ
                or t4 == TokenType.NEWLINE
                or self.is_expression_ttype(t4)
            )
            and (
                t5 == TokenType.NAME
                or t5 == TokenType.NEWLINE
                or self.is_expression_ttype(t5)
            )
            and (
                t6 == TokenType.NAME
                or t6 == TokenType.NEWLINE
                or t6 == TokenType.EQ
                or self.is_expression_ttype(t6)
            )
        ):
            self.constant_def(region)
            t1 = self.lexer.peek(1).ttype
            t2 = self.lexer.peek(2).ttype
            t3 = self.lexer.peek(3).ttype
            t4 = self.lexer.peek(4).ttype
            t5 = self.lexer.peek(5).ttype
            t6 = self.lexer.peek(6).ttype

    # vertex_block := vertex_def*
    def vertex_block(self):
        while (
            self.lexer.peek(1).ttype == TokenType.NAME
            and self.lexer.peek(2).ttype == TokenType.EQ
        ):
            self.vertex_def()

    # face_block := Faces : \n face_def*
    def face_block(self):
        if not self.expect(TokenType.NAME).lexeme == "Faces":
            self.syntax_error()
        self.expect(TokenType.COLON)
        self.linebreak()
        while self.lexer.peek(1).ttype == TokenType.LBRACE:
            self.face_def()

    # polyhedron := name_def constant_block vertex_block face_block EOF
    def parse(self) -> VisualPolyhedron:
        self.name_def()
        self.constant_block(ConstantRegion.DEF)
        self.where_block()
        self.vertex_block()
        self.face_block()
        self.expect(TokenType.EOF)

        self.constant_sequence = (
            self.constant_where_sequence + self.constant_def_sequence
        )

        name = self.name

        return VisualPolyhedron(
            name,
            self.vertices,
            self.faces,
            self.constant_exacts,
            self.constant_floats,
            self.constant_sequence,
        )

    def dump_tokenstream(self):
        while self.lexer.peek(1).ttype != TokenType.EOF:
            tok = self.lexer.get()
            print(tok.ttype, tok.lexeme)


def parse_visual_polyhedra_file(filepath: str) -> VisualPolyhedron:
    """Parse a visual polyhedra file and return a VisualPolyhedron."""
    with open(filepath, "r") as f:
        content = f.read()

    parser = VisualPolyhedraParser(content)
    polyhedron = parser.parse()
    return polyhedron


def main():
    parser = argparse.ArgumentParser(
        description="Convert visual polyhedron text files to .obj"
    )
    parser.add_argument("input_file", help="Visual polyhedron text file")
    parser.add_argument(
        "-o",
        "--output",
        dest="output_file",
        help="Output OBJ file path. If not specified, will use input filename with .obj extension.",
    )

    args = parser.parse_args()

    polyhedron = parse_visual_polyhedra_file(args.input_file)

    if args.output_file:
        output_path = args.output_file
    else:
        if args.input_file.endswith(".txt"):
            output_path = args.input_file.rsplit(".", 1)[0] + ".obj"
        else:
            output_path = args.input_file + ".obj"

    polyhedron.to_obj(output_path)


if __name__ == "__main__":
    main()
