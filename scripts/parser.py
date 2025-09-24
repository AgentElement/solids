from enum import Enum


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


class Token:
    def __init__(self, ttype: TokenType, lexeme: str | None, pos: int) -> None:
        self.ttype = ttype
        self.lexeme = lexeme
        self.pos = pos

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

    def __str__(self) -> str:
        return f"{self.pos} {self.ttype} {self.lexeme}"


class Lexer:
    def __init__(self) -> None:
        self.tokenstream = []
        self.pos = 0

    @staticmethod
    def munch_num(input: str, pos: int) -> tuple[Token, int]:
        lexeme = ""
        offset = 0
        while input[pos + offset].isnumeric():
            lexeme += input[pos + offset]
            offset += 1

        if input[pos + offset] != ".":
            return (Token(TokenType.INT, lexeme, pos), offset)
        offset += 1
        lexeme += "."

        while input[pos + offset].isnumeric():
            lexeme += input[pos + offset]
            offset += 1

        return (Token(TokenType.FLOAT, lexeme, pos), offset)

    @staticmethod
    def munch_name(input: str, pos: int) -> tuple[Token, int]:
        if not input[pos].isalpha():
            raise Exception(f"Cannot parse name at position {pos}")

        lexeme = input[pos]
        offset = 1

        while input[pos + offset].isalnum():
            lexeme += input[pos + offset]
            offset += 1

        return (Token(TokenType.NAME, lexeme, pos), offset)

    def lex(self, input: str):
        i = 0
        while i < len(input):
            match input[i]:
                case "(":
                    self.tokenstream.append(Token(TokenType.LPAREN, None, i))
                    i += 1
                case ")":
                    self.tokenstream.append(Token(TokenType.RPAREN, None, i))
                    i += 1
                case "{":
                    self.tokenstream.append(Token(TokenType.LBRACE, None, i))
                    i += 1
                case "}":
                    self.tokenstream.append(Token(TokenType.RBRACE, None, i))
                    i += 1
                case "=":
                    self.tokenstream.append(Token(TokenType.EQ, None, i))
                    i += 1
                case "-":
                    self.tokenstream.append(Token(TokenType.MINUS, None, i))
                    i += 1
                case ",":
                    self.tokenstream.append(Token(TokenType.COMMA, None, i))
                    i += 1
                case "*":
                    self.tokenstream.append(Token(TokenType.STAR, None, i))
                    i += 1
                case "+":
                    self.tokenstream.append(Token(TokenType.PLUS, None, i))
                    i += 1
                case "/":
                    self.tokenstream.append(Token(TokenType.SLASH, None, i))
                    i += 1
                case "^":
                    self.tokenstream.append(Token(TokenType.CARET, None, i))
                    i += 1
                case ":":
                    self.tokenstream.append(Token(TokenType.COLON, None, i))
                    i += 1
                case "\n":
                    self.tokenstream.append(Token(TokenType.NEWLINE, None, i))
                    i += 1
                case " " | "\t":
                    i += 1
                case "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9":
                    (tok, offset) = self.munch_num(input, i)
                    self.tokenstream.append(tok)
                    i += offset
                case _:
                    (tok, offset) = self.munch_name(input, i)
                    self.tokenstream.append(tok)
                    i += offset
        self.tokenstream.append(Token(TokenType.EOF, None, i))

    def get(self) -> Token:
        token = self.tokenstream[self.pos]
        self.pos += 1
        return token

    def peek(self, i: int) -> Token:
        assert i >= 0
        assert self.pos + i <= len(self.tokenstream)
        token = self.tokenstream[self.pos + i - 1]
        return token


class Polyhedron:
    def __init__(
        self, name, vertices, faces, constant_exacts, constant_floats, constant_sequence
    ) -> None:
        self.vertices = vertices
        self.faces = faces
        self.name = name

        self.constant_exacts = constant_exacts
        self.constant_floats = constant_floats
        self.constant_sequence = constant_sequence

        self.edges = self.make_edgelist()

    def make_edgelist(self) -> set[tuple[int, int]]:
        edges = set()
        for face in self.faces:
            for i, v1 in enumerate(face):
                for v2 in face[i:]:
                    edges.add((v1, v2) if v1 < v2 else (v2, v1))
        return edges

    def openscad_vertices(self) -> list[Token]:
        tokenstream = [
            Token(TokenType.NAME, "vertices", -1),
            Token(TokenType.EQ, None, -1),
            Token(TokenType.LSQUARE, None, -1),
            Token(TokenType.NEWLINE, None, -1),
        ]
        for vertex, token_list in self.vertices.items():
            tokenstream += token_list
            tokenstream.append(Token(TokenType.COMMA, None, -1))
            tokenstream.append(Token(TokenType.NEWLINE, None, -1))
        tokenstream.append(Token(TokenType.RSQUARE, None, -1))
        tokenstream.append(Token(TokenType.SEMI, None, -1))
        tokenstream.append(Token(TokenType.NEWLINE, None, -1))
        return tokenstream

    def openscad_constants(self) -> list[Token]:
        tokenstream = []
        seen_constants = set()
        for constant in self.constant_sequence:
            if constant in seen_constants:
                continue
            tokenstream.append(Token(TokenType.NAME, constant, -1))
            tokenstream.append(Token(TokenType.EQ, None, -1))
            if constant in self.constant_exacts:
                tokenstream += self.constant_exacts[constant]
            else:
                tokenstream += self.constant_floats[constant]
            tokenstream.append(Token(TokenType.SEMI, None, -1))
            tokenstream.append(Token(TokenType.NEWLINE, None, -1))
        return tokenstream

    def openscad_edges(self) -> list[Token]:
        tokenstream = [
            Token(TokenType.NAME, "edges", -1),
            Token(TokenType.EQ, None, -1),
            Token(TokenType.LSQUARE, None, -1),
            Token(TokenType.NEWLINE, None, -1),
        ]
        for start, end in self.edges:
            tokenstream.append(Token(TokenType.LSQUARE, None, -1))
            tokenstream.append(Token(TokenType.NAME, str(start), -1))
            tokenstream.append(Token(TokenType.COMMA, None, -1))
            tokenstream.append(Token(TokenType.NAME, str(end), -1))
            tokenstream.append(Token(TokenType.RSQUARE, None, -1))
            tokenstream.append(Token(TokenType.COMMA, None, -1))
            tokenstream.append(Token(TokenType.NEWLINE, None, -1))
        tokenstream.append(Token(TokenType.RSQUARE, None, -1))
        tokenstream.append(Token(TokenType.SEMI, None, -1))
        tokenstream.append(Token(TokenType.NEWLINE, None, -1))
        return tokenstream

    def openscad(self) -> str:
        tokenstream = self.openscad_constants()
        tokenstream += self.openscad_vertices()
        tokenstream += self.openscad_edges()
        return "".join([x.literal() for x in tokenstream])


