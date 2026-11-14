# -*- coding: utf-8 -*-
import re
import os

files_to_check = [
    "demo/index.html",
    "demo/js/graph_visualizer.js",
    "demo/js/academic_lab.js",
    "demo/js/app.js",
    "demo/js/mock_data.js",
    "demo/js/modal_component.js",
    "demo/css/styles.css"
]

known_latex = [
    "frac", "sum", "sqrt", "rho", "alpha", "beta", "Delta", "sigma",
    "times", "cdot", "cap", "cup", "text", "quad", "mathbf", "math",
    "left", "right", "argmax", "argmin", "log", "le", "ge", "approx",
    "in", "infty", "begin", "end", "lim", "to", "int", "prod"
]

print("=== KIỂM TRA LỆNH LATEX TOÀN DIỆN ===")
latex_found = []
for p in files_to_check:
    if not os.path.exists(p):
        continue
    with open(p, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for l_no, line in enumerate(lines, 1):
        for cmd in known_latex:
            pattern = r'\\' + cmd + r'([^a-zA-Z]|$)'
            if re.search(pattern, line):
                latex_found.append((p, l_no, cmd, line.strip()))

if latex_found:
    print(f"PHÁT HIỆN {len(latex_found)} LỆNH LATEX:")
    for item in latex_found:
        print(f"  {item[0]}:{item[1]} -> \\{item[2]} trong '{item[3]}'")
else:
    print("HOÀN TOÀN KHÔNG CÓ BẤT KỲ LỆNH LATEX NÀO! (100% SẠCH)")

print("\n=== KIỂM TRA KÝ TỰ DOLLAR TRONG HTML & CHUỖI HIỂN THỊ ===")
dollar_in_html = []
with open("demo/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()
for l_no, line in enumerate(lines, 1):
    if "$" in line:
        dollar_in_html.append((l_no, line.strip()))

if dollar_in_html:
    print(f"PHÁT HIỆN {len(dollar_in_html)} KÝ TỰ DOLLAR TRONG HTML:")
    for l_no, text in dollar_in_html:
        print(f"  demo/index.html:{l_no} -> {text}")
else:
    print("HTML KHÔNG CHỨA BẤT KỲ KÝ TỰ DOLLAR NÀO! (100% SẠCH)")

print("\n=== KIỂM TRA KÝ TỰ DOLLAR KHÔNG PHẢI JS TEMPLATE STRING TRONG FILE JS ===")
js_files = ["demo/js/graph_visualizer.js", "demo/js/academic_lab.js", "demo/js/app.js", "demo/js/mock_data.js", "demo/js/modal_component.js"]
suspicious_dollars = []
for p in js_files:
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Loại bỏ các template literal hợp lệ dạng `${...}`
    # Chú ý regex nhiều dòng
    cleaned = re.sub(r'\$\{[^}]*\}', '', content)
    
    # Tìm xem còn dấu dollar nào sót lại không
    for l_no, line in enumerate(cleaned.splitlines(), 1):
        if "$" in line:
            # Kiểm tra xem có phải là comment giải thích về việc cấm dollar không
            stripped = line.strip()
            if "không dùng" in stripped or "cấm" in stripped or "dollar" in stripped or "Tuyệt đối" in stripped:
                continue
            suspicious_dollars.append((p, l_no, stripped))

if suspicious_dollars:
    print(f"PHÁT HIỆN {len(suspicious_dollars)} KÝ TỰ DOLLAR ĐÁNG NGỜ TRONG JS:")
    for p, l_no, text in suspicious_dollars:
        print(f"  {p}:{l_no} -> {text}")
else:
    print("TẤT CẢ FILE JS HOÀN TOÀN KHÔNG CÓ KÝ TỰ DOLLAR HIỂN THỊ TOÁN/UI! (100% SẠCH)")
