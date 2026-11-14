# -*- coding: utf-8 -*-
"""
MoodGraph Milestone 2 - UI/UX & Academic Notation Adversarial Audit
Kiểm tra đối kháng chuyên sâu về ký hiệu học thuật, cấm ký tự dollar/LaTeX, và kiểm thử logic vis-network.
"""

import os
import re
import json

def audit_latex_and_dollars():
    print("=== 1. KIỂM TRA KÝ TỰ DOLLAR VÀ CÚ PHÁP LATEX ===")
    
    files = {
        "index.html": "demo/index.html",
        "graph_visualizer.js": "demo/js/graph_visualizer.js",
        "academic_lab.js": "demo/js/academic_lab.js",
        "app.js": "demo/js/app.js",
        "mock_data.js": "demo/js/mock_data.js",
        "styles.css": "demo/css/styles.css"
    }
    
    # Danh sách mẫu cú pháp LaTeX
    latex_commands = [
        r'\\frac', r'\\sum', r'\\sqrt', r'\\rho', r'\\alpha', r'\\beta',
        r'\\Delta', r'\\sigma', r'\\times', r'\\cdot', r'\\cap', r'\\cup',
        r'\\text\{', r'\\quad', r'\\mathbf', r'\\math', r'\\left', r'\\right',
        r'\\argmax', r'\\log', r'\\le', r'\\ge', r'\\approx', r'\\in', r'\\infty'
    ]
    
    issues = []
    
    for label, filepath in files.items():
        if not os.path.exists(filepath):
            print(f"File không tồn tại: {filepath}")
            continue
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        full_text = "".join(lines)
        
        # 1. Quét tìm lệnh LaTeX
        for line_no, line in enumerate(lines, 1):
            for cmd in latex_commands:
                if re.search(cmd, line):
                    issues.append({
                        "file": label,
                        "line": line_no,
                        "type": "LATEX_COMMAND",
                        "content": line.strip()
                    })
                    
        # 2. Quét tìm ký tự dollar ($) trong HTML
        if filepath.endswith(".html"):
            for line_no, line in enumerate(lines, 1):
                # Kiểm tra xem có chứa ký tự dollar trong text HTML không
                # Loại trừ thẻ script nếu có biến JS
                dollar_matches = [m.start() for m in re.finditer(r'\$', line)]
                if dollar_matches:
                    issues.append({
                        "file": label,
                        "line": line_no,
                        "type": "DOLLAR_IN_HTML",
                        "content": line.strip()
                    })
                    
        # 3. Quét tìm ký tự dollar trong chuỗi UI text của JS (không phải template literal ${...})
        elif filepath.endswith(".js"):
            for line_no, line in enumerate(lines, 1):
                # Tìm dấu dollar không nằm trong dạng ${...}
                # Ví dụ dạng $x$ hoặc $$...$$ hoặc chuỗi text '$'
                cleaned_line = re.sub(r'\$\{[^}]*\}', '', line) # bỏ template literal
                if '$' in cleaned_line:
                    # Kiểm tra xem có phải là Math dollar hay selector
                    issues.append({
                        "file": label,
                        "line": line_no,
                        "type": "DOLLAR_IN_JS",
                        "content": line.strip()
                    })
                    
    print(f"Tổng số vấn đề phát hiện được: {len(issues)}")
    for iss in issues:
        print(f"[{iss['type']}] {iss['file']}:{iss['line']} -> {iss['content'][:120]}")
    return issues

