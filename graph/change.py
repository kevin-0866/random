import ast
import os

class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self, code_dir):
        self.code_dir = code_dir
        self.func_defs = {}
        self.func_calls = {}
        self.var_usage = {}
        self.class_methods = {}  # New: Track class methods
        self.var_types = {}  # New: Track variable types

    def visit_FunctionDef(self, node):
        func_name = node.name
        self.func_defs[func_name] = node
        self.func_calls[func_name] = []
        self.var_usage[func_name] = set()

        for inner in ast.walk(node):
            if isinstance(inner, ast.Call):
                if isinstance(inner.func, ast.Name):
                    self.func_calls[func_name].append(inner.func.id)
                elif isinstance(inner.func, ast.Attribute):
                    self.func_calls[func_name].append(inner.func.attr)
            elif isinstance(inner, ast.Name):
                self.var_usage[func_name].add(inner.id)

        self.generic_visit(node)

    def visit_ClassDef(self, node):
        class_name = node.name
        self.class_methods[class_name] = set()

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self.class_methods[class_name].add(item.name)

        self.generic_visit(node)

    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
                self.var_types[var_name] = node.value.func.id
            elif isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
                class_name = node.value.func.value.id
                method_name = node.value.func.attr
                self.var_types[var_name] = f"{class_name}.{method_name}"

        self.generic_visit(node)

    def visit_Attribute(self, node):
        if isinstance(node.ctx, ast.Load):
            if isinstance(node.value, ast.Name):
                var_name = node.value.id
                if var_name in self.var_types:
                    class_name, method_name = self.var_types[var_name].split(".")
                    if class_name in self.class_methods and method_name in self.class_methods[class_name]:
                        self.func_calls[var_name].append(method_name)

        self.generic_visit(node)

    def analyze(self, file_name):
        with open(file_name, "r") as file:
            tree = ast.parse(file.read(), filename=file_name)
            self.visit(tree)
