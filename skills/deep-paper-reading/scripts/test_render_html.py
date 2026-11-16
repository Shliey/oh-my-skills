"""Verify fidelity, correspondence, offline assets, and rejected input."""

import copy
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
import base64

from render_html import ASSETS, STAGES, SUMMARY, render


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.elements = []
        self.rows = []
        self.parts = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elements.append((tag, attrs))
        classes = attrs.get("class", "").split()
        if "row" in classes:
            self.parts = []
            self.rows.append(self.parts)
        for label in ("original", "translation", "annotation"):
            if label in classes:
                self.parts.append(label)


def example():
    note = {"function": "报告结果", "role": "支持主张", "technique": "尚未验证外部效度。"}
    return {
        "title": "Test & compare", "course": "研究方法 <实验课>",
        "mode": "full", "coverage": "complete", "source": "合成论文，完整正文。",
        "sections": [{
            "title": "Abstract",
            "blocks": [{
                "kind": "paragraph", "locator": "摘要第1段",
                "original": 'Results: 31%. <script>alert("x")</script> & data.',
                "translation": "结果为 31%。", "annotation": note,
                "highlights": [{"category": "evidence", "text": "31%"}],
            }],
        }, {
            "title": "Method",
            "blocks": [
                {
                    "kind": "equation", "locator": "公式 (1)", "original": "Keep s > τ.",
                    "formula": "s > τ", "translation": "保留分数大于阈值的条目。",
                    "annotation": dict(note, technique="[论文明确] 阈值数值未说明。"),
                    "highlights": [{"category": "method", "text": "s > τ"}],
                }, {
                    "kind": "table", "locator": "表 1", "original": "Table 1. Outcomes.",
                    "translation": "表 1. 结果。", "annotation": note,
                    "table": {"columns": ["Group", "%"], "rows": [["A", "31"]]},
                }, {
                    "kind": "figure", "locator": "图 1", "original": "Figure 1. Diagram.",
                    "translation": "图 1. 示意图。", "annotation": note,
                    "image": "diagram.png", "alt": "单像素测试图",
                },
            ],
        }],
        "summary": {
            **{key: {"text": "基于摘要或方法。", "refs": ["p-1-1", "p-2-1"]} for key in SUMMARY},
            "rebuttal": {"text": "论文未明确处理反驳。", "unavailable": True},
        },
        "stages": {str(i): [{"text": name, "refs": ["p-2-1"], "answer": i == 8}]
                   for i, name in enumerate(STAGES, 1)},
    }


class RenderTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        (self.folder / "diagram.png").write_bytes(base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aXewAAAAASUVORK5CYII="
        ))
        self.packet = example()

    def test_order_links_and_marks(self):
        result = render(self.packet, self.folder)
        actual = Document(result)
        self.assertEqual(actual.rows, [["original", "translation", "annotation"]] * 4)
        ids = [attrs["id"] for _, attrs in actual.elements if "id" in attrs]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual([i for i in ids if i.startswith("p-")], ["p-1-1", "p-2-1", "p-2-2", "p-2-3"])
        for _, attrs in actual.elements:
            if "href" in attrs:
                self.assertIn(attrs["href"].removeprefix("#"), ids)
        self.assertIn('Results: <mark class="evidence" title="蓝色 · 实证证据">31%</mark>.', result)
        self.assertIn('<p>结果为 31%。</p>', result)
        self.assertNotIn("<script>", result)
        self.assertIn("&lt;script&gt;", result)
        self.assertIn("阈值数值未说明", result)
        self.assertIn("论文未明确处理反驳", result)
        self.assertEqual(sum(a.get("class") == "stage" for _, a in actual.elements), 8)

    def test_offline_assets_and_source_integrity(self):
        result = render(self.packet, self.folder)
        self.assertIn('aria-label="公式">s &gt; τ', result)
        self.assertIn("<td>31</td>", result)
        self.assertIn('src="data:image/png;base64,', result)
        self.assertIn("课程：研究方法 &lt;实验课&gt;", result)
        self.assertIn("font-src data:; img-src data:", result)
        embedded = re.findall(r"data:font/ttf;base64,([A-Za-z0-9+/=]+)", result)
        for value, stem in zip(embedded, ("Lora", "IBMPlexSans"), strict=True):
            self.assertEqual(base64.b64decode(value), (ASSETS / "fonts" / (stem + ".ttf")).read_bytes())
        for _, attrs in Document(result).elements:
            if "src" in attrs:
                self.assertTrue(attrs["src"].startswith("data:"))
        self.assertEqual(result.count("SIL OPEN FONT LICENSE"), 2)

    def test_gap_requires_honest_coverage(self):
        self.packet["sections"][0]["blocks"][0] = {
            "kind": "gap", "locator": "摘要第1段", "note": "扫描页缺失。",
            "annotation": {"function": "未知", "role": "未知", "technique": "无法核对。"},
        }
        with self.assertRaisesRegex(ValueError, "gap requires"):
            render(self.packet, self.folder)
        self.packet.update(coverage="partial", coverage_note="摘要页缺失。", stages={})
        result = render(self.packet, self.folder)
        self.assertIn("部分阅读：摘要页缺失", result)
        self.assertIn("扫描页缺失", result)
        self.assertEqual(Document(result).rows[0], ["original", "annotation"])
        self.assertNotIn("八阶段深读", result)

    def test_full_requires_all_stages(self):
        self.packet["stages"].pop("8")
        with self.assertRaisesRegex(ValueError, "all eight"):
            render(self.packet, self.folder)
        self.packet.update(mode="module", coverage="focused", coverage_note="只读方法。")
        self.packet.pop("course")
        self.packet["summary"]["strongest"] = {"text": "局部材料不足。", "unavailable": True}
        result = render(self.packet, self.folder)
        self.assertIn("局部阅读：只读方法", result)
        self.assertNotIn("课程：", result)

    def test_invalid_marks_backlinks_and_table(self):
        invalid = [
            ("match exactly once", lambda p: p["sections"][0]["blocks"][0]["highlights"][0].update(text="absent")),
            ("overlapping", lambda p: p["sections"][0]["blocks"][0]["highlights"].append({"category": "method", "text": "31%."})),
            ("unresolved passage", lambda p: p["summary"]["claim"].update(refs=["p-99-99"])),
            ("row width", lambda p: p["sections"][1]["blocks"][1]["table"]["rows"].append(["A"])),
            ("stay inside", lambda p: p["sections"][1]["blocks"][2].update(image="../outside.png")),
        ]
        for message, change in invalid:
            with self.subTest(message=message):
                packet = copy.deepcopy(self.packet)
                change(packet)
                with self.assertRaisesRegex(ValueError, message):
                    render(packet, self.folder)

    def test_cli_output_is_single_and_will_not_overwrite(self):
        source, output = self.folder / "packet.json", self.folder / "paper.html"
        source.write_text(json.dumps(self.packet, ensure_ascii=False), encoding="utf-8")
        command = [sys.executable, "-B", str(Path(__file__).with_name("render_html.py")), str(source), str(output)]
        subprocess.run(command, check=True, capture_output=True)
        before = output.read_bytes()
        self.assertTrue(before.startswith(b"<!doctype html>"))
        self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
        self.assertEqual(output.read_bytes(), before)
        self.assertEqual({p.name for p in self.folder.iterdir()}, {"packet.json", "diagram.png", "paper.html"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