class Parser:
    def __init__(self, input) -> None:
        self.lexer = Lexer()
        self.lexer.lex(input)

        self.vertices = {}
        self.faces = []
        self.name = None

        self.constant_exacts = {}
        self.constant_floats = {}
        self.constant_sequence = []

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
            ):
                return True
            case _:
                return False

    def expect(self, ttype: TokenType) -> Token:
        token = self.lexer.get()
        if token.ttype != ttype:
            raise Exception(
                f"Expected {ttype} at position {token.pos}, found {token.ttype}"
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
        while self.lexer.peek(1).ttype == TokenType.NAME:
            names.append(self.expect(TokenType.NAME).lexeme)
        self.linebreak()
        self.name = " ".join(names)

    # constant_def := name = float \n
    # constant_def := name = float = [int|name|*|(|)|+|/|*|] \n
    # constant_def := name = [int|name|*|(|)|+|/|] \n
    def constant_def(self):
        const = self.expect(TokenType.NAME).lexeme
        floatv = ""
        exactv = []

        self.expect(TokenType.EQ)
        ttype = self.lexer.peek(1).ttype
        if ttype == TokenType.FLOAT:
            floatv = self.expect(TokenType.FLOAT).ttype
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

        self.constant_sequence.append(const)
        self.constant_exacts[const] = exactv
        self.constant_floats[const] = floatv

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
        name = self.expect(TokenType.NAME).lexeme
        self.expect(TokenType.EQ)
        self.expect(TokenType.LPAREN)
        token_list.append(Token(TokenType.LSQUARE, None, -1))
        token_list += self.value()
        token_list.append(self.expect(TokenType.COMMA))
        token_list += self.value()
        token_list.append(self.expect(TokenType.COMMA))
        token_list += self.value()
        self.expect(TokenType.RPAREN)
        token_list.append(Token(TokenType.RSQUARE, None, -1))
        self.linebreak()

        self.vertices[name] = token_list

    # face_def := { int, int, int } \n
    def face_def(self):
        triplet = []
        self.expect(TokenType.LBRACE)
        triplet.append(self.expect(TokenType.INT).lexeme)
        self.expect(TokenType.COMMA)
        triplet.append(self.expect(TokenType.INT).lexeme)
        self.expect(TokenType.COMMA)
        triplet.append(self.expect(TokenType.INT).lexeme)
        self.expect(TokenType.RBRACE)
        self.linebreak()

        self.faces.append(triplet)

    # constant_block := constant_seq*
    def constant_block(self):
        t1 = self.lexer.peek(1).ttype
        t2 = self.lexer.peek(2).ttype
        t3 = self.lexer.peek(3).ttype
        t4 = self.lexer.peek(4).ttype
        t5 = self.lexer.peek(5).ttype
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
        ):
            self.constant_def()
            t1 = self.lexer.peek(1).ttype
            t2 = self.lexer.peek(2).ttype
            t3 = self.lexer.peek(3).ttype
            t4 = self.lexer.peek(4).ttype
            t5 = self.lexer.peek(5).ttype

    # vertex_block := vertex_def*
    def vertex_block(self):
        t1 = self.lexer.peek(1).ttype
        t2 = self.lexer.peek(2).ttype
        while t1 == TokenType.NAME and t2 == TokenType.EQ:
            self.vertex_def()
            t1 = self.lexer.peek(1).ttype
            t2 = self.lexer.peek(2).ttype

    # face_block := Faces : \n face_def*
    def face_block(self):
        if not self.expect(TokenType.NAME).lexeme == "Faces":
            self.syntax_error()
        self.expect(TokenType.COLON)
        self.linebreak()
        while self.lexer.peek(1).ttype == TokenType.LBRACE:
            self.face_def()

    # polyhedron := name_def constant_block vertex_block face_block EOF
    def polyhedron(self) -> Polyhedron:
        self.name_def()
        self.constant_block()
        self.vertex_block()
        self.face_block()
        self.expect(TokenType.EOF)

        return Polyhedron(
            self.name,
            self.vertices,
            self.faces,
            self.constant_exacts,
            self.constant_floats,
            self.constant_sequence,
        )

    def dump_tokenstream(self):
        while self.lexer.peek(1).ttype != TokenType:
            tok = self.lexer.get()
            print(tok.ttype, tok.lexeme)


def main():
    with open("../data/DisdyakisTriacontahedron.txt") as f:
        parser = Parser(f.read())
    polyhedron = parser.polyhedron()
    print(polyhedron.openscad())


if __name__ == "__main__":
    main()
