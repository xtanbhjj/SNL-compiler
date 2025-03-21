from parser import *

class SymbolTable:
    def __init__(self, name, parent=None):
        self.name = name          # 作用域名称（如全局、过程名）
        self.parent = parent      # 父作用域
        self.symbols = {}         # 符号表内容 {name: (type, category)}
        self.children = []        # 子作用域（用于嵌套）

    def add_symbol(self, name, symbol_type, category='variable'):
        if name in self.symbols:
            return False  # 重复定义
        self.symbols[name] = (symbol_type, category)
        return True

    def lookup(self, name):
        current = self
        while current:
            if name in current.symbols:
                return current.symbols[name]
            current = current.parent
        return None  # 未找到

class RecType:
    def __init__(self, fields):
        """
        初始化 RecType 对象。

        Args:
            fields: 一个字典，键是字段名（字符串），值是字段的类型（可以是 "INTEGER", "CHAR", 或 ArrayType 的实例）。
        """
        self.fields = fields

    def __str__(self):
        fields_str = ", ".join([f"{name}: {type}" for name, type in self.fields.items()])
        return f"RECORD ({fields_str})"

    def __repr__(self):
        return f"RecType(fields={self.fields})"

class ArrayType:
    def __init__(self, lower_bound, upper_bound, element_type):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.element_type = element_type

    def __str__(self):
        return f"ARRAY [{self.lower_bound}..{self.upper_bound}] OF {self.element_type}"

    def __repr__(self):
        return f"ArrayType(lower_bound={self.lower_bound}, upper_bound={self.upper_bound}, element_type='{self.element_type}')"
    
    
