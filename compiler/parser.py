import sys
sys.path.append("../")
from ply import yacc
from lexer import SNLLexer
from graphviz import Digraph

class SNLParser:
    tokens = SNLLexer().tokens  # 继承词法分析器定义的 tokens

    def __init__(self):
        self.lexer = SNLLexer()
        self.parser = yacc.yacc(module=self)
        self.parse_tree = None

    # Program ::= ProgramHead DeclarePart ProgramBody DOT
    def p_Program(self, p):
        '''Program : ProgramHead DeclarePart ProgramBody DOT'''
        p[0] = ('Program', p[1], p[2], p[3])

    # ProgramHead ::= PROGRAM ProgramName
    def p_ProgramHead(self, p):
        '''ProgramHead : PROGRAM ProgramName'''
        p[0] = ('ProgramHead', p[2])

    # ProgramName ::= ID
    def p_ProgramName(self, p):
        '''ProgramName : ID'''
        p[0] = ('ProgramName', p[1])

    # DeclarePart ::= TypeDec VarDec ProcDec
    def p_DeclarePart(self, p):
        '''DeclarePart : TypeDec VarDec ProcDec'''
        p[0] = ('DeclarePart', p[1], p[2], p[3])

    # TypeDec ::= epsilon | TypeDeclaration
    def p_TypeDec_empty(self, p):
        '''TypeDec : '''
        p[0] = ('TypeDec', None)

    def p_TypeDec_declaration(self, p):
        '''TypeDec : TypeDeclaration'''
        p[0] = ('TypeDec', p[1])

    # TypeDeclaration ::= TYPE TypeDecList
    def p_TypeDeclaration(self, p):
        '''TypeDeclaration : TYPE TypeDecList'''
        p[0] = ('TypeDeclaration', p[2])

    # TypeDecList ::= TypeId EQ TypeName SEMI TypeDecMore
    def p_TypeDecList(self, p):
        '''TypeDecList : TypeId EQ TypeName SEMI TypeDecMore'''
        p[0] = ('TypeDecList', p[1], p[3], p[5])

    # TypeDecMore ::= epsilon | TypeDecList
    def p_TypeDecMore_empty(self, p):
        '''TypeDecMore : '''
        p[0] = ('TypeDecMore', None)

    def p_TypeDecMore_list(self, p):
        '''TypeDecMore : TypeDecList'''
        p[0] = ('TypeDecMore', p[1])

    # TypeId ::= ID
    def p_TypeId(self, p):
        '''TypeId : ID'''
        p[0] = ('TypeId', p[1])

    # TypeName ::= BaseType | StructureType | ID
    def p_TypeName_base(self, p):
        '''TypeName : BaseType'''
        p[0] = ('TypeName', p[1])

    def p_TypeName_structure(self, p):
        '''TypeName : StructureType'''
        p[0] = ('TypeName', p[1])
    
    def p_TypeName_id(self, p):
        '''TypeName : ID'''
        p[0] = ('TypeName', p[1])

    # BaseType ::= INTEGER | CHAR
    def p_BaseType(self, p):
        '''BaseType : INTEGER
                    | CHAR'''
        p[0] = ('BaseType', p[1])

    # StructureType ::= ArrayType | RecType
    def p_StructureType(self, p):
        '''StructureType : ArrayType
                         | RecType'''
        p[0] = ('StructureType', p[1])

    # ArrayType ::= ARRAY LMIDPAREN INTC UNDERANGE INTC RMIDPAREN OF BaseType
    def p_ArrayType(self, p):
        '''ArrayType : ARRAY LMIDPAREN INTC UNDERANGE INTC RMIDPAREN OF BaseType'''
        p[0] = ('ArrayType', p[3], p[5], p[8])

    # RecType ::= RECORD FieldDecList END
    def p_RecType(self, p):
        '''RecType : RECORD FieldDecList END'''
        p[0] = ('RecType', p[2])

    # FieldDecList ::= BaseType IdList SEMI FieldDecMore | ArrayType IdList SEMI FieldDecMore
    def p_FieldDecList_base(self, p):
        '''FieldDecList : BaseType IdList SEMI FieldDecMore'''
        p[0] = ('FieldDecList', p[1], p[2], p[4])

    def p_FieldDecList_array(self, p):
        '''FieldDecList : ArrayType IdList SEMI FieldDecMore'''
        p[0] = ('FieldDecList', p[1], p[2], p[4])

    # FieldDecMore ::= epsilon | FieldDecList
    def p_FieldDecMore_empty(self, p):
        '''FieldDecMore : '''
        p[0] = ('FieldDecMore', None)

    def p_FieldDecMore_list(self, p):
        '''FieldDecMore : FieldDecList'''
        p[0] = ('FieldDecMore', p[1])

    # IdList ::= ID IdMore
    def p_IdList(self, p):
        '''IdList : ID IdMore'''
        p[0] = ('IdList', p[1], p[2])

    # IdMore ::= epsilon | COMMA IdList
    def p_IdMore_empty(self, p):
        '''IdMore : '''
        p[0] = ('IdMore', None)

    def p_IdMore_list(self, p):
        '''IdMore : COMMA IdList'''
        p[0] = ('IdMore', p[2])

    # VarDec ::= epsilon | VarDeclaration
    def p_VarDec_empty(self, p):
        '''VarDec : '''
        p[0] = ('VarDec', None)

    def p_VarDec_declaration(self, p):
        '''VarDec : VarDeclaration'''
        p[0] = ('VarDec', p[1])

    # VarDeclaration ::= VAR VarDecList
    def p_VarDeclaration(self, p):
        '''VarDeclaration : VAR VarDecList'''
        p[0] = ('VarDeclaration', p[2])

    # VarDecList ::= TypeName VarIdList SEMI VarDecMore
    def p_VarDecList(self, p):
        '''VarDecList : TypeName VarIdList SEMI VarDecMore'''
        p[0] = ('VarDecList', p[1], p[2], p[4])

    # VarDecMore ::= epsilon | VarDecList
    def p_VarDecMore_empty(self, p):
        '''VarDecMore : '''
        p[0] = ('VarDecMore', None)

    def p_VarDecMore_list(self, p):
        '''VarDecMore : VarDecList'''
        p[0] = ('VarDecMore', p[1])

    # VarIdList ::= ID VarIdMore
    def p_VarIdList(self, p):
        '''VarIdList : ID VarIdMore'''
        p[0] = ('VarIdList', p[1], p[2])

    # VarIdMore ::= epsilon | COMMA VarIdList
    def p_VarIdMore_empty(self, p):
        '''VarIdMore : '''
        p[0] = ('VarIdMore', None)

    def p_VarIdMore_list(self, p):
        '''VarIdMore : COMMA VarIdList'''
        p[0] = ('VarIdMore', p[2])

    # ProcDec ::= epsilon | ProcDeclaration
    def p_ProcDec_empty(self, p):
        '''ProcDec : '''
        p[0] = ('ProcDec', None)

    def p_ProcDec_declaration(self, p):
        '''ProcDec : ProcDeclaration'''
        p[0] = ('ProcDec', p[1])

    # ProcDeclaration ::= PROCEDURE ProcName LPAREN ParamList RPAREN SEMI ProcDecPart ProcBody ProcDecMore
    def p_ProcDeclaration(self, p):
        '''ProcDeclaration : PROCEDURE ProcName LPAREN ParamList RPAREN SEMI ProcDecPart ProcBody ProcDecMore'''
        p[0] = ('ProcDeclaration', p[2], p[4], p[7], p[8], p[9])

    # ProcDecMore ::= epsilon | ProcDec
    def p_ProcDecMore_empty(self, p):
        '''ProcDecMore : '''
        p[0] = ('ProcDecMore', None)

    def p_ProcDecMore_proc(self, p):
        '''ProcDecMore : ProcDec'''
        p[0] = ('ProcDecMore', p[1])

    # ProcName ::= ID
    def p_ProcName(self, p):
        '''ProcName : ID'''
        p[0] = ('ProcName', p[1])

    # ParamList ::= epsilon | ParamDecList
    def p_ParamList_empty(self, p):
        '''ParamList : '''
        p[0] = ('ParamList', None)

    def p_ParamList_list(self, p):
        '''ParamList : ParamDecList'''
        p[0] = ('ParamList', p[1])

    # ParamDecList ::= Param ParamMore
    def p_ParamDecList(self, p):
        '''ParamDecList : Param ParamMore'''
        p[0] = ('ParamDecList', p[1], p[2])

    # ParamMore ::= epsilon | SEMI ParamDecList
    def p_ParamMore_empty(self, p):
        '''ParamMore : '''
        p[0] = ('ParamMore', None)

    def p_ParamMore_list(self, p):
        '''ParamMore : SEMI ParamDecList'''
        p[0] = ('ParamMore', p[2])

    # Param ::= TypeName FormList | VAR TypeName FormList
    def p_Param_type(self, p):
        '''Param : TypeName FormList'''
        p[0] = ('Param', p[1], p[2])

    def p_Param_var(self, p):
        '''Param : VAR TypeName FormList'''
        p[0] = ('Param', p[1], p[2], p[3])

    # FormList ::= ID FidMore
    def p_FormList(self, p):
        '''FormList : ID FidMore'''
        p[0] = ('FormList', p[1], p[2])

    # FidMore ::= epsilon | COMMA FormList
    def p_FidMore_empty(self, p):
        '''FidMore : '''
        p[0] = ('FidMore', None)

    def p_FidMore_list(self, p):
        '''FidMore : COMMA FormList'''
        p[0] = ('FidMore', p[2])

    # ProcDecPart ::= DeclarePart
    def p_ProcDecPart(self, p):
        '''ProcDecPart : DeclarePart'''
        p[0] = ('ProcDecPart', p[1])

    # ProcBody ::= ProgramBody
    def p_ProcBody(self, p):
        '''ProcBody : ProgramBody'''
        p[0] = ('ProcBody', p[1])

    # ProgramBody ::= BEGIN StmList END
    def p_ProgramBody(self, p):
        '''ProgramBody : BEGIN StmList END'''
        p[0] = ('ProgramBody', p[2])

    # StmList ::= Stm StmMore
    def p_StmList(self, p):
        '''StmList : Stm StmMore'''
        p[0] = ('StmList', p[1], p[2])

    # StmMore ::= epsilon | SEMI StmList
    def p_StmMore_empty(self, p):
        '''StmMore : '''
        p[0] = ('StmMore', None)

    def p_StmMore_list(self, p):
        '''StmMore : SEMI StmList'''
        p[0] = ('StmMore', p[2])

    # Stm ::= ConditionalStm | LoopStm | InputStm | OutputStm | ReturnStm | ID AssCall
    def p_Stm(self, p):
        '''Stm : ConditionalStm
               | LoopStm
               | InputStm
               | OutputStm
               | ReturnStm
               | ID AssCall'''
        if len(p) == 2:
            p[0] = ('Stm', p[1])
        else:
            p[0] = ('Stm', p[1], p[2])

    # AssCall ::= AssignmentRest | CallStmRest
    def p_AssCall(self, p):
        '''AssCall : AssignmentRest
                   | CallStmRest'''
        p[0] = ('AssCall', p[1])

    # AssignmentRest ::= VariMore ASSIGN Exp
    def p_AssignmentRest(self, p):
        '''AssignmentRest : VariMore ASSIGN Exp'''
        p[0] = ('AssignmentRest', p[1], p[3])

    # ConditionalStm ::= IF RelExp THEN StmList ELSE StmList FI
    def p_ConditionalStm(self, p):
        '''ConditionalStm : IF RelExp THEN StmList ELSE StmList FI'''
        p[0] = ('ConditionalStm', p[2], p[4], p[6])

    # LoopStm ::= WHILE RelExp DO StmList ENDWH
    def p_LoopStm(self, p):
        '''LoopStm : WHILE RelExp DO StmList ENDWH'''
        p[0] = ('LoopStm', p[2], p[4])

    # InputStm ::= READ LPAREN Invar RPAREN
    def p_InputStm(self, p):
        '''InputStm : READ LPAREN Invar RPAREN'''
        p[0] = ('InputStm', p[3])

    # Invar ::= ID
    def p_Invar(self, p):
        '''Invar : ID'''
        p[0] = ('Invar', p[1])

    # OutputStm ::= WRITE LPAREN Exp RPAREN
    def p_OutputStm(self, p):
        '''OutputStm : WRITE LPAREN Exp RPAREN'''
        p[0] = ('OutputStm', p[3])

    # ReturnStm ::= RETURN LPAREN Exp RPAREN
    def p_ReturnStm(self, p):
        '''ReturnStm : RETURN LPAREN Exp RPAREN'''
        p[0] = ('ReturnStm', p[3])

    # CallStmRest ::= LPAREN ActParamList RPAREN
    def p_CallStmRest(self, p):
        '''CallStmRest : LPAREN ActParamList RPAREN'''
        p[0] = ('CallStmRest', p[2])

    # ActParamList ::= epsilon | Exp ActParamMore
    def p_ActParamList_empty(self, p):
        '''ActParamList : '''
        p[0] = ('ActParamList', None)

    def p_ActParamList_list(self, p):
        '''ActParamList : Exp ActParamMore'''
        p[0] = ('ActParamList', p[1], p[2])

    # ActParamMore ::= epsilon | COMMA ActParamList
    def p_ActParamMore_empty(self, p):
        '''ActParamMore : '''
        p[0] = ('ActParamMore', None)

    def p_ActParamMore_list(self, p):
        '''ActParamMore : COMMA ActParamList'''
        p[0] = ('ActParamMore', p[2])

    # RelExp ::= Exp OtherRelE
    def p_RelExp(self, p):
        '''RelExp : Exp OtherRelE'''
        p[0] = ('RelExp', p[1], p[2])

    # OtherRelE ::= CmpOp Exp
    def p_OtherRelE(self, p):
        '''OtherRelE : CmpOp Exp'''
        p[0] = ('OtherRelE', p[1], p[2])

    # Exp ::= Term OtherTerm
    def p_Exp(self, p):
        '''Exp : Term OtherTerm'''
        p[0] = ('Exp', p[1], p[2])

    # OtherTerm ::= epsilon | AddOp Exp
    def p_OtherTerm_empty(self, p):
        '''OtherTerm : '''
        p[0] = ('OtherTerm', None)

    def p_OtherTerm_list(self, p):
        '''OtherTerm : AddOp Exp'''
        p[0] = ('OtherTerm', p[1], p[2])

    # Term ::= Factor OtherFactor
    def p_Term(self, p):
        '''Term : Factor OtherFactor'''
        p[0] = ('Term', p[1], p[2])

    # OtherFactor ::= epsilon | MultOp Term
    def p_OtherFactor_empty(self, p):
        '''OtherFactor : '''
        p[0] = ('OtherFactor', None)

    def p_OtherFactor_list(self, p):
        '''OtherFactor : MultOp Term'''
        p[0] = ('OtherFactor', p[1], p[2])

    # Factor ::= LPAREN Exp RPAREN | INTC | Variable
    def p_Factor_paren(self, p):
        '''Factor : LPAREN Exp RPAREN'''
        p[0] = ('Factor', p[2])

    def p_Factor_intc(self, p):
        '''Factor : INTC'''
        p[0] = ('Factor', p[1])

    def p_Factor_variable(self, p):
        '''Factor : Variable'''
        p[0] = ('Factor', p[1])

    # Variable ::= ID VariMore
    def p_Variable(self, p):
        '''Variable : ID VariMore'''
        p[0] = ('Variable', p[1], p[2])

    # VariMore ::= epsilon | LMIDPAREN Exp RMIDPAREN | DOT FieldVar
    def p_VariMore_empty(self, p):
        '''VariMore : '''
        p[0] = ('VariMore', None)

    def p_VariMore_index(self, p):
        '''VariMore : LMIDPAREN Exp RMIDPAREN'''
        p[0] = ('VariMore', p[2])

    def p_VariMore_field(self, p):
        '''VariMore : DOT FieldVar'''
        p[0] = ('VariMore', p[2])

    # FieldVar ::= ID FieldVarMore
    def p_FieldVar(self, p):
        '''FieldVar : ID FieldVarMore'''
        p[0] = ('FieldVar', p[1], p[2])

    # FieldVarMore ::= epsilon | LMIDPAREN Exp RMIDPAREN
    def p_FieldVarMore_empty(self, p):
        '''FieldVarMore : '''
        p[0] = ('FieldVarMore', None)

    def p_FieldVarMore_index(self, p):
        '''FieldVarMore : LMIDPAREN Exp RMIDPAREN'''
        p[0] = ('FieldVarMore', p[2])

    # CmpOp ::= LT | EQ
    def p_CmpOp(self, p):
        '''CmpOp : LT
                 | EQ'''
        p[0] = ('CmpOp', p[1])

    # AddOp ::= PLUS | MINUS
    def p_AddOp(self, p):
        '''AddOp : PLUS
                 | MINUS'''
        p[0] = ('AddOp', p[1])

    # MultOp ::= TIMES | OVER
    def p_MultOp(self, p):
        '''MultOp : TIMES
                  | OVER'''
        p[0] = ('MultOp', p[1])

    # Error rule for syntax errors
    def p_error(self, p):
        print(f"词法语法错误：在输入中遇到意外的 token '{p.value}' (类型: {p.type})，位于行 {p.lineno}")

    def parse_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = f.read() 
        tokens = self.lexer.analyze_file(file_path, "../result/token.txt") 
        '''
        self.parse_tree = self.parser.parse(tokens, lexer=None)  # 传递字符串
        return self.parse_tree
        '''
        token_iter = iter(tokens)  # 创建 token 迭代器

        def token_func():
            try:
                return next(token_iter)
            except StopIteration:
                return None

        self.parse_tree = self.parser.parse(None, tokenfunc=token_func) # 传递 tokenfunc
        #visualize_ast(self.parse_tree, "../data/ast.pdf")
        return self.parse_tree

def print_ast(node, indent=0):
    if isinstance(node, tuple):
        print('  ' * indent + node[0])
        for child in node[1:]:
            print_ast(child, indent + 1)
    elif node is not None:
        print('  ' * indent + str(node))

if __name__ == '__main__':

    parser = SNLParser()
    parse_tree = parser.parse_file("./data/demo.txt")

    if parse_tree:
        print("\n语法分析成功！")
        print("抽象语法树 (AST):")
        print_ast(parse_tree)
        print(parse_tree)
    else:
        print("\n语法分析失败！")