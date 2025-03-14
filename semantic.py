from lexer import SNLLexer  # 导入词法分析器
from parser import SNLParser  # 导入语法分析器

class Symbol:
    def __init__(self, name, category, type=None, params=None, array_range=None, fields=None):
        self.name = name
        self.category = category  # 'variable', 'type', 'procedure'
        self.type = type
        self.params = params or []  # 过程参数列表
        self.array_range = array_range  # 数组类型范围 (low, high)
        self.fields = fields or {}  # 结构体字段字典

class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = [{}]  # 符号表栈
        self.errors = []
        self.current_proc = None

    def enter_scope(self):
        self.symbol_table.append({})

    def exit_scope(self):
        if len(self.symbol_table) > 1:
            self.symbol_table.pop()

    def add_symbol(self, symbol):
        if symbol.name in self.symbol_table[-1]:
            self.error(f"重复定义标识符：{symbol.name}")
        self.symbol_table[-1][symbol.name] = symbol

    def lookup(self, name):
        for scope in reversed(self.symbol_table):
            if name in scope:
                return scope[name]
        self.error(f"未声明的标识符：{name}")
        return None

    def error(self, msg):
        self.errors.append(msg)

    def analyze(self, ast):
        self.visit(ast)
        if self.errors:
            print("\n语义错误：")
            for err in self.errors:
                print(f"  - {err}")
        else:
            print("\n语义分析成功！")

    def visit(self, node):
        if not isinstance(node, tuple):
            return
        method = 'visit_' + node[0]
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        for child in node[1:]:
            self.visit(child)

    # 声明部分处理
    def visit_TypeDecList(self, node):
        type_id = node[1][1]
        type_name = node[2][1]
        if type_name in ('INTEGER', 'CHAR'):
            self.add_symbol(Symbol(type_id, 'type', type_name))
        else:
            # 处理结构类型
            self.add_symbol(Symbol(type_id, 'type', type_name))
        self.visit(node[3])

    def visit_VarDecList(self, node):
        type_name = node[1][1]
        var_list = node[2]
        for var in self._extract_var_list(var_list):
            if var in self.symbol_table[-1]:
                self.error(f"重复定义变量：{var}")
            self.add_symbol(Symbol(var, 'variable', type_name))
        self.visit(node[3])

    def _extract_var_list(self, node):
        vars = []
        while node is not None:
            vars.append(node[1])
            node = node[2][1] if node[2] else None
        return vars

    def visit_ProcDeclaration(self, node):
        proc_name = node[1][1]
        params = self._process_param_list(node[2])
        self.add_symbol(Symbol(proc_name, 'procedure', params=params))
        self.enter_scope()
        for param in params:
            self.add_symbol(param)
        self.visit(node[3])  # 处理过程声明部分
        self.visit(node[4])  # 处理过程体
        self.exit_scope()
        self.visit(node[5])  # 处理后续过程声明

    def _process_param_list(self, node):
        params = []
        if not node or not node[1]:
            return params
        current = node[1]
        while True:
            is_var = current[1] == 'VAR'
            type_name = current[2][1] if is_var else current[1][1]
            form_list = current[3] if is_var else current[2]
            for var in self._extract_form_list(form_list):
                params.append(Symbol(var, 'variable', type_name))
            if not current[2][1] or not current[2][1][1]:
                break
            current = current[2][1][1]
        return params

    def _extract_form_list(self, node):
        vars = []
        while node is not None:
            vars.append(node[1])
            node = node[2][1] if node[2] else None
        return vars

    # 语句部分处理
    def visit_AssignmentRest(self, node):
        var_info = self.visit(node[1])
        exp_type = self.visit(node[2])
        if var_info and exp_type:
            if var_info.category != 'variable':
                self.error(f"赋值左值必须是变量：{var_info.name}")
            if var_info.type != exp_type:
                self.error(f"类型不匹配：{var_info.type} 和 {exp_type}")

    def visit_Variable(self, node):
        var_name = node[1]
        symbol = self.lookup(var_name)
        vari_more = node[2]
        if not vari_more or not vari_more[1]:
            return symbol
        # 处理数组或结构体访问
        if vari_more[0] == 'VariMore' and vari_more[1]:
            if symbol.type.category != 'array':
                self.error(f"需要数组类型：{var_name}")
            index = self.visit(vari_more[1])
            if index != 'INTEGER':
                self.error("数组下标必须是整数")
            return Symbol('', 'variable', symbol.type.element_type)
        elif vari_more[0] == 'VariMore' and vari_more[2]:
            field = vari_more[2][1]
            if symbol.type.category != 'record':
                self.error(f"需要结构体类型：{var_name}")
            if field not in symbol.type.fields:
                self.error(f"未知字段：{field}")
            return symbol.type.fields[field]
        return symbol

    def visit_CallStmRest(self, node):
        proc_name = node[-1]  # 需要从父节点获取
        proc = self.lookup(proc_name)
        if proc.category != 'procedure':
            self.error(f"需要过程标识符：{proc_name}")
        actual_params = self.visit(node[1])
        if len(actual_params) != len(proc.params):
            self.error(f"参数数量不匹配：{proc_name}")
        for a, f in zip(actual_params, proc.params):
            if a != f.type:
                self.error(f"参数类型不匹配：{a} 和 {f.type}")

    def visit_RelExp(self, node):
        left = self.visit(node[1])
        right = self.visit(node[2][2])
        if left != right:
            self.error("关系运算符类型不匹配")
        return 'BOOLEAN'

    def visit_Exp(self, node):
        term = self.visit(node[1])
        other = node[2][1] if node[2] else None
        if not other:
            return term
        op = other[1][1]
        exp_type = self.visit(other[2])
        if term != exp_type:
            self.error(f"操作符 {op} 类型不匹配")
        return term

    def visit_Term(self, node):
        factor = self.visit(node[1])
        other = node[2][1] if node[2] else None
        if not other:
            return factor
        op = other[1][1]
        term_type = self.visit(other[2])
        if factor != term_type:
            self.error(f"操作符 {op} 类型不匹配")
        return factor

    def visit_Factor(self, node):
        if node[1][0] == 'Variable':
            return self.visit(node[1]).type
        elif node[1][0] == 'INTC':
            return 'INTEGER'
        else:
            return self.visit(node[1])

    # 主程序入口
    def run(self, ast):
        self.analyze(ast)
        return not self.errors
    

# 测试代码
if __name__ == '__main__':
    # 先进行词法和语法分析
    parser = SNLParser()
    ast = parser.parse_file("./data/demo.txt")
    
    if ast:
        print("开始语义分析...")
        analyzer = SemanticAnalyzer()
        success = analyzer.run(ast)
        if success:
            print("语义分析通过！")
        else:
            print("语义分析失败，请查看错误信息")
    else:
        print("语法分析失败，无法进行语义分析")