class SemanticAnalyzer:
    def __init__(self):
        self.current_scope = SymbolTable("global")
        self.scope_stack = [self.current_scope]  # 作用域堆栈
        self.type_table = {}       # 类型表，记录用户定义类型
        self.errors = []           # 收集错误信息

    def lookup_type_table(self, name):
        return self.type_table.get(name, None)

    def enter_scope(self, name):
        new_scope = SymbolTable(name, parent=self.current_scope)
        self.current_scope.children.append(new_scope)
        self.scope_stack.append(new_scope)
        self.current_scope = new_scope

    def exit_scope(self):
        # 退出作用域时打印符号表
        print(f"\n退出作用域 '{self.current_scope.name}'，符号表内容：")
        for name, (type_, category) in self.current_scope.symbols.items():
            print(f"  {name}: 类型={type_}, 类别={category}")
        self.scope_stack.pop()
        self.current_scope = self.scope_stack[-1]

    def analyze(self, ast):
        if ast is None:
            return
        self.visit(ast)
        # 打印所有错误
        if self.errors:
            print("\n语义错误列表：")
            for error in self.errors:
                print(error)

    def error(self, message, lineno=None):
        err_msg = f"语义错误: {message}"
        if lineno:
            err_msg += f" (行号: {lineno})"
        self.errors.append(err_msg)

    def visit(self, node):
        if isinstance(node, tuple):
            node_type = node[0]
            method_name = f'visit_{node_type}'
            if hasattr(self, method_name):
                getattr(self, method_name)(node)
            else:
                self.error(f"未知的节点类型: {node_type}")
        elif isinstance(node, list):
            for child in node:
                self.visit(child)
        elif node is not None:
            pass  # 忽略基础类型（如字符串、数字）

    # ----------- 处理所有节点类型 -----------
    def visit_Program(self, node):
        _, program_head, declare_part, program_body = node
        self.visit(program_head)
        self.visit(declare_part)
        self.visit(program_body)

    # program_head
    def visit_ProgramHead(self, node):
        _, program_name = node
        self.visit(program_name)

    def visit_ProgramName(self, node):
        pass  # 程序名无需处理

    # DeclarePart
    def visit_DeclarePart(self, node):
        _, type_dec, var_dec, proc_dec = node
        self.visit(type_dec)  # 处理类型声明
        print(self.type_table)
        self.visit(var_dec)   # 处理变量声明
        print(self.current_scope.symbols)
        self.visit(proc_dec)  # 处理过程声明

    def _resolve_type(self, type_name_node):

        if type_name_node and len(type_name_node) == 2 and type_name_node[0] == 'TypeName':
            type_name_content = type_name_node[1]
            if isinstance(type_name_content, str):
                # Rule 14: TypeName -> ID
                if not self.lookup_type_table(type_name_content):
                    self.error(f"类型 '{type_name_content}' 未定义")
                return type_name_content
                
            elif isinstance(type_name_content, tuple) and len(type_name_content) == 2:
                tag = type_name_content[0]
                if tag == 'BaseType':
                    # Rule 12: TypeName -> BaseType
                    return self.analyze_base_type(type_name_content)
                elif tag == 'StructureType':
                    # Rule 13: TypeName -> StructureType
                    return self.analyze_structure_type(type_name_content)
        return None

    def analyze_base_type(self, base_type_node):
        """
        解析 BaseType 节点并返回其具体的类型字符串。
        """
        if base_type_node and len(base_type_node) == 2 and base_type_node[0] == 'BaseType':
            return base_type_node[1]
        return None

    def analyze_structure_type(self, structure_type_node):
        """
        解析 StructureType 节点并返回其具体的结构类型信息。
        """
        if structure_type_node and len(structure_type_node) == 2 and structure_type_node[0] == 'StructureType':
            structure_content = structure_type_node[1]
            if isinstance(structure_content, tuple) and len(structure_content) > 0 and structure_content[0] == 'ArrayType':
                lower_bound = structure_content[1]
                upper_bound = structure_content[2]
                element_type = self.analyze_base_type(structure_content[3])
                if element_type:
                    try:
                        lower_bound = int(lower_bound)
                        upper_bound = int(upper_bound)
                        return ArrayType(lower_bound, upper_bound, element_type)
                    except ValueError:
                        print(f"警告: 数组边界不是整数: {lower_bound}, {upper_bound}")
                        return None
            elif isinstance(structure_content, tuple) and len(structure_content) == 2 and structure_content[0] == 'RecType' :
                fields = self.parse_dec_list(structure_content[1])
                #print(fields)
                if fields is not None:
                    return RecType(fields)
            return None
    def parse_dec_list(self, field_dec_list_node):
        """
        Returns:
            dict: 字段字典，键是字段名，值是字段类型。
                如果解析失败，返回 None。
        """
        if not field_dec_list_node or not isinstance(field_dec_list_node, tuple) or len(field_dec_list_node) == 0 or field_dec_list_node[0] != 'FieldDecList':
            return {}

        fields = {}
        current_node = field_dec_list_node
        #print(field_dec_list_node)

        while current_node and isinstance(current_node, tuple) and len(current_node) > 0 and current_node[0] == 'FieldDecList':
            # Rule 21: FieldDecList -> BaseType IdList SEMI FieldDecMore
            # Rule 22: FieldDecList -> ArrayType IdList SEMI FieldDecMore
            if len(current_node) == 4:
                type_node = current_node[1]
                id_list_node = current_node[2]  # 注意这里索引是 2，因为 SEMI 是索引 2
                field_dec_more_node = current_node[3]

                field_type = None
                if type_node[0] == 'BaseType':
                    field_type = self.analyze_base_type(type_node)
                elif type_node[0] == 'ArrayType':
                    # 需要将 ArrayType 节点包装成 TypeName 的形式传递给 analyze_type_name
                    field_type = self.analyze_type_name(('TypeName', ('StructureType', type_node)))

                if field_type:
                    ids = self.parse_id_list(id_list_node)
                    if ids:
                        for id_name in ids:
                            fields[id_name] = field_type

                    # 处理 FieldDecMore
                    if field_dec_more_node and isinstance(field_dec_more_node, tuple) and len(field_dec_more_node) > 0:
                        if field_dec_more_node[0] == 'FieldDecList':
                            # Rule 24: FieldDecMore -> FieldDecList
                            more_fields = self.parse_dec_list(field_dec_more_node)
                            if more_fields:
                                fields.update(more_fields)
                        elif field_dec_more_node[0] == 'empty':
                            # Rule 23: FieldDecMore -> <empty>
                            break
            break # 处理完当前的 FieldDecList 就退出，FieldDecMore 会处理后续的

        return fields
    def parse_id_list(self, id_list_node):
        """
        解析 IdList, VarIdlist 节点并返回标识符列表。
        Returns:
            list: 标识符名称列表。
                如果解析失败，返回 None。
        """
        if not id_list_node or not isinstance(id_list_node, tuple) or len(id_list_node) == 0:
            return

        ids = []
        if len(id_list_node) == 3:
            # Rule 25: IdList -> ID IdMore
            if isinstance(id_list_node[1], str):
                ids.append(id_list_node[1])
                id_more_node = id_list_node[2] # 这里应该是 id_list_node[1] 才是 ID，id_list_node[2] 是 IdMore
                if isinstance(id_more_node, tuple):
                    ids.extend(self.parse_id_more(id_more_node))
        return ids

    def parse_id_more(self, id_more_node):
        """
        解析 IdMore, VarIDMore 节点并返回标识符列表。
        Returns:
            list: 标识符名称列表。
        """
        ids = []
        if not id_more_node or not isinstance(id_more_node, tuple) or len(id_more_node) == 0:
            return
        if len(id_more_node) == 2 and id_more_node[1] != None:
            ids.extend(self.parse_id_list(id_more_node[1]))
        return ids
    '''
    TypeDeclaration
    '''
    def visit_TypeDec(self, node):
        _, type_decl = node
        if type_decl is not None:
            self.visit(type_decl)

    def visit_TypeDeclaration(self, node):
        _, type_dec_list = node
        self.visit(type_dec_list)

    def visit_TypeDecList(self, node):
        _, type_id, type_name, type_dec_more = node
        type_id_name = type_id[1]
        if type_id_name in self.type_table:
            self.error(f"类型 '{type_id_name}' 重复定义")
        else:
            self.type_table[type_id_name] = self._resolve_type(type_name)
        self.visit(type_dec_more)
    
    def visit_TypeDecMore(self, node):
        _, type_dec_list = node
        if type_dec_list:
            self.visit(type_dec_list)

    '''
    VarDeclaration
    '''
    def visit_VarDec(self, node):
        _, var_decl = node
        if var_decl is not None:
            self.visit(var_decl)

    def visit_VarDeclaration(self, node):
        _, var_dec_list = node
        self.visit(var_dec_list)

    def visit_VarDecList(self, node):
        _, type_node, var_id_list, var_dec_more = node
        var_type = self._resolve_type(type_node)
        if var_type:
            ids = self.parse_id_list(var_id_list)
            if ids:
                for id_name in ids:
                    if not self.current_scope.add_symbol(id_name, var_type):
                        self.error(f"Variable {id_name} already defined in this scope")

        self.visit(var_dec_more)
    
    def visit_VarDecMore(self, node):
        _, var_dec_list = node
        if var_dec_list:
            self.visit(var_dec_list)

    '''
    def visit_ProcDeclaration(self, node):
        _, proc_name, param_list, proc_dec_part, proc_body, proc_dec_more = node
        proc_name = proc_name[1]
        # 进入过程作用域
        self.enter_scope(proc_name)
        # 处理参数
        self.visit(param_list)
        # 处理过程内的声明和语句
        self.visit(proc_dec_part)
        self.visit(proc_body)
        # 退出作用域
        self.exit_scope()
        self.visit(proc_dec_more)

    def visit_Param(self, node):
        if len(node) == 3:  # TypeName FormList
            type_node, form_list = node[1], node[2]
            param_type = self._resolve_type(type_node)
            self.visit(form_list, param_type)
        elif len(node) == 4:  # VAR TypeName FormList
            type_node, form_list = node[2], node[3]
            param_type = f"var {self._resolve_type(type_node)}"
            self.visit(form_list, param_type)

    def visit_FormList(self, node, param_type):
        _, param_id, fid_more = node
        if not self.current_scope.add_symbol(param_id[1], param_type, 'param'):
            self.error(f"参数 '{param_id[1]}' 重复定义")
        self.visit(fid_more, param_type)

    def visit_Stm(self, node):
        if len(node) == 2:
            self.visit(node[1])
        elif len(node) == 3:  # ID AssCall
            var_name = node[1][1]
            var_info = self.current_scope.lookup(var_name)
            if not var_info:
                self.error(f"变量 '{var_name}' 未声明")
            self.visit(node[2])

    def visit_AssignmentRest(self, node):
        _, vari_more, exp = node
        # 检查变量类型和表达式类型是否匹配
        var_type = self._get_variable_type(vari_more)
        exp_type = self._get_expression_type(exp)
        if var_type != exp_type:
            self.error(f"类型不匹配: 不能将 {exp_type} 赋值给 {var_type}")

    def _get_variable_type(self, vari_more):
        # 简化处理：假设变量是基本类型
        return 'integer'  # 实际应根据符号表查找

    def _get_expression_type(self, exp_node):
        # 简化处理：假设表达式类型为 integer
        return 'integer'

    # ----------- 其他节点处理（省略部分代码） -----------
    # 补全所有缺失的节点处理函数（如 visit_TypeDecMore, visit_VarDecMore 等）
    def visit_TypeDecMore(self, node):
        _, content = node
        if content:
            self.visit(content)

    def visit_VarDecMore(self, node):
        _, content = node
        if content:
            self.visit(content)

    def visit_FidMore(self, node):
        _, content = node
        if content:
            self.visit(content)

    def visit_ParamMore(self, node):
        _, content = node
        if content:
            self.visit(content)

    def visit_VariMore(self, node):
        _, content = node
        if content:
            self.visit(content)

    def visit_OtherFactor(self, node):
        _, content = node
        if content:
            self.visit(content)

    def visit_OtherTerm(self, node):
        _, content = node
        if content:
            self.visit(content)

    def visit_OtherRelE(self, node):
        _, content = node
        if content:
            self.visit(content)

    def visit_StmMore(self, node):
        _, content = node
        if content:
            self.visit(content)

    def visit_ProcDecMore(self, node):
        _, content = node
        if content:
            self.visit(content)

    def visit_Invar(self, node):
        var_name = node[1][1]
        if not self.current_scope.lookup(var_name):
            self.error(f"输入变量 '{var_name}' 未声明")'
    '''

if __name__ == '__main__':
    parser = SNLParser()
    parse_tree = parser.parse_file("./data/demo.txt")

    if parse_tree:
        print("\n语法分析成功！")
        semantic_analyzer = SemanticAnalyzer()
        semantic_analyzer.analyze(parse_tree)
        print("\n语义分析完成！")
    else:
        print("\n语法分析失败！")