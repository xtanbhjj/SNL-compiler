import sys
sys.path.append("../")
from lexer import *
from Quad import *

class ConstantFolder:
    def __init__(self, quad_list):
        self.quad_list = quad_list
        self.optimized_quads = []
        self.const_table = {}  # 记录变量的常量值，如 {'t1': 7, 'x': 3}

    def is_constant(self, operand):
        # 是常数字面量，或之前已经是常量表达式的变量
        return self.is_immediate_constant(operand) or operand in self.const_table

    def is_immediate_constant(self, operand):
        try:
            float(operand)
            return True
        except:
            return False

    def get_constant_value(self, operand):
        if self.is_immediate_constant(operand):
            return float(operand)
        elif operand in self.const_table:
            return self.const_table[operand]
        else:
            return None

    def fold_constants(self):
        for quad in self.quad_list:
            op = quad.operator
            arg1 = quad.operand1
            arg2 = quad.operand2
            res = quad.result

            if op in ['WHILE', 'ENDWHILE', 'DO', 'THEN', 'ELSE', 'PROCEDURE', 'ENDIF', 'ENDPROCEDURE']:
                self.const_table = {}
                self.optimized_quads.append(quad)
                continue
            if op in ['+', '-', '*', '/']:
                if self.is_constant(arg1) and self.is_constant(arg2):
                    val1 = self.get_constant_value(arg1)
                    val2 = self.get_constant_value(arg2)
                    try:
                        if op == '+':
                            result = val1 + val2
                        elif op == '-':
                            result = val1 - val2
                        elif op == '*':
                            result = val1 * val2
                        elif op == '/':
                            result = val1 / val2
                        if result == int(result):
                            result = int(result)
                        self.const_table[res] = result
                        if res[0] != 't':
                            self.optimized_quads.append(Quadruple(':=', result, None, res))
                    except ZeroDivisionError:
                        print(f"Warning: division by zero in quad {quad}")
                        self.optimized_quads.append(quad)
                else:
                    if arg1 in self.const_table:
                        self.optimized_quads.append(Quadruple(':=', self.const_table[arg1], None, arg1)) 
                    if arg2 in self.const_table:
                        self.optimized_quads.append(Quadruple(':=', self.const_table[arg2], None, arg2))
                    new_arg1 = str(self.const_table[arg1]) if arg1 in self.const_table else arg1
                    new_arg2 = str(self.const_table[arg2]) if arg2 in self.const_table else arg2
                    self.optimized_quads.append(Quadruple(op, arg1, arg2, res))
                    # 运算结果未知，移除res的常量记录
                    if res in self.const_table:
                        del self.const_table[res]

            elif op == ':=':
                # 赋值语句，尝试更新 const_table
                if self.is_constant(arg1):
                    value = self.get_constant_value(arg1)
                    if value == int(value):
                        value = int(value)
                    self.const_table[res] = value
                    if res[0] != 't':
                        self.optimized_quads.append(Quadruple(':=', value, None, res))
                else:
                    self.optimized_quads.append(Quadruple(op, arg1, None, res))
                    if res in self.const_table:
                        del self.const_table[res]
            else:
                # 其他操作，不处理，原样加入
                self.optimized_quads.append(quad)
        table = PrettyTable(field_names=["operator", "exp1", "exp2", "result"])
        for i in self.optimized_quads:
            table.add_row([i.operator, i.operand1, i.operand2, i.result])
        with open("../result/中间代码优化.txt", "w", encoding="utf-8") as w:
            w.write(table.get_string())
        return self.quad_list

if __name__ == '__main__':
    parser = SNLParser()
    parse_tree = parser.parse_file("../data/9-constOpt.txt")
    print(parse_tree)

    if parse_tree:
        print("\n语法分析成功！")
        semantic_analyzer = SemanticAnalyzer()
        semantic_analyzer.analyze(parse_tree)
        print("\n语义分析完成！")
        print(len(semantic_analyzer.quadruples))
        folder = ConstantFolder(semantic_analyzer.quadruples)
        optimized_quads = folder.fold_constants()
        print(len(optimized_quads))
        for i in optimized_quads:
            print(i)
    else:
        print("\n语法分析失败！")
