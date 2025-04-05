from ply import lex
from prettytable import PrettyTable

class Token:
    def __init__(self, type, value, lineno):
        self.type = type  # 单词类型（如 ID, INTC, PROGRAM 等）
        self.value = value  # 单词的值（如标识符名、整数值等）
        self.lineno = lineno  # 单词所在的行号

class SNLLexer:
    def __init__(self):
        self.tokens = (
            # 关键字
            'PROGRAM', 'PROCEDURE', 'TYPE', 'VAR', 'IF', 'THEN', 'ELSE', 'FI',
            'WHILE', 'DO', 'ENDWH', 'BEGIN', 'END', 'READ', 'WRITE', 'ARRAY', 'OF',
            'RECORD', 'RETURN',
            # 类型
            'INTEGER', 'CHAR',
            # 标识符和常量
            'ID', 'INTC', 'CHARC', 
            # 运算符和符号
            'ASSIGN', 'EQ', 'LT', 'PLUS', 'MINUS', 'TIMES',
            'OVER', 'LPAREN', 'RPAREN', 'LMIDPAREN', 'RMIDPAREN', 'UNDERANGE',
            'SEMI', 'COMMA', 'DOT'
        )

        self.reserved = {
            'program': 'PROGRAM',
            'procedure': 'PROCEDURE',
            'type': 'TYPE',
            'var': 'VAR',
            'if': 'IF',
            'then': 'THEN',
            'else': 'ELSE',
            'fi': 'FI',
            'while': 'WHILE',
            'do': 'DO',
            'endwh': 'ENDWH',
            'begin': 'BEGIN',
            'end': 'END',
            'read': 'READ',
            'write': 'WRITE',
            'array': 'ARRAY',
            'of': 'OF',
            'record': 'RECORD',
            'return': 'RETURN',
            'integer': 'INTEGER',
            'char': 'CHAR'
        }

        self.lexer = lex.lex(module=self)  # 指的是让lexer使用本类中的方法

    # 正则表达式规则
    t_ASSIGN = r':='
    t_EQ = r'='
    t_LT = r'<'
    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_TIMES = r'\*'
    t_OVER = r'/'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LMIDPAREN = r'\['
    t_RMIDPAREN = r'\]'
    t_UNDERANGE = r'\.\.'
    t_SEMI = r';'
    t_COMMA = r','
    t_DOT = r'\.'
    t_ignore = ' \t'

    def t_ID(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_]*'
        t.type = self.reserved.get(t.value.lower(), 'ID')
        return t

    def t_INTC(self, t):
        r'\d+'
        t.value = int(t.value)
        return t

    def t_CHARC(self, t):
        r"'([^\\']|\\')'"
        t.value = t.value[1:-1].replace("\\'", "'")
        return t

    def t_COMMENT(self, t):
        r'\{[^}]*\}'
        pass

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    def t_error(self, t):
        print(f"非法字符 '{t.value[0]}' 在行 {t.lineno}")
        t.lexer.skip(1)

    def analyze_file(self, input_file, output_file):
        try:
            with open(input_file, "r", encoding="utf-8") as r:
                data = r.read()
            self.lexer.input(data)

            table = PrettyTable(field_names=["行", "语义信息", "词法信息"])
            tokens = []

            while True:
                tok = self.lexer.token()
                if not tok:
                    break
                table.add_row([tok.lineno, tok.value, tok.type])
                tokens.append(Token(tok.type, tok.value, tok.lineno))

            with open(output_file, "w", encoding="utf-8") as w:
                w.write(table.get_string())
            print(f"output is in {output_file}")
            return tokens
        
        except FileNotFoundError:
            print(f"错误：文件 '{input_file}' 未找到。")


if __name__ == '__main__':
    lexer = SNLLexer()
    lexer.analyze_file("./data/demo.txt", "./data/token.txt")