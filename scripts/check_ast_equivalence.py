#!/usr/bin/env python3
"""
MOODGRAPH TASK 3A: AST BEHAVIOR-PRESERVATION AUDITOR
===================================================
So sánh cây cú pháp trừu tượng (AST) của các file Python trước và sau khi bổ sung
chú thích/docstrings, bảo đảm 100% logic thực thi, luồng điều khiển, chữ ký hàm,
giá trị trả về và hằng số được giữ nguyên vẹn.
"""

import argparse
import ast
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

# Reconfigure stdout/stderr for utf-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


class DocstringAndCommentStripper(ast.NodeTransformer):
    """Loại bỏ docstrings cấp module, class và function để chỉ giữ lại mã thực thi."""

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
    """Phân tích cú pháp mã nguồn, loại bỏ docstring và trích xuất cấu trúc AST chuẩn hóa."""
    tree = ast.parse(source_code)
    cleaned = DocstringAndCommentStripper().visit(tree)
    ast.fix_missing_locations(cleaned)
    return ast.dump(cleaned, include_attributes=False)


def compare_files(file1: Path, file2: Path) -> Tuple[bool, str]:
    """So sánh AST chuẩn hóa giữa hai tệp Python trên đĩa."""
    code1 = file1.read_text(encoding="utf-8")
    code2 = file2.read_text(encoding="utf-8")
    ast1 = get_normalized_ast(code1)
    ast2 = get_normalized_ast(code2)
    if ast1 == ast2:
        return True, "ASTs are strictly equivalent."
    return False, "AST executable logic differs!"


def compare_against_git_ref(file_path: Path, base_ref: str = "92e6305") -> Tuple[bool, str]:
    """So sánh file hiện tại với phiên bản tại một git commit / ref cụ thể."""
    repo_root = file_path.resolve().parent
    while not (repo_root / ".git").exists() and repo_root != repo_root.parent:
        repo_root = repo_root.parent

    rel_path = file_path.resolve().relative_to(repo_root.resolve()).as_posix()
    try:
        base_code = subprocess.check_output(
            ["git", "show", f"{base_ref}:{rel_path}"],
            cwd=str(repo_root),
            text=True,
            encoding="utf-8",
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        return False, f"Could not retrieve ref {base_ref}:{rel_path} ({e})"

    current_code = file_path.read_text(encoding="utf-8")
    try:
        ast_base = get_normalized_ast(base_code)
        ast_curr = get_normalized_ast(current_code)
    except Exception as e:
        return False, f"AST parsing failed: {e}"

    if ast_base == ast_curr:
        return True, f"Executable AST matches {base_ref} 100%."
    return False, f"Executable AST differs from {base_ref}!"


def main():
    parser = argparse.ArgumentParser(
        description="Kiểm toán tính bảo toàn 100% cây cú pháp thực thi (AST Equivalence Auditor)."
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="Đường dẫn file Python hoặc thư mục cần kiểm toán AST.",
    )
    parser.add_argument(
        "--base",
        default="92e6305",
        help="Git commit / ref cơ sở để đối chiếu (mặc định: 92e6305).",
    )
    parser.add_argument(
        "--all-als",
        action="store_true",
        help="Kiểm toán toàn bộ 12 module cốt lõi trong recommender/als/ và các scripts liên quan.",
    )

    args = parser.parse_args()

    # Xử lý danh sách file
    files_to_check: List[Path] = []
    repo_root = Path(__file__).resolve().parent.parent

    if args.all_als or not args.targets:
        als_modules = sorted((repo_root / "recommender" / "als").glob("*.py"))
        files_to_check.extend(als_modules)
        script_files = [
            repo_root / "scripts" / "run_m10_delivery.py",
            repo_root / "scripts" / "audit_m10_release.py",
            repo_root / "scripts" / "run_m09_diagnostics.py",
            repo_root / "scripts" / "run_m08_frozen_benchmark.py",
            repo_root / "scripts" / "run_m07_tuning.py",
            repo_root / "scripts" / "run_m06_als_topn.py",
            repo_root / "scripts" / "run_m05_train_als.py",
            repo_root / "scripts" / "run_m04_toy_als.py",
            repo_root / "scripts" / "run_m03_popularity.py",
            repo_root / "scripts" / "run_m01_audit.py",
            repo_root / "scripts" / "verify_m02_evaluator.py",
            repo_root / "scripts" / "hermes_memory.py",
        ]
        files_to_check.extend([p for p in script_files if p.exists()])
    else:
        for t in args.targets:
            p = Path(t).resolve()
            if p.is_file() and p.suffix == ".py":
                files_to_check.append(p)
            elif p.is_dir():
                files_to_check.extend(sorted(p.rglob("*.py")))

    if not files_to_check:
        print("Không tìm thấy tệp Python nào để kiểm toán.")
        sys.exit(1)

    print(f"=== KIỂM TOÁN TÍNH BẢO TOÀN AST SO VỚI BASE REF: {args.base} ===")
    all_pass = True
    for f in files_to_check:
        ok, msg = compare_against_git_ref(f, base_ref=args.base)
        status = "PASS" if ok else "FAIL"
        rel_str = f.relative_to(repo_root).as_posix() if repo_root in f.parents else f.name
        print(f"  [{status}] {rel_str:<42} : {msg}")
        if not ok:
            all_pass = False

    print("=" * 70)
    if all_pass:
        print(f"KẾT QUẢ: 100% TẤT CẢ {len(files_to_check)} FILES ĐẠT AST MATCH VỚI REF {args.base}.")
        sys.exit(0)
    else:
        print(f"KẾT QUẢ: PHÁT HIỆN FILE SAI LỆCH CÂY CÚ PHÁP THỰC THI SO VỚI {args.base}!")
        sys.exit(1)


if __name__ == "__main__":
    main()
