from enum import Enum


class TokenType(Enum):
    NAME = 0
    EQ = 1
    EXPR = 2
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


class Token:
    def __init__(self, ttype: TokenType, lexeme: str | None, pos: int) -> None:
        self.ttype = ttype
        self.lexeme = lexeme
        self.pos = pos


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


class Parser:
    def __init__(self, input) -> None:
        self.lexer = Lexer()
        self.lexer.lex(input)

        self.vertices = []
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

    # name_def := names* \n
    def name_def(self):
        names = []
        while self.lexer.peek(1).ttype == TokenType.NAME:
            names.append(self.expect(TokenType.NAME).ttype)
        self.expect(TokenType.NEWLINE)
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

        self.expect(TokenType.NEWLINE)

        self.constant_sequence.append(const)
        self.constant_exacts[const] = exactv
        self.constant_floats[const] = floatv

    # value := -? [name|int|float]
    def value(self):
        if self.lexer.peek(1).ttype == TokenType.MINUS:
            self.expect(TokenType.MINUS)

        ttype = self.lexer.peek(1).ttype
        match ttype:
            case TokenType.NAME:
                self.expect(TokenType.NAME)
            case TokenType.INT:
                self.expect(TokenType.INT)
            case TokenType.FLOAT:
                self.expect(TokenType.FLOAT)
            case _:
                self.syntax_error()

    # vertex_def := name = (value, value, value) \n
    def vertex_def(self):
        self.expect(TokenType.LPAREN)
        self.value()
        self.expect(TokenType.COMMA)
        self.value()
        self.expect(TokenType.COMMA)
        self.value()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.NEWLINE)

    # face_def := { int, int, int } \n
    def face_def(self):
        self.expect(TokenType.LBRACE)
        self.expect(TokenType.INT)
        self.expect(TokenType.COMMA)
        self.expect(TokenType.INT)
        self.expect(TokenType.COMMA)
        self.expect(TokenType.INT)
        self.expect(TokenType.RBRACE)
        self.expect(TokenType.NEWLINE)

    # constant_block := constant_seq*
    def constant_block(self):
        t1 = self.lexer.peek(1).ttype
        t2 = self.lexer.peek(2).ttype
        t3 = self.lexer.peek(3).ttype
        while (
            t1 == TokenType.NAME
            and t2 == TokenType.EQ
            and (t3 == TokenType.FLOAT or self.is_expression_ttype(t3))
        ):
            self.constant_def()
            t1 = self.lexer.peek(1).ttype
            t2 = self.lexer.peek(2).ttype
            t3 = self.lexer.peek(3).ttype

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
        self.expect(TokenType.NEWLINE)
        while self.lexer.peek(1).ttype == TokenType.LBRACE:
            self.face_def()

    # polyhedron := name_def constant_block vertex_block face_block EOF
    def polyhedron(self):
        self.name_def()
        self.constant_block()
        self.vertex_block()
        self.expect(TokenType.EOF)


def main():
    with open("../data/DisdyakisTriacontahedron.txt") as f:
        parser = Parser(f.read())
    while parser.lexer.peek(1).ttype != TokenType:
        print(parser.lexer.get().ttype)


if __name__ == "__main__":
    main()
