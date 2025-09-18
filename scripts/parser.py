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
                case '(':
                    self.tokenstream.append(Token(TokenType.LPAREN, None, i))
                    i += 1
                case ')':
                    self.tokenstream.append(Token(TokenType.RPAREN, None, i))
                    i += 1
                case '{':
                    self.tokenstream.append(Token(TokenType.LBRACE, None, i))
                    i += 1
                case '}':
                    self.tokenstream.append(Token(TokenType.RBRACE, None, i))
                    i += 1
                case '=':
                    self.tokenstream.append(Token(TokenType.EQ, None, i))
                    i += 1
                case '-':
                    self.tokenstream.append(Token(TokenType.MINUS, None, i))
                    i += 1
                case ',':
                    self.tokenstream.append(Token(TokenType.COMMA, None, i))
                    i += 1
                case '*':
                    self.tokenstream.append(Token(TokenType.STAR, None, i))
                    i += 1
                case '+':
                    self.tokenstream.append(Token(TokenType.PLUS, None, i))
                    i += 1
                case '/':
                    self.tokenstream.append(Token(TokenType.SLASH, None, i))
                    i += 1
                case '^':
                    self.tokenstream.append(Token(TokenType.CARET, None, i))
                    i += 1
                case ':':
                    self.tokenstream.append(Token(TokenType.COLON, None, i))
                    i += 1
                case '\n':
                    self.tokenstream.append(Token(TokenType.NEWLINE, None, i))
                    i += 1
                case ' ' | '\t':
                    i += 1
                case '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9' :
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

    def peek(self, i: int) -> Token | None:
        assert i > 0
        if self.pos + i > len(self.tokenstream):
            return None

        token = self.tokenstream[self.pos + i - 1]
        return token


class Parser:
    def __init__(self, input) -> None:
        self.lexer = Lexer()
        self.lexer.lex(input)

        self.vertices = []
        self.faces = []
        self.name = None
        self.constants = []

    def expect(self, ttype: TokenType) -> Token:
        token = self.lexer.get()
        if token.ttype != ttype:
            raise Exception(f"Bad expect at position {token.pos}")

        return token


def main():
    with open("../data/DisdyakisTriacontahedron.txt") as f:
        parser = Parser(f.read())
    while parser.lexer.peek(1):
        print(parser.lexer.get().ttype)

if __name__ == "__main__":
    main()

