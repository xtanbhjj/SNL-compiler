import sys
sys.path.append("..")
from lexer import *
from Quad import *

class MIPSGenerator:
    def __init__(self, quadruples):
        self.quads = quadruples
        self.code = []
        self.label_count = 0
        self.reg_map = {}
        self.reg_pool = ['$t%d' % i for i in range(10)]  # 可用的临时寄存器
        self.param_regs = ['$a%d' % i for i in range(4)] # 参数寄存器
        self.current_proc = None
        self.stack_offset1 = {}
        self.stack_list = []
        self.stack_offset = 0 # 当前栈帧大小
        self.target_stack = []# 目标指令地址栈 (存储需要回填的跳转指令索引)
        self.label_stack = []
        self.size = 4 # 每个变量的大小
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
    
    def has_reg(self, var):
        return var in self.reg_map

    def free_reg(self, var):
        """释放寄存器"""
        if var in self.reg_map:
            reg = self.reg_map.pop(var)
            self.reg_pool.insert(0, reg)

    def emit(self, instruction):
        """添加指令到代码列表"""
        self.code.append(instruction)
        return len(self.code) - 1 # 返回指令的索引
    
    def get_offset(self, var):
        if var in self.stack_offset1:
            off = self.stack_offset1.get(var, 0) 
            if isinstance(off, tuple):
                return off[0]
            else:
                return off
        else:
            offset = self.stack_offset1['size'] + 8
            for i in range(len(self.stack_list)-1, -1, -1):
                if var in self.stack_list[i]:
                    off = self.stack_list[i].get(var, 0)
                    if isinstance(off, tuple):
                        return offset + off[0]
                    else:
                        return offset + off
                else:
                    offset += self.stack_list[i]['size'] + 8
    
    def is_var(self, var):
        if var in self.stack_offset1:
            if isinstance(self.stack_offset1[var], tuple):
                return self.stack_offset1[var]
            else:
                return True
        else:
            for i in range(len(self.stack_list)-1, -1, -1):
                if var in self.stack_list[i]:
                    return self.stack_list[i].get(var, 0)
            return False

    def generate(self):
        self.code.append(".data")
        # global var but not necessary
        # for quad in self.quads:
        #     if quad.operator == ''
        self.code.append("newline: .asciiz \"\\n\"")
        self.code.append(".text")
        self.code.append(".globl main")  # 声明main函数为全局
        self.code.append("main:")
        # not defined whether to li $sp 0x7FFFF...
        self.emit("li $sp, 0x7FFFFFFC")
        pq = self._resolve_sp(0)
        jk = 0
        for idx in range(pq, len(self.quads)):
            if idx < jk:
                continue
            op, arg1, arg2, res = self.quads[idx].operator, self.quads[idx].operand1, self.quads[idx].operand2, self.quads[idx].result
            if self.quads[idx].operator == 'PROCEDURE':
                self._gen_procedure(op, arg1, arg2, res)
                num = res
                self._resolve_sp(idx + 1)
                idx += 1
                for i in range(num):
                    op, arg1, arg2, res = self.quads[idx].operator, self.quads[idx].operand1, self.quads[idx].operand2, self.quads[idx].result
                    off_set = self.get_offset(res)
                    self.emit(f'sw $a{i}, {off_set}($sp)')
                    idx += 1
                while(self.quads[idx].operator == 'DECLARE'):
                    idx += 1
                jk = idx
                #print(idx, "duhaonjsdhyagwid")
            elif self.quads[idx].operator == 'param':
                num = 0
                while self.quads[idx].operator == 'param':
                    if not self.quads[idx].result:
                        #print("--------", self.quads[idx].operand1)
                        arg_reg = self.get_regs(self.quads[idx].operand1)
                        self.emit(f'move $a{num}, {arg_reg}')
                        self.free_regs(self.quads[idx].operand1, arg_reg)
                    else:
                        offset = self.get_offset(self.quads[idx].operand1)
                        self.emit(f'li $v0, {offset}')
                        self.emit(f'add $v0, $sp, $v0')
                        self.emit(f'move $a{num}, $v0')
                    num += 1
                    idx += 1
                jk = idx
            else:
                self._gen_instruction(op, arg1, arg2, res)

        # 结束程序
        self.code.append("li $v0, 10")
        self.code.append("syscall")
        mips_code = '\n'.join(self.code) 
        with open("../result/target.mips", "w") as f:
            for line in mips_code:
                f.write(line)
        return mips_code

    def _resolve_sp(self, idx):
        self.stack_offset = 0
        while self.quads[idx].operator in ('DECLARE', 'get'):
            if self.quads[idx].operator == 'get' and self.quads[idx].operand1:
                self.stack_offset1[self.quads[idx].result] = (self.stack_offset, True)
            else:
                self.stack_offset1[self.quads[idx].result] = self.stack_offset 
            self.stack_offset += self.quads[idx].operand2 * self.size
            idx += 1
        self.stack_offset1["size"] = self.stack_offset
        self.code.append(f"addi $sp, $sp, -{self.stack_offset}")
        return idx

    def get_regs(self, operator):
        reg = self.get_reg(operator)
        flag = self.is_var(operator)
        #print(flag, operator)
        if isinstance(flag, tuple):
            offset = flag[0]
            self.emit(f"lw $v0, {offset}($sp)")
            self.emit(f"lw {reg}, 0($v0)")
        elif flag:
            offset = self.get_offset(operator)
            self.emit(f"lw {reg}, {offset}($sp)")
        return reg
    
    def free_regs(self, operator, reg):
        flag = self.is_var(operator)
        if isinstance(flag, tuple):
            offset = flag[0]
            self.emit(f"lw $v0, {offset}($sp)")
            self.emit(f"sw {reg}, 0($v0)")
            self.free_reg(operator)
        elif flag:
            offset = self.get_offset(operator)
            self.emit(f"sw {reg}, {offset}($sp)")
            self.free_reg(operator)
        else:
            self.free_reg(operator)

    def _gen_instruction(self, op, arg1, arg2, res):
        handler = {
            ':=': self._gen_assign,
            '+': self._gen_add,
            '-': self._gen_sub,
            '*': self._gen_mul,
            '/': self._gen_div,
            '<': self._gen_lt,
            '=': self._gen_eq,
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
            'load': self._gen_load,
            ':=:': self._addr_assign,
            '[]': self._gen_address,
            'label': self._gen_label,
            'Go': self._gen_goto
        }.get(op, self._gen_unknown)
        handler(op, arg1, arg2, res)

    def _gen_label(self, op, label, _, __):
        self.emit(f'{label}:')

    def _gen_goto(self, op, label, _, __):
        self.emit(f'j {label}')

    def _gen_load(self, op, addr, _, dest):
        dest_reg = self.get_regs(dest)
        self.emit(f'add {dest_reg}, {dest_reg}, $sp')
        self.emit(f"lw {dest_reg}, 0({dest_reg})")

    def _addr_assign(self, op, src, _, dest):
        dest_reg = self.get_regs(dest)
        self.emit(f'add {dest_reg}, {dest_reg}, $sp')
        if isinstance(src, int):
            self.emit(f"li $v0, {src}") 
            self.emit(f"sw $v0, 0({dest_reg})")
        else: 
            src_reg = self.get_regs(src)
            self.emit(f"sw {src_reg}, 0({dest_reg})")
            self.free_regs(src, src_reg)
        self.free_regs(dest, dest_reg) 

    def _gen_address(self, op, addr, src, dest):
        dest_reg = self.get_regs(dest)
        src_reg = self.get_regs(src)
        
        if self.has_reg(addr):
            self.emit(f'add, {dest_reg}, {src_reg}, {self.get_reg(addr)}')
        else:
            offset = self.get_offset(addr)
            self.emit(f'addi {dest_reg}, {src_reg}, {offset}')
        self.free_regs(src, src_reg)

    def _gen_assign(self, op, src, _, dest):
        dest_reg = self.get_regs(dest)
        if isinstance(src, int):  # 如果是数字，则直接加载到寄存器中
            self.emit(f"li {dest_reg}, {src}")
        else: 
            src_reg = self.get_regs(src)
            self.emit(f"move {dest_reg}, {src_reg}")
            self.free_regs(src, src_reg)

        if dest in self.stack_offset1:
            self.free_regs(dest, dest_reg)

    def _gen_lt(self, op, a, b, res):
        res_reg = self.get_regs(res)
        a_reg = self.get_regs(a)
        if isinstance(b, int):
            self.emit(f"slti {res_reg}, {a_reg}, {b}")
        else:
            b_reg = self.get_regs(b)
            self.emit(f"slt {res_reg}, {a_reg}, {b_reg}")
            self.free_regs(b, b_reg)
        self.free_regs(a, a_reg)

    def _gen_eq(self, op, a, b, res):
        res_reg = self.get_regs(res)
        a_reg = self.get_regs(a)
        b_reg = self.get_regs(b)
        self.emit(f"sub {res_reg}, {a_reg}, {b_reg}")
        self.emit(f"slti {res_reg}, {res_reg}, 1")
        self.free_regs(a, a_reg)
        self.free_regs(b, b_reg)

    def _gen_add(self, op, a, b, res):
        res_reg = self.get_regs(res)
        a_reg = self.get_regs(a)
        if isinstance(b, int):
            self.emit(f"addi {res_reg}, {a_reg}, {b}")
        else:
            b_reg = self.get_regs(b)
            self.emit(f"add {res_reg}, {a_reg}, {b_reg}")
            self.free_regs(b, b_reg)
        self.free_regs(a, a_reg)

    def _gen_sub(self, op, a, b, res):
        res_reg = self.get_regs(res)
        a_reg = self.get_regs(a)
        if isinstance(b, int):
            self.emit(f"addi {res_reg}, {a_reg}, -{b}")
        else:
            b_reg = self.get_regs(b)
            self.emit(f"sub {res_reg}, {a_reg}, {b_reg}")
            self.free_regs(b, b_reg)
        self.free_regs(a, a_reg)

    def _gen_mul(self, op, a, b, res):
        res_reg = self.get_regs(res)
        a_reg = self.get_regs(a)
        b_reg = self.get_regs(b)
        self.emit(f"mul {res_reg}, {a_reg}, {b_reg}")
        self.free_regs(a, a_reg)
        self.free_regs(b, b_reg)

    def _gen_div(self, op, a, b, res):
        res_reg = self.get_regs(res)
        a_reg = self.get_regs(a)
        b_reg = self.get_regs(b)
        self.emit(f"div {a_reg}, {b_reg}")
        self.emit(f"mflo {res_reg}")
        self.free_regs(a, a_reg)
        self.free_regs(b, b_reg)

    def _gen_then(self, op, cond, _, __):
        cond_reg = self.get_reg(cond)
        jump_index = self.emit(f"beqz {cond_reg}, else_label")
        self.emit("nop")
        self.target_stack.append((jump_index, "else_label"))

    def _gen_else(self, op, _, __, ___):
        jump_index = self.emit(f"j endif_label")
        self.emit("nop")
        # 回填 THEN 语句的跳转目标
        if self.target_stack:
            then_jump_index, then_label = self.target_stack.pop()
            self.code[then_jump_index] = self.code[then_jump_index].replace(then_label, f"label{self.label_count}")
            #self.label_definitions[f"label{self.label_count}"] = len(self.code)
            self.emit(f"label{self.label_count}:")
            self.label_count += 1
        else:
            raise RuntimeError(f"找不到与 ELSE 对应的 THEN 标签:")
                # 将需要回填的跳转指令索引和目标标号压入栈
        self.target_stack.append((jump_index, 'endif_label'))

    def _gen_endif(self, op, ___, _, __):
        if self.target_stack:
            #print(self.target_stack)
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
        jump_index = self.emit(f"beqz {cond_reg}, endwh")
        self.emit("nop")
        self.target_stack.append((jump_index, "endwh"))

    def _gen_endwhile(self, op, __, _, ___):
        start_label = self.label_stack.pop()
        self.emit(f"j {start_label}")
        self.emit("nop")
        if self.target_stack:
            do_jump_index, do_label = self.target_stack.pop()
            self.code[do_jump_index] = self.code[do_jump_index].replace(do_label, f"label{self.label_count}")
        else:
            raise RuntimeError(f"找不到与 ENDWHILE 对应的 DO 标签:")
        self.emit(f"label{self.label_count}:")
        self.label_count += 1

    def _gen_input(self, op, var, _, __):
        self.emit("li $v0, 5")
        self.emit("syscall")
        reg = self.get_regs(var)
        self.emit(f"move {reg}, $v0")
        self.free_regs(var, reg)

    def _gen_output(self, op, val, _, __):
        reg = self.get_regs(val)
        self.emit("li $v0, 1")
        self.emit(f"move $a0, {reg}")
        self.emit("syscall")
        # 打印换行
        self.emit("li $v0, 4")
        self.emit("la $a0, newline")
        self.emit("syscall")

    def _gen_procedure(self, op, name, _, num):
        self.stack_list.append(self.stack_offset1)
        self.stack_offset1 = {}
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
        #print(self.stack_offset1)
        self.stack_offset1 = self.stack_list.pop()
        #print(self.stack_offset1)
        self.current_proc = None

    def _gen_call(self, op, proc, _, __):
        self.emit(f"jal {proc}")
        # 参数寄存器在被调用函数中处理，这里不需要重置

    def _gen_unknown(self, op, *args):
        raise RuntimeError(f"未知操作符: {op}, 参数: {args}")

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
    parse_tree = parser.parse_file("../data/demo.txt")
    print(parse_tree)

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
