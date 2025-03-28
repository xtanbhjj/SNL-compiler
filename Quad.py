from parser import *
from lexer import *

class Quadruple:
    def __init__(self, operator, operand1, operand2, result):
        self.operator = operator
        self.operand1 = operand1
        self.operand2 = operand2
        self.result = result

    def __str__(self):
        return f"({self.operator}, {self.operand1}, {self.operand2}, {self.result})"

from parser import *

class SymbolTable:
    def __init__(self, name, parent=None):
        self.name = name          # 作用域名称（如全局、过程名）
        self.parent = parent      # 父作用域
        self.symbols = {}         # 符号表内容 {name: (type, category)}
        self.children = []        # 子作用域（用于嵌套）
        self.offset = 0

    def add_symbol(self, name, symbol_type, category='variable'):
        if name in self.symbols:
            return None, None, None  # 重复定义
        self.symbols[name] = (symbol_type, self.offset, category)
        #print(symbol_type)
        length = 0
        if symbol_type == "integer":
            length = 1
        elif symbol_type == "char":
            length = 1
        else:
            length = symbol_type.size
        self.offset += length
        return name, length, self.symbols[name][1]

    def lookup(self, name):
        current = self
        while current:
            if name in current.symbols:
                return current.symbols[name]
            current = current.parent
        return None  # 未找到

class ProcType:
    """表示过程的类型，存储形参信息（类型和传递方式）"""
    def __init__(self):
        self.params = []  # 形参列表，每个元素为 (参数类型, 是否引用传递)
        self.size = 0

    def add_param(self, param_type):
        """添加形参到参数列表"""
        self.params.append((param_type))

    def __repr__(self):
        params_str = ", ".join(
            [f"{param_type}" 
             for param_type in self.params]
        )
        return f"ProcType(params=[{params_str}])"