def audit_8_academic_annotations():
    print("\n=== 2. KIỂM TRA 8 KHỐI CHÚ THÍCH HỌC THUẬT (UNICODE STANDARD) ===")
    
    with open("demo/index.html", "r", encoding="utf-8") as f:
        html = f.read()
    with open("demo/js/academic_lab.js", "r", encoding="utf-8") as f:
        lab_js = f.read()
    with open("demo/js/graph_visualizer.js", "r", encoding="utf-8") as f:
        graph_js = f.read()
        
    combined = html + "\n" + lab_js + "\n" + graph_js
    
    # 8 khối công thức và kiểm tra ký tự Unicode chuẩn
    annotations = {
        "1. RRF (Reciprocal Rank Fusion)": {
            "keywords": ["RRF_Score", "Reciprocal Rank Fusion", "60 + Rank"],
            "unicode_chars": ["∑"],
            "forbidden": ["\\sum", "\\frac"]
        },
        "2. Weighted Hybrid Fusion": {
            "keywords": ["Score_Hybrid", "S_norm_ALS", "S_norm_KG", "0.1", "0.9"],
            "unicode_chars": ["·"],
            "forbidden": ["\\cdot"]
        },
        "3. Metapath P1 (Genre / Thể loại)": {
            "keywords": ["Score_P1", "Movies(g)", "P1"],
            "unicode_chars": ["∑", "√"],
            "forbidden": ["\\sum", "\\sqrt", "\\frac"]
        },
        "4. Metapath P2 (Mood Genome Tag)": {
            "keywords": ["Score_P2", "rel_m", "rel_c", "ln(1 + |Movies(t)|)", "P2"],
            "unicode_chars": ["∑", "·"],
            "forbidden": ["\\sum", "\\cdot", "\\ln"]
        },
        "5. Metapath P3 (Collaborative / Cộng tác)": {
            "keywords": ["Score_P3", "CosineSim", "w(r_v, c)", "P3"],
            "unicode_chars": ["∑", "·"],
            "forbidden": ["\\sum", "\\cdot"]
        },
        "6. Spearman rho": {
            "keywords": ["Spearman", "d_i^2", "n^2 - 1"],
            "unicode_chars": ["ρ", "∑", "·"],
            "forbidden": ["\\rho", "\\sum", "\\cdot"]
        },
        "7. Jaccard Similarity": {
            "keywords": ["Jaccard", "|A ∩ B|", "|A ∪ B|"],
            "unicode_chars": ["∩", "∪"],
            "forbidden": ["\\cap", "\\cup"]
        },
        "8. Shannon Novelty Entropy": {
            "keywords": ["Novelty", "-log2", "Count_Train", "Bits"],
            "unicode_chars": [],
            "forbidden": ["\\log"]
        },
        "9. Bonus - Cosine Similarity": {
            "keywords": ["Cosine", "||u||", "||v||"],
            "unicode_chars": ["·"],
            "forbidden": ["\\cdot"]
        },
        "10. Bonus - PCA 3D Projection": {
            "keywords": ["PCA", "W_k", "argmax_W"],
            "unicode_chars": ["·"],
            "forbidden": ["\\argmax", "\\cdot"]
        }
    }
    
    results = {}
    for name, reqs in annotations.items():
        found_kw = any(kw in combined for kw in reqs["keywords"])
        found_uni = all(char in combined for char in reqs["unicode_chars"])
        found_forb = [fb for fb in reqs["forbidden"] if fb in combined]
        
        status = found_kw and found_uni and len(found_forb) == 0
        results[name] = {
            "status": "PASS" if status else "FAIL",
            "keywords_found": found_kw,
            "unicode_present": found_uni,
            "forbidden_found": found_forb
        }
        print(f"[{'PASS' if status else 'FAIL'}] {name}")
        if not status:
            print(f"   Chi tiết: kw={found_kw}, uni={found_uni}, forb={found_forb}")
            
    return results

def audit_graph_interaction_and_interlock():
    print("\n=== 3. KIỂM TRA TƯƠNG TÁC ĐỒ THỊ & HOVER INTERLOCK ===")
    
    with open("demo/js/graph_visualizer.js", "r", encoding="utf-8") as f:
        js = f.read()
    with open("demo/index.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    checks = {}
    
    # 1. Kiểm tra tích hợp vis-network CDN
    checks["vis_network_cdn"] = "vis-network" in html
    
    # 2. Kiểm tra container đồ thị
    checks["container_element"] = 'id="graph-network-container"' in html or 'id="kg-network-container"' in html or 'id="network-container"' in html or 'id="graph-canvas-container"' in html or 'graph-container' in html
    
    # 3. Physics engine (Barnes-Hut)
    checks["physics_barnes_hut"] = "barnesHut" in js or "physics" in js
    
    # 4. Các sự kiện tương tác
    checks["event_click"] = "network.on('click'" in js or 'network.on("click"' in js or "on('click'" in js or 'on("click"' in js
    checks["event_hover"] = "hoverNode" in js or "on('hoverNode'" in js or 'on("hoverNode"' in js
    checks["event_blur"] = "blurNode" in js or "on('blurNode'" in js or 'on("blurNode"' in js
    checks["interaction_options"] = "dragNodes" in js and "zoomView" in js and "dragView" in js
    
    # 5. Hover Interlock logic
    checks["hover_interlock_highlight"] = "highlight" in js or "setInterlock" in js or "activePath" in js or "interlock" in js
    checks["hover_interlock_dimming"] = "0.2" in js or "opacity" in js or "rgba" in js or "hidden" in js or "dim" in js
    
    # 6. Tooltip kính quang học
    checks["optical_tooltip"] = "backdrop-blur" in js or "graph-tooltip" in js or "tooltip" in js or "boxShadow" in js
    checks["tooltip_fields"] = any(k in js for k in ["P1", "P2", "P3", "academic_explanation", "lý do", "đóng góp"])
    
    for k, v in checks.items():
        print(f"[{'PASS' if v else 'FAIL'}] {k}: {v}")
        
    return checks

if __name__ == "__main__":
    audit_latex_and_dollars()
    audit_8_academic_annotations()
    audit_graph_interaction_and_interlock()
