import sys
sys.path.append("../")
from lexer import *
from parser import *
from Quad import *
from ConstantFolder import *
from MIPSGenerator import *

def main():
    src_file = "../data/7-bubbleSort.txt"
    #语法 + 词法
    parser = SNLParser()
    parse_tree = parser.parse_file(src_file)
    if parse_tree:
        print("\n语法分析成功！")
        #语意 + 中间代码
        semantic_analyzer = SemanticAnalyzer()
        semantic_analyzer.analyze(parse_tree)
        print("\n语义分析完成！")
        quad_list = semantic_analyzer.quadruples
        print("\n四元式生成完成！")
        #中间代码优化
        folder = ConstantFolder(semantic_analyzer.quadruples)
        optimized_quads = folder.fold_constants()
        print("\n四元式列表优化完成！")
        #目标代码生成
        mips_gen = MIPSGenerator(optimized_quads)
        mips_code = mips_gen.generate()
        print("\n目标代码生成完成！")

if __name__ == "__main__":
    main()