class RecType:
    def __init__(self, fields):
        """
        初始化 RecType 对象。

        Args:
            fields: 一个字典，键是字段名（字符串），值是字段的类型（可以是 "INTEGER", "CHAR", 或 ArrayType 的实例）。
        """
        self.fields = fields
        self.offset = {}
        self.size = 0
        #print(self.fields)
        for name, type in self.fields.items():
            self.offset[name] = self.size
            if type == "integer":
                self.size += 1
            elif type == "char":
                self.size += 1
            else:
                self.size += type.size      

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
        self.size = upper_bound - lower_bound + 1

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
        self.quadruples = []
        self.flag = True
        self.temp_var_count = 0

    def generate_temp_var(self):
        self.temp_var_count += 1
        return f"t{self.temp_var_count}"
    
    def emit_quad(self, op, arg1, arg2, result):
        self.quadruples.append(Quadruple(op, arg1, arg2, result))

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
        for name, (type_, offset, category) in self.current_scope.symbols.items():
            print(f"  {name}: offset = {offset},类型={type_}, 类别={category}")
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
        else:
            for name, (type_, offset, category) in self.current_scope.symbols.items():
                print(f"  {name}: offset = {offset},类型={type_}, 类别={category}")
            table = PrettyTable(field_names=["operator", "exp1", "exp2", "result"])
            for i in self.quadruples:
                table.add_row([i.operator, i.operand1, i.operand2, i.result])
            with open("./data/exps.txt", "w", encoding="utf-8") as w:
                w.write(table.get_string())

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
        self.emit_quad("label", "here", None, None)
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
        #print(self.type_table)
        self.visit(var_dec)   # 处理变量声明
        #print(self.current_scope.symbols)
        if self.flag:
            self.emit_quad("Go", "here", None, None)
            self.flag = False
        self.visit(proc_dec)  # 处理过程声明

    def _resolve_type(self, type_name_node):

        if type_name_node and len(type_name_node) == 2 and type_name_node[0] == 'TypeName':
            type_name_content = type_name_node[1]
            if isinstance(type_name_content, str):
                # Rule 14: TypeName -> ID
                if not self.lookup_type_table(type_name_content):
                    self.error(f"类型 '{type_name_content}' 未定义")
                return self.lookup_type_table(type_name_content)
                
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
                #print(fields, "dwaidhiwa")
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
                field_dec_more_node = current_node[3][1]

                field_type = None
                if type_node[0] == 'BaseType':
                    field_type = self.analyze_base_type(type_node)
                elif type_node[0] == 'ArrayType':
                    # 需要将 ArrayType 节点包装成 TypeName 的形式传递给 analyze_type_name
                    field_type = self._resolve_type(('TypeName', ('StructureType', type_node)))
                    #print(field_type)

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
                            #print(more_fields)
                            if more_fields:
                                fields.update(more_fields)
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
                    name, length, offset = self.current_scope.add_symbol(id_name, var_type) 
                    if not name:
                        self.error(f"Variable {id_name} already defined in this scope")
                    else:
                        self.emit_quad('DECLARE', offset, length, name)

        self.visit(var_dec_more)
    
    def visit_VarDecMore(self, node):
        _, var_dec_list = node
        if var_dec_list:
            self.visit(var_dec_list)
    '''
    procedure declaration
    '''
    def visit_ProcDec(self, node):
        _, proc_dec = node
        if proc_dec:
            self.visit(proc_dec)

    def visit_ProcDeclaration(self, node):
        _, proc_name_node, param_list_node, proc_dec_part, proc_body, proc_dec_more = node
        proc_name = proc_name_node[1]
        self.emit_quad('PROCEDURE', proc_name, None, None)
        
        if self.current_scope.lookup(proc_name):
            self.error(f"过程 '{proc_name}' 重复定义")
            return
        Proc = ProcType()
        
        self.enter_scope(proc_name)
        
        # 处理参数列表
        self.visit(param_list_node)
        for i in self.current_scope.symbols:
            Proc.add_param(self.current_scope.symbols[i][0])
        num = len(Proc.params)
        for i in range(len(self.quadruples) - 1, -1, -1):
            if self.quadruples[i].operator == 'PROCEDURE':
                self.quadruples[i].result = num
                break
        self.current_scope.parent.add_symbol(proc_name, Proc, 'PROCEDURE')
        print(self.current_scope.symbols)
        print(self.current_scope.parent.symbols)
        
        # 处理过程内的声明部分
        self.visit(proc_dec_part)
        #print(self.type_table)
        
        # 处理过程体
        self.visit(proc_body)
        
        # 退出过程作用域
        self.exit_scope()
        
        # 处理后续过程声明
        self.visit(proc_dec_more)
        self.emit_quad('ENDPROCEDURE', None, None, None)

    def visit_ProcDecMore(self, node):
        _, proc_dec = node
        if proc_dec is not None:
            self.visit(proc_dec)

    def visit_ParamList(self, node):
        _, param_dec_list = node
        if param_dec_list:
            self.visit(param_dec_list)

    def visit_ParamDecList(self, node):
        _, param, param_more = node
        self.visit(param)
        self.visit(param_more)

    def visit_Param(self, node):
        # 解析参数模式（值传递/引用传递）
        is_ref = False
        if node[0] == 'Param' and len(node) == 4:  # VAR TypeName FormList
            is_ref = True
            type_node = node[2]
            form_list = node[3]
        else:  # TypeName FormList
            type_node = node[1]
            form_list = node[2]
        
        # 解析类型并附加到子节点
        param_type = self._resolve_type(type_node)
        if param_type:
            # 将类型信息附加到FormList节点
            new_form_node = (form_list[0], form_list[1], form_list[2], param_type, is_ref)
            self.visit(new_form_node)


    def visit_ParamMore(self, node):
        _, param_dec = node
        if param_dec:
            self.visit(param_dec)

    def visit_FormList(self, node):
        # 从节点结构获取附加信息
        _, param_id, fid_more, param_type, is_ref = node

        param_name = param_id
        
        # 添加参数到符号表
        full_type = ("var " if is_ref else "") + str(param_type)
        name, length, offset = self.current_scope.add_symbol(param_name, full_type, category='param')
        if not name:
            self.error(f"参数 '{param_name}' 重复定义")
        else:
            self.emit_quad("get", offset, length, param_name)
        
        # 处理后续参数（传递附加信息）
        if fid_more and fid_more[1]:
            new_fid_node = (fid_more[0], fid_more[1], param_type, is_ref)
            self.visit(new_fid_node)

    def visit_FidMore(self, node):
        if len(node) > 2:  # 携带附加信息的节点
            _, form_list, param_type, is_ref = node
            new_form_node = (form_list[0], form_list[1], form_list[2], param_type, is_ref)
            self.visit(new_form_node)

    def visit_ProcDecPart(self, node):
        _, dec_part = node
        if dec_part:
            self.visit(dec_part)
    
    '''
    programbody IMP
    '''
    def visit_ProcBody(self, node):
        _, pro_body = node
        if pro_body:
            self.visit(pro_body)
    
    def visit_ProgramBody(self, node):
        _, stm_list = node  # 结构为 ('ProgramBody', StmList)
        self.visit(stm_list)

    def visit_StmList(self, node):
        _, stm, stm_more = node  # 结构为 ('StmList', Stm, StmMore)
        self.visit(stm)
        self.visit(stm_more)
    
    def visit_StmMore(self, node):
        if node[1] is not None:  # 结构为 ('StmMore', StmList)
            self.visit(node[1])
        
    def visit_Stm(self, node):
        if len(node) == 3:
            # 结构为 ('Stm', 'ID', AssCall)，例如 x := 10 或 proc(a, b)
            var_name = node[1]  # ID 名称
            ass_call_node = node[2]  # AssCall 节点
            self._handle_id_asscall(var_name, ass_call_node[1])
        else:
            self.visit(node[1])

    def _handle_id_asscall(self, var_name, ass_call_node):
        """处理 ID AssCall 结构（赋值或过程调用）"""
        if ass_call_node[0] == "AssignmentRest":
            self._handle_assignment(var_name, ass_call_node)
        elif ass_call_node[0] == "CallStmRest":
            self._handle_procedure_call(var_name, ass_call_node)
        else:
            self.error(f"未知的 AssCall 类型: {ass_call_node[0]}")

    def check_string_in_nested_tuple(self, data, target_string):
        if isinstance(data, str):
            return data == target_string
        elif isinstance(data, tuple):
            for item in data:
                if self.check_string_in_nested_tuple(item, target_string):
                    return True
        return False
    def _handle_assignment(self, var_name, assignment_node):
        _, var_more, exp = assignment_node
        curr_type, var_location = self._get_variable_value(("Variable", var_name, var_more))
        flag = self.check_string_in_nested_tuple(("Variable", var_name, var_more), "Exp")
        if flag:
            self.quadruples.pop()
        exp_type, exp_value = self._get_expression_value(exp)

        if curr_type != exp_type:
            self.error(f" 类型不匹配：无法将  {exp_type}  赋值给  {curr_type}")
        if flag:
            self.emit_quad(':=:', exp_value, None, var_location)
        else:
            self.emit_quad(':=', exp_value, None, var_location)

    def _handle_procedure_call(self, proc_name, call_node):
        _, act_param_list = call_node
        proc_info = self.current_scope.lookup(proc_name)
        #print(proc_info)
        if not proc_info or proc_info[2] != 'PROCEDURE':
            self.error(f" 过程  '{proc_name}'  未声明 ")
            return

        formal_params = self._get_formal_parameters(proc_name)
        actual_params = self._parse_act_param_list_for_quad(act_param_list)

        if len(formal_params) != len(actual_params):
            self.error(f" 参数数量不匹配：预期  {len(formal_params)} ，实际  {len(actual_params)}")
        else:
            for i, (formal, actual) in enumerate(zip(formal_params, actual_params)):
                # 这里需要考虑值传递和引用传递
                self.emit_quad('param', actual[1], None, None) # 传递参数值或地址

        self.emit_quad('call', proc_name, None, None)

    def _parse_act_param_list_for_quad(self, act_param_list_node):
        actual_params = []
        if act_param_list_node[1] is None:
            return actual_params

        current_node = act_param_list_node
        while current_node:
            Exp = current_node[1]
            More = current_node[2]
            param_type, param_value = self._get_expression_value(Exp)
            actual_params.append((param_type, param_value))
            current_node = More[1]
        return actual_params
    
    def _get_formal_parameters(self, proc_name):
        """从符号表中获取过程的形参列表"""
        proc = None
        proc = self.current_scope.lookup(proc_name)[0]
        if not proc:
            return []
        return proc.params

    def visit_ConditionalStm(self, node):
        _, rel_exp, stm_list1, stm_list2 = node
        #print(rel_exp, "i love you")
        rel_type, condition_result = self._get_expression_value(rel_exp)
        if rel_type != 'BOOLEAN':
            self.error(" 条件表达式必须为布尔值 ")
            return None

        self.emit_quad('THEN', condition_result, None, None)
        self.visit(stm_list1)
        self.emit_quad('ELSE', None, None, None)
        self.visit(stm_list2)
        self.emit_quad('ENDIF', None, None, None) # 生成 end 标签四元式

    def visit_LoopStm(self, node):
        _, rel_exp, stm_list = node

        self.emit_quad('WHILE', None, None, None)
        rel_type, condition_result = self._get_expression_value(rel_exp)
        if rel_type != 'BOOLEAN':
            self.error(" 循环条件必须是布尔类型 ")
            return
        self.emit_quad('DO', condition_result, None, None)
        self.visit(stm_list)
        self.emit_quad('ENDWHILE', None, None, None) # 生成循环结束标签四元式

    def visit_InputStm(self, node):
        _, invar = node  # 结构为 ('InputStm', Invar)
        var_name = invar[1]
        self.emit_quad('IN', var_name, None, None)
        if not self.current_scope.lookup(var_name):
            self.error(f"输入变量 '{var_name}' 未声明")

    def visit_OutputStm(self, node):
        _, exp = node  # 结构为 ('OutputStm', Exp)
        _, value = self._get_expression_value(exp)  # 仅检查表达式合法性
        self.emit_quad('OUT', value, None, None)

    def visit_ReturnStm(self, node):
        _, exp = node  # 结构为 ('ReturnStm', Exp)
        self._get_expression_value(exp)  # 根据需求检查返回类型
    
    # 在SemanticAnalyzer类中添加以下方法

    def visit_RelExp(self, node):
        _, exp, other_rel_e = node
        exp_type, value1 = self._get_expression_value(exp)
        cmp_op, cmp_exp = other_rel_e[1], other_rel_e[2]
        cmp_exp_type, value2 = self._get_expression_value(cmp_exp)

        if exp_type != cmp_exp_type:
            self.error(f" 比较操作类型不匹配 : {exp_type}  和  {cmp_exp_type}")
        result = self.generate_temp_var()
        self.emit_quad(cmp_op[1], value1, value2, result)
        return 'BOOLEAN', result # 返回类型和存储结果的临时变量

    def visit_Exp(self, node):
        _, term, other_term = node
        term_type, term_value = self._get_expression_value(term)

        if other_term[1] is None:
            return term_type, term_value

        add_op, exp = other_term[1], other_term[2]
        exp_type, exp_value = self._get_expression_value(exp)

        if term_type not in ['integer', 'char'] or exp_type not in ['integer', 'char']:
            self.error(f" 不支持的操作类型 : {term_type} {add_op} {exp_type}")
            if exp_type != term_type:
                self.error(" 操作类型不匹配 ")
            return None, None # 或者抛出异常
        '''
        if isinstance(term_value, int):
            tmp = self.generate_temp_var()
            self.emit_quad(':=', term_value, None, tmp)
            term_value = tmp
        if isinstance(exp_value, int):
            tmp = self.generate_temp_var()
            self.emit_quad(':=', exp_value, None, tmp)
            exp_value = tmp
        '''
        result = self.generate_temp_var()
        self.emit_quad(add_op[1], term_value, exp_value, result)
        return term_type, result
    
    def visit_Term(self, node):
        _, factor, other_factor = node
        factor_type, factor_value = self._get_expression_value(factor)

        if other_factor[1] is None:
            return factor_type, factor_value

        mult_op, term = other_factor[1], other_factor[2]
        term_type, term_value = self._get_expression_value(term)

        if factor_type not in ['integer', 'char'] or term_type not in ['integer', 'char']:
            self.error(f" 不支持的操作类型 : {factor_type} {mult_op} {term_type}")
            return None, None
        if factor_type != term_type:
            self.error(" 操作类型不匹配 ")
        result = self.generate_temp_var()
        self.emit_quad(mult_op[1], factor_value, term_value, result)
        return factor_type, result

    def visit_Factor(self, node):
        if isinstance(node[1], tuple):
            return self._get_expression_value(node[1])
        else:
            return "integer", node[1] # 返回类型和值
    def _get_variable_value(self, variable_node):
        _, var_id, var_more = variable_node
        # 查找变量基础类型
        var_info = self.current_scope.lookup(var_id)
        if not var_info:
            self.error(f"未定义的变量: {var_id}")
            return None
        base_type = var_info[0]
        # 处理数组下标或结构体访问
        current_type = base_type
        current_more = var_more
        
        while current_more and current_more[1] is not None:
            #print(var_id, current_more)
            if current_more[1][0] == 'Exp':  # 数组访问
                if not isinstance(current_type, ArrayType):
                    self.error(f"{var_id} 不是数组类型")
                    return None
                index_type, value = self._get_expression_value(current_more[1])
                if index_type != 'integer':
                    self.error("数组下标必须为整数")
                cons_pos = self.generate_temp_var()
                off_set = self.generate_temp_var()
                value_pos = self.generate_temp_var()
                self.emit_quad(":=", 4, None, cons_pos)
                self.emit_quad("*", value, cons_pos, off_set)
                self.emit_quad("[]", var_id, off_set, value_pos)
                self.emit_quad("load", value_pos, None, value_pos)
                var_id = value_pos
                current_type = current_type.element_type
                current_more = None
                
            else: 
                if not isinstance(current_type, RecType):
                    self.error(f"{var_id} 不是记录类型")
                    return None
                field_name = current_more[1][1]  # FieldVar的ID
                #print(current_type.fields)
                if field_name not in current_type.fields:
                    self.error(f"字段 {field_name} 不存在于记录中")
                    return None
                value_pos = self.generate_temp_var()
                self.emit_quad("[]", var_id, current_type.offset[field_name], value_pos)
                current_type = current_type.fields[field_name]
                var_id = value_pos
                current_more = current_more[1][2]
                print(current_more)
        
        return current_type, var_id

    def visit_CmpOp(self, node):
        return node[1]  # 返回操作符类型（LT/EQ）用于错误信息

    def visit_AddOp(self, node):
        return node[1]  # 返回操作符类型（PLUS/MINUS）

    def visit_MultOp(self, node):
        return node[1]  # 返回操作符类型（TIMES/OVER）

    def _get_expression_value(self, exp_node):
        """ 递归获取表达式的类型和值 """
        if isinstance(exp_node, tuple):
            if exp_node[0] == 'RelExp':
                return self.visit_RelExp(exp_node)
            elif exp_node[0] == 'Exp':
                return self.visit_Exp(exp_node)
            elif exp_node[0] == 'Term':
                return self.visit_Term(exp_node)
            elif exp_node[0] == 'Factor':
                return self.visit_Factor(exp_node)
            elif exp_node[0] == 'Variable':
                return self._get_variable_value(exp_node)
            elif exp_node[0] in ['INTC', 'ID']:
                return self.visit_Factor(('Factor', exp_node))
        return None, None

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