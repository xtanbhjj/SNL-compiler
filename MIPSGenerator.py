from lexer import *
from Quad import *

'''
class MIPSGenerator:
    def __init__(self, quadruples):
        self.quads = quadruples
        self.code = []
        self.label_count = 0
        self.reg_map = {}        
        self.reg_pool = ['$t%d' % i for i in range(10)]  # 可用的临时寄存器
        self.param_regs = ['$a%d' % i for i in range(4)] # 参数寄存器
        self.current_proc = None
        self.stack_offset = 0     
        self.label_map = {}      

    def get_reg(self, var):
        """分配寄存器，优先复用已分配的"""
        if var in self.reg_map:
            return self.reg_map[var]
        if not self.reg_pool:
            self._handle_register_overflow()  # 处理寄存器溢出
        reg = self.reg_pool.pop(0)
        self.reg_map[var] = reg
        return reg

    def free_reg(self, var):
        """释放寄存器"""
        if var in self.reg_map:
            reg = self.reg_map.pop(var)
            self.reg_pool.insert(0, reg)

    def new_label(self):
        self.label_count += 1
        return "label%d" % self.label_count

    def generate(self):
        self.code.append(".data")
        self.code.append("newline: .asciiz \"\\n\"")
        self.code.append(".text")
        self.code.append(".globl main")  # 声明main函数为全局
        self.code.append("main:")

        for quad in self.quads:
            op, arg1, arg2, res = quad.operator, quad.operand1, quad.operand2, quad.result
            self._gen_instruction(op, arg1, arg2, res)

        # 结束程序
        self.code.append("li $v0, 10")
        self.code.append("syscall")
        return '\n'.join(self.code)

    def _gen_instruction(self, op, arg1, arg2, res):
        handler = {
            ':=': self._gen_assign,
            '+': self._gen_add,
            '-': self._gen_sub,
            '*': self._gen_mul,
            '/': self._gen_div,
            'THEN': self._gen_then,
            'ELSE': self._gen_else,
            'ENDIF': self._gen_endif,
            'WHILE': self._gen_while,
            'DO': self._gen_do,
            'ENDWHILE': self._gen_endwhile,
            'IN': self._gen_input,
            '<': self._gen_lt,
            'OUT': self._gen_output,
            'PROCEDURE': self._gen_procedure,
            'ENDPROCEDURE': self._gen_endprocedure,
            'call': self._gen_call,
            'param': self._gen_param,
            '[]': self._gen_add
        }.get(op, self._gen_unknown)
        handler(op, arg1, arg2, res)

    def _gen_assign(self, op, src, _, dest):
        dest_reg = self.get_reg(dest)
        if isinstance(src, int):  # 立即数
            self.code.append(f"li {dest_reg}, {src}")
        else:  # 变量到变量
            src_reg = self.get_reg(src)
            self.code.append(f"move {dest_reg}, {src_reg}")
        self.free_reg(src)

    def _gen_lt(self, op, a, b, res):
        res_reg = self.get_reg(res)
        a_reg = self.get_reg(a)
        if isinstance(b, int):
            self.code.append(f"slti {res_reg}, {a_reg}, {b}")
        else:
            b_reg = self.get_reg(b)
            self.code.append(f"slt {res_reg}, {a_reg}, {b_reg}")
            self.free_reg(b)
        self.free_reg(a)

    def _gen_add(self, op, a, b, res):
        res_reg = self.get_reg(res)
        a_reg = self.get_reg(a)
        if isinstance(b, int):
            self.code.append(f"addi {res_reg}, {a_reg}, {b}")
        else:
            b_reg = self.get_reg(b)
            self.code.append(f"add {res_reg}, {a_reg}, {b_reg}")
        self.free_reg(a)
        self.free_reg(b)

    def _gen_sub(self, op, a, b, res):
        res_reg = self.get_reg(res)
        a_reg = self.get_reg(a)
        if isinstance(b, int):
            self.code.append(f"addi {res_reg}, {a_reg}, -{b}")
        else:
            b_reg = self.get_reg(b)
            self.code.append(f"sub {res_reg}, {a_reg}, {b_reg}")
        self.free_reg(a)
        self.free_reg(b)

    def _gen_mul(self, op, a, b, res):
        res_reg = self.get_reg(res)
        a_reg = self.get_reg(a)
        b_reg = self.get_reg(b)
        self.code.append(f"mul {res_reg}, {a_reg}, {b_reg}")
        self.free_reg(a)
        self.free_reg(b)

    def _gen_div(self, op, a, b, res):
        res_reg = self.get_reg(res)
        a_reg = self.get_reg(a)
        b_reg = self.get_reg(b)
        self.code.append(f"div {a_reg}, {b_reg}")
        self.code.append(f"mflo {res_reg}")
        self.free_reg(a)
        self.free_reg(b)

    def _gen_then(self, op, cond, _, label):
        cond_reg = self.get_reg(cond)
        else_label = self.new_label()
        self.label_map[label] = self.new_label() # ENDIF label
        self.code.append(f"beqz {cond_reg}, {else_label}")
        self.code.append(f"nop")
        self.code.append((else_label, 'else_label')) # 标记 else 标签位置

    def _gen_else(self, op, _, __, label):
        endif_label = self.label_map.get(label)
        if endif_label:
            self.code.append(f"j {endif_label}")
            self.code.append(f"nop")
            # 回填 ELSE 标签
            for i in range(len(self.code)):
                if isinstance(self.code[i], tuple) and self.code[i][1] == 'else_label':
                    self.code[i] = f"{self.code[i][0]}:"
                    break
        else:
            raise RuntimeError(f"找不到与 ELSE 对应的 ENDIF 标签: {label}")

    def _gen_endif(self, op, label, _, __):
        endif_label = self.label_map.get(label)
        if endif_label:
            self.code.append(f"{endif_label}:")
        else:
            raise RuntimeError(f"找不到 ENDIF 标签: {label}")
        if label in self.label_map:
            del self.label_map[label]

    def _gen_while(self, op, _, __, label):
        loop_start = self.new_label()
        self.label_map[label] = loop_start
        self.code.append(f"{loop_start}:")

    def _gen_do(self, op, cond, _, label):
        cond_reg = self.get_reg(cond)
        end_label = self.new_label()
        self.label_map[label] = end_label
        self.code.append(f"beqz {cond_reg}, {end_label}")
        self.code.append(f"nop")

    def _gen_endwhile(self, op, label_start, _, label_end):
        start_label = self.label_map.get(label_start)
        end_label = self.label_map.get(label_end)
        if start_label and end_label:
            self.code.append(f"j {start_label}")
            self.code.append(f"nop")
            self.code.append(f"{end_label}:")
            del self.label_map[label_start]
            del self.label_map[label_end]
        else:
            raise RuntimeError(f"找不到 WHILE 或 DO 对应的标签: start={label_start}, end={label_end}")

    def _gen_input(self, op, var, _, __):
        self.code.append("li $v0, 5")
        self.code.append("syscall")
        reg = self.get_reg(var)
        self.code.append(f"move {reg}, $v0")

    def _gen_output(self, op, val, _, __):
        reg = self.get_reg(val)
        self.code.append("li $v0, 1")
        self.code.append(f"move $a0, {reg}")
        self.code.append("syscall")
        # 打印换行
        self.code.append("li $v0, 4")
        self.code.append("la $a0, newline")
        self.code.append("syscall")

    def _gen_procedure(self, op, name, _, __):
        self.code.append(f"{name}:")
        self.current_proc = name
        self.stack_offset = 0
        # 保存返回地址和帧指针
        self.code.append("subu $sp, $sp, 8")
        self.code.append("sw $ra, 4($sp)")
        self.code.append("sw $fp, 0($sp)")
        self.code.append("move $fp, $sp")

    def _gen_endprocedure(self, op, _, __, ___):
        # 恢复帧指针和返回地址
        self.code.append("move $sp, $fp")
        self.code.append("lw $fp, 0($sp)")
        self.code.append("lw $ra, 4($sp)")
        self.code.append("addu $sp, $sp, 8")
        self.code.append("jr $ra")
        self.current_proc = None

    def _gen_param(self, op, arg, _, __):
        # 简单实现：将参数放入栈上
        self.stack_offset -= 4
        arg_reg = self.get_reg(arg)
        self.code.append(f"sw {arg_reg}, {self.stack_offset}($fp)")
        self.free_reg(arg) # 参数用完可以释放寄存器

    def _gen_call(self, op, proc, _, __):
        self.code.append(f"jal {proc}")
        # 参数寄存器在被调用函数中处理，这里不需要重置

    def _gen_unknown(self, op, *args):
        raise RuntimeError(f"未知操作符: {op}")

    def _handle_register_overflow(self):
        """处理寄存器溢出 (简单实现，实际需要更完善的策略)"""
        if not self.reg_map:
            raise RuntimeError("寄存器严重不足")
        var, reg = self.reg_map.popitem()
        self.reg_pool.insert(0, reg)
        # 这里需要将寄存器的值写回内存，但没有栈帧管理，暂时省略
        print(f"警告: 寄存器溢出，变量 '{var}' 的值可能丢失。需要实现栈帧管理。")
'''

