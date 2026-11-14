"""
Tầng 4: Browser Runtime & Static Assets Smoke Check.
Kiểm định:
1. Cú pháp toàn bộ JavaScript frontend (node -c).
2. Nạp đúng và đủ các tài nguyên HTML, CSS, JS tĩnh qua FastAPI StaticFiles mount.
3. Không có liên kết đứt gãy trong demo/index.html.
4. Tuân thủ triệt để Quy chuẩn CẤM dấu Dollar ($) và cú pháp KaTeX/LaTeX bị vỡ trong giao diện.
"""

import re
import subprocess
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from recommender.api.app import app

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture(scope="module")
def api_client():
    with TestClient(app) as client:
        yield client


class TestTier4BrowserAndSmoke:
    """Bộ kiểm thử kiểm tra tính toàn vẹn frontend, static assets và môi trường runtime browser."""

    def test_01_javascript_syntax_cleanliness(self):
        """Kiểm tra biên dịch cú pháp toàn bộ JavaScript frontend bằng Node.js (node -c)."""
        js_dir = PROJECT_ROOT / "demo" / "js"
        js_files = list(js_dir.glob("*.js"))
        assert len(js_files) >= 5, "Thư mục demo/js phải chứa ít nhất 5 tệp JS."

        for js_file in js_files:
            cmd = ["node", "-c", str(js_file)]
            res = subprocess.run(cmd, capture_output=True, text=True)
            assert res.returncode == 0, (
                f"Lỗi cú pháp JavaScript trong tệp {js_file.name}:\n{res.stderr}"
            )

    def test_02_static_homepage_serving(self, api_client):
        """Kiểm tra serving trang web chính tại root / và /demo/."""
        # 1. Truy cập root /
        resp_root = api_client.get("/")
        assert resp_root.status_code == 200
        assert "text/html" in resp_root.headers.get("content-type", "")
        assert "MoodGraph" in resp_root.text

        # 2. Truy cập /demo/
        resp_demo = api_client.get("/demo/")
        assert resp_demo.status_code == 200
        assert "text/html" in resp_demo.headers.get("content-type", "")

    def test_03_static_stylesheets_serving(self, api_client):
        """Kiểm tra serving file CSS stylesheet."""
        resp_css = api_client.get("/css/styles.css")
        assert resp_css.status_code == 200
        assert "text/css" in resp_css.headers.get("content-type", "")
        assert len(resp_css.text) > 1000

    def test_04_static_javascript_modules_serving(self, api_client):
        """Kiểm tra serving toàn bộ các module JavaScript frontend qua FastAPI."""
        expected_modules = [
            "/js/app.js",
            "/js/academic_lab.js",
            "/js/graph_visualizer.js",
            "/js/mock_data.js",
            "/js/modal_component.js",
        ]
        for mod_path in expected_modules:
            resp = api_client.get(mod_path)
            assert resp.status_code == 200, f"Module {mod_path} không tìm thấy (404)!"
            c_type = resp.headers.get("content-type", "")
            assert "javascript" in c_type or "text" in c_type, (
                f"Content-Type không phù hợp cho {mod_path}: {c_type}"
            )
            assert len(resp.text) > 100

    def test_05_no_broken_internal_links_in_index_html(self):
        """Kiểm tra index.html không chứa liên kết nội bộ đứt gãy tới các file tĩnh cục bộ."""
        html_path = PROJECT_ROOT / "demo" / "index.html"
        assert html_path.exists(), "demo/index.html phải tồn tại."
        html_content = html_path.read_text(encoding="utf-8")

        # Tìm các link rel="stylesheet" href="..." cục bộ
        css_links = re.findall(r'<link[^>]+href=["\']([^"\']+\.css)["\']', html_content)
        for link in css_links:
            if not link.startswith("http"):
                clean_path = link.lstrip("./").lstrip("/")
                file_target = PROJECT_ROOT / "demo" / clean_path
                assert file_target.exists(), f"Liên kết CSS đứt gãy: {link} -> {file_target}"

        # Tìm các script src="..." cục bộ
        js_links = re.findall(r'<script[^>]+src=["\']([^"\']+\.js)["\']', html_content)
        for link in js_links:
            if not link.startswith("http"):
                clean_path = link.lstrip("./").lstrip("/")
                file_target = PROJECT_ROOT / "demo" / clean_path
                assert file_target.exists(), f"Liên kết JavaScript đứt gãy: {link} -> {file_target}"

    def test_06_typography_strict_no_dollar_latex_in_ui(self):
        """
        Kiểm tra tuân thủ quy chuẩn Typography:
        Tuyệt đối CẤM 100% cú pháp KaTeX/LaTeX bị vỡ (\\frac, \\sum, $$) và cấm dấu dollar
        trong các nhãn công thức toán học trên giao diện frontend.
        """
        html_path = PROJECT_ROOT / "demo" / "index.html"
        content = html_path.read_text(encoding="utf-8")

        # Cấm dấu dollar đôi ($$)
        assert "$$" not in content, "Phát hiện dấu dollar đôi ($$) trong demo/index.html!"
        # Cấm các lệnh LaTeX thông dụng
        latex_commands = ["\\frac", "\\sum", "\\int", "\\text{", "\\sqrt", "\\alpha", "\\beta"]
        for cmd in latex_commands:
            assert cmd not in content, f"Phát hiện cú pháp LaTeX '{cmd}' trong demo/index.html!"
