#!/usr/bin/env python3
"""
MOODGRAPH TASK 3A: AST BEHAVIOR-PRESERVATION AUDITOR
===================================================
Compares abstract syntax trees (AST) of Python files before and after
comment/docstring updates, guaranteeing that executable logic, control flow,
function signatures, return values, and constants remain 100% identical.
"""

import ast
import sys
from pathlib import Path
from typing import Dict, Tuple

class DocstringAndCommentStripper(ast.NodeTransformer):
    """Strips docstrings from modules, classes, and functions."""

    def _strip_docstring(self, body):
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            return body[1:]
        return body

    def visit_Module(self, node):
        self.generic_visit(node)
        node.body = self._strip_docstring(node.body)
        return node

    def visit_ClassDef(self, node):
        self.generic_visit(node)
        node.body = self._strip_docstring(node.body)
        return node

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        node.body = self._strip_docstring(node.body)
        return node

    def visit_AsyncFunctionDef(self, node):
        self.generic_visit(node)
        node.body = self._strip_docstring(node.body)
        return node


def get_normalized_ast(source_code: str) -> str:
    """Parse source code, strip docstrings, and dump AST structure."""
    tree = ast.parse(source_code)
    cleaned = DocstringAndCommentStripper().visit(tree)
    ast.fix_missing_locations(cleaned)
    return ast.dump(cleaned, include_attributes=False)


def compare_files(file1: Path, file2: Path) -> Tuple[bool, str]:
    """Compare normalized AST of two Python files."""
    code1 = file1.read_text(encoding="utf-8")
    code2 = file2.read_text(encoding="utf-8")
    ast1 = get_normalized_ast(code1)
    ast2 = get_normalized_ast(code2)
    if ast1 == ast2:
        return True, "ASTs are strictly equivalent."
    return False, "AST executable logic differs!"


def compare_against_git_head(file_path: Path) -> Tuple[bool, str]:
    """Compare working tree file against its HEAD version in git."""
    import subprocess
    repo_root = file_path.parent
    while not (repo_root / ".git").exists() and repo_root != repo_root.parent:
        repo_root = repo_root.parent

    rel_path = file_path.resolve().relative_to(repo_root.resolve()).as_posix()
    try:
        head_code = subprocess.check_output(
            ["git", "show", f"HEAD:{rel_path}"],
            cwd=str(repo_root),
            text=True,
            encoding="utf-8"
        )
    except Exception as e:
        return False, f"Could not retrieve HEAD version: {e}"

    current_code = file_path.read_text(encoding="utf-8")
    ast_head = get_normalized_ast(head_code)
    ast_curr = get_normalized_ast(current_code)
    if ast_head == ast_curr:
        return True, "Executable AST matches HEAD 100%."
    return False, "Executable AST differs from HEAD!"


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
        if target.is_file():
            ok, msg = compare_against_git_head(target)
            print(f"{target.name}: {'PASS' if ok else 'FAIL'} - {msg}")
            sys.exit(0 if ok else 1)
    print("Usage: python check_ast_equivalence.py <file_path>")