from lexer import *
from Quad import *

class MIPSGenerator:
    def __init__(self, quadruples):
        self.quads = quadruples
        self.code = []
        self.label_count = 0
        self.reg_map = {}
        self.reg_pool = ['$t%d' % i for i in range(20)]  # 可用的临时寄存器
        self.param_regs = ['$a%d' % i for i in range(4)] # 参数寄存器
        self.current_proc = None
        self.stack_offset = 0
        self.target_stack = []# 目标指令地址栈 (存储需要回填的跳转指令索引)
        self.label_stack = []
        #self.label_definitions = {} # 存储标号定义的位置 (标号: 指令索引)

    def get_reg(self, var):
        """分配寄存器，优先复用已分配的"""
        if var in self.reg_map:
            return self.reg_map[var]
        if not self.reg_pool:
            self._handle_register_overflow()  # 处理寄存器溢出
        reg = self.reg_pool.pop(0)
        self.reg_map[var] = reg
        return reg

    def free_reg(self, var):
        """释放寄存器"""
        if var in self.reg_map:
            reg = self.reg_map.pop(var)
            self.reg_pool.insert(0, reg)



    def emit(self, instruction):
        """添加指令到代码列表"""
        self.code.append(instruction)
        return len(self.code) - 1 # 返回指令的索引

    def generate(self):
        self.code.append(".data")
        self.code.append("newline: .asciiz \"\\n\"")
        self.code.append(".text")
        self.code.append(".globl main")  # 声明main函数为全局
        self.code.append("main:")

        for quad in self.quads:
            op, arg1, arg2, res = quad.operator, quad.operand1, quad.operand2, quad.result
            self._gen_instruction(op, arg1, arg2, res)

        # 结束程序
        self.code.append("li $v0, 10")
        self.code.append("syscall")
        return '\n'.join(self.code)

    def _gen_instruction(self, op, arg1, arg2, res):
        handler = {
            ':=': self._gen_assign,
            '+': self._gen_add,
            '-': self._gen_sub,
            '*': self._gen_mul,
            '/': self._gen_div,
            '<': self._gen_lt,
            'THEN': self._gen_then,
            'ELSE': self._gen_else,
            'ENDIF': self._gen_endif,
            'WHILE': self._gen_while,
            'DO': self._gen_do,
            'ENDWHILE': self._gen_endwhile,
            'IN': self._gen_input,
            'OUT': self._gen_output,
            'PROCEDURE': self._gen_procedure,
            'ENDPROCEDURE': self._gen_endprocedure,
            'call': self._gen_call,
            'param': self._gen_param,
            '[]': self._gen_add
        }.get(op, self._gen_unknown)
        handler(op, arg1, arg2, res)

    def _gen_assign(self, op, src, _, dest):
        dest_reg = self.get_reg(dest)
        if isinstance(src, int):  # 立即数
            self.emit(f"li {dest_reg}, {src}")
        else:  # 变量到变量
            src_reg = self.get_reg(src)
            self.emit(f"move {dest_reg}, {src_reg}")
        self.free_reg(src)

    def _gen_lt(self, op, a, b, res):
        """生成小于比较的 MIPS 代码"""
        res_reg = self.get_reg(res)
        a_reg = self.get_reg(a)
        if isinstance(b, int):
            self.emit(f"slti {res_reg}, {a_reg}, {b}")
        else:
            b_reg = self.get_reg(b)
            self.emit(f"slt {res_reg}, {a_reg}, {b_reg}")
            self.free_reg(b)
        self.free_reg(a)

    def _gen_add(self, op, a, b, res):
        res_reg = self.get_reg(res)
        a_reg = self.get_reg(a)
        if isinstance(b, int):
            self.emit(f"addi {res_reg}, {a_reg}, {b}")
        else:
            b_reg = self.get_reg(b)
            self.emit(f"add {res_reg}, {a_reg}, {b_reg}")
        self.free_reg(a)
        self.free_reg(b)

    def _gen_sub(self, op, a, b, res):
        res_reg = self.get_reg(res)
        a_reg = self.get_reg(a)
        if isinstance(b, int):
            self.emit(f"addi {res_reg}, {a_reg}, -{b}")
        else:
            b_reg = self.get_reg(b)
            self.emit(f"sub {res_reg}, {a_reg}, {b_reg}")
        self.free_reg(a)
        self.free_reg(b)

    def _gen_mul(self, op, a, b, res):
        res_reg = self.get_reg(res)
        a_reg = self.get_reg(a)
        b_reg = self.get_reg(b)
        self.emit(f"mul {res_reg}, {a_reg}, {b_reg}")
        self.free_reg(a)
        self.free_reg(b)

    def _gen_div(self, op, a, b, res):
        res_reg = self.get_reg(res)
        a_reg = self.get_reg(a)
        b_reg = self.get_reg(b)
        self.emit(f"div {a_reg}, {b_reg}")
        self.emit(f"mflo {res_reg}")
        self.free_reg(a)
        self.free_reg(b)

    def _gen_then(self, op, cond, _, __):
        cond_reg = self.get_reg(cond)
        # 生成条件跳转指令，目标地址暂时留空
        jump_index = self.emit(f"beqz {cond_reg}, else_label")
        self.emit("nop")
        # 将需要回填的跳转指令索引和目标标号压入栈
        self.target_stack.append((jump_index, "else_label"))

    def _gen_else(self, op, _, __, ___):
        jump_index = self.emit(f"j endif_label")
        self.emit("nop")
        # 将需要回填的跳转指令索引和目标标号压入栈
        self.target_stack.append((jump_index, 'endif_label'))
        # 回填 THEN 语句的跳转目标
        if self.target_stack:
            then_jump_index, then_label = self.target_stack.pop()
            self.code[then_jump_index] = self.code[then_jump_index].replace(then_label, f"label{self.label_count}")
            #self.label_definitions[f"label{self.label_count}"] = len(self.code)
            self.emit(f"label{self.label_count}:")
            self.label_count += 1
        else:
            raise RuntimeError(f"找不到与 ELSE 对应的 THEN 标签:")

    def _gen_endif(self, op, ___, _, __):
        if self.target_stack:
            print(self.target_stack)
            else_jump_index, else_label = self.target_stack.pop()
            self.code[else_jump_index] = self.code[else_jump_index].replace(else_label, f"label{self.label_count}")
        else:
            raise RuntimeError(f"找不到与 ENDIF 对应的 THEN 或 ELSE 标签:")
        # 定义 ENDIF 标号的位置
        #self.label_definitions[f"label{self.label_count}"] = len(self.code)
        self.emit(f"label{self.label_count}:")
        self.label_count += 1

    def _gen_while(self, op, _, __, ___):
        # 定义循环开始的标号
        #self.label_definitions[f"label{self.label_count}"] = len(self.code)
        self.emit(f"label{self.label_count}:")
        self.label_count += 1
        self.label_stack.append(f"label{self.label_count - 1}")

    def _gen_do(self, op, cond, _, __):
        cond_reg = self.get_reg(cond)
        # 生成条件跳转指令，目标地址暂时留空
        jump_index = self.emit(f"beqz {cond_reg}, endwh")
        self.emit("nop")
        # 将需要回填的跳转指令索引和目标标号压入栈
        self.target_stack.append((jump_index, "endwh"))

    def _gen_endwhile(self, op, __, _, ___):
        start_label = self.label_stack.pop()
        self.emit(f"j {start_label}")
        self.emit("nop")
        # 回填 DO 语句的跳转目标
        if self.target_stack:
            do_jump_index, do_label = self.target_stack.pop()
            self.code[do_jump_index] = self.code[do_jump_index].replace(do_label, f"label{self.label_count}")
        else:
            raise RuntimeError(f"找不到与 ENDWHILE 对应的 DO 标签:")
        # 定义循环结束的标号
        self.emit(f"label{self.label_count}:")
        self.label_count += 1

    def _gen_input(self, op, var, _, __):
        self.emit("li $v0, 5")
        self.emit("syscall")
        reg = self.get_reg(var)
        self.emit(f"move {reg}, $v0")

    def _gen_output(self, op, val, _, __):
        reg = self.get_reg(val)
        self.emit("li $v0, 1")
        self.emit(f"move $a0, {reg}")
        self.emit("syscall")
        # 打印换行
        self.emit("li $v0, 4")
        self.emit("la $a0, newline")
        self.emit("syscall")

    def _gen_procedure(self, op, name, _, __):
        self.emit(f"{name}:")
        self.current_proc = name
        self.stack_offset = 0
        # 保存返回地址和帧指针
        self.emit("subu $sp, $sp, 8")
        self.emit("sw $ra, 4($sp)")
        self.emit("sw $fp, 0($sp)")
        self.emit("move $fp, $sp")

    def _gen_endprocedure(self, op, _, __, ___):
        # 恢复帧指针和返回地址
        self.emit("move $sp, $fp")
        self.emit("lw $fp, 0($sp)")
        self.emit("lw $ra, 4($sp)")
        self.emit("addu $sp, $sp, 8")
        self.emit("jr $ra")
        self.current_proc = None

    def _gen_param(self, op, arg, _, __):
        # 简单实现：将参数放入栈上
        self.stack_offset -= 4
        arg_reg = self.get_reg(arg)
        self.emit(f"sw {arg_reg}, {self.stack_offset}($fp)")
        self.free_reg(arg) # 参数用完可以释放寄存器

    def _gen_call(self, op, proc, _, __):
        self.emit(f"jal {proc}")
        # 参数寄存器在被调用函数中处理，这里不需要重置

    def _gen_unknown(self, op, *args):
        raise RuntimeError(f"未知操作符: {op}")

    def _handle_register_overflow(self):
        """处理寄存器溢出 (简单实现，实际需要更完善的策略)"""
        if not self.reg_map:
            raise RuntimeError("寄存器严重不足")
        var, reg = self.reg_map.popitem()
        self.reg_pool.insert(0, reg)
        # 这里需要将寄存器的值写回内存，但没有栈帧管理，暂时省略
        print(f"警告: 寄存器溢出，变量 '{var}' 的值可能丢失。需要实现栈帧管理。")


if __name__ == '__main__':
    parser = SNLParser()
    parse_tree = parser.parse_file("./data/demo.txt")

    if parse_tree:
        print("\n语法分析成功！")
        semantic_analyzer = SemanticAnalyzer()
        semantic_analyzer.analyze(parse_tree)
        print("\n语义分析完成！")
        mips_gen = MIPSGenerator(semantic_analyzer.quadruples)
        mips_code = mips_gen.generate()
        print(mips_code)
    else:
        print("\n语法分析失败！")
