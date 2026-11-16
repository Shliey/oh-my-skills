"""Render a local UTF-8 reading packet to one inert, offline HTML file."""

import argparse
import base64
from html import escape
import json
from pathlib import Path
import re
from string import Template


ASSETS = Path(__file__).resolve().parents[1] / "assets"
COLORS = {
    "thesis": "黄色 · 核心论点", "concept": "红色 · 关键概念",
    "evidence": "蓝色 · 实证证据", "rebuttal": "绿色 · 让步或反驳",
    "method": "紫色 · 方法论",
}
STAGES = (
    "研究问题与输入输出", "整体架构", "数据表示", "关键机制",
    "训练与推理", "完整实例追踪", "创新与实验证据", "总结与自测",
)
SUMMARY = {
    "problem": "问题", "thesis": "论点", "evidence": "证据",
    "rebuttal": "反驳", "conclusion": "结论", "claim": "一句话核心主张",
    "strongest": "论证最强处", "weakest": "论证最弱处",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def obj(value, label):
    require(isinstance(value, dict), f"{label}: expected an object")
    return value


def array(value, label, *, nonempty=False):
    require(isinstance(value, list) and (value or not nonempty),
            f"{label}: expected {'a nonempty' if nonempty else 'an'} array")
    return value


def string(value, label):
    require(isinstance(value, str) and value.strip(), f"{label}: expected nonempty text")
    return value


def field(data, key):
    return string(data.get(key), key)


def enc(value):
    return base64.b64encode(value).decode("ascii")


def font_assets():
    styles, licenses = [], []
    for name, stem in (("Lora", "Lora"), ("IBM Plex Sans", "IBMPlexSans")):
        directory = ASSETS / "fonts"
        styles.append(
            f'@font-face {{ font-family: "{name}"; font-style: normal; '
            f'font-weight: 400 700; src: url(data:font/ttf;base64,'
            f'{enc((directory / (stem + ".ttf")).read_bytes())}) format("truetype"); }}'
        )
        license_text = (directory / (stem + "-OFL.txt")).read_text(encoding="utf-8")
        licenses.append(f"<h3>{name}</h3><pre>{escape(license_text)}</pre>")
    return "\n".join(styles), (
        '<details class="wrap metadata"><summary>字体许可证</summary>'
        + "".join(licenses) + "</details>"
    )


def highlighted(source, marks, label):
    spans = []
    for item in array(marks, f"{label}.highlights"):
        item = obj(item, f"{label}.highlight")
        excerpt, category = field(item, "text"), field(item, "category")
        require(category in COLORS, f"{label}: unknown highlight category {category}")
        # Find literal occurrences, including overlaps. An explicit occurrence is 1-based.
        starts = [m.start() for m in re.finditer(f"(?={re.escape(excerpt)})", source)]
        occurrence = item.get("occurrence")
        if occurrence is None:
            require(len(starts) == 1, f"{label}: highlight must match exactly once or name occurrence")
            occurrence = 1
        require(type(occurrence) is int and 1 <= occurrence <= len(starts),
                f"{label}: highlight occurrence not found")
        start = starts[occurrence - 1]
        spans.append((start, start + len(excerpt), category))
    cursor, parts = 0, []
    for start, end, category in sorted(spans):
        require(start >= cursor, f"{label}: overlapping highlights")
        parts += [
            escape(source[cursor:start]),
            f'<mark class="{category}" title="{COLORS[category]}">{escape(source[start:end])}</mark>',
        ]
        cursor = end
    return "".join(parts) + escape(source[cursor:])


def table(value):
    value = obj(value, "table")
    columns = array(value.get("columns"), "table.columns", nonempty=True)
    rows = array(value.get("rows"), "table.rows", nonempty=True)
    head = "".join(f'<th scope="col">{escape(string(x, "column"))}</th>' for x in columns)
    body = []
    for row in rows:
        require(isinstance(row, list) and len(row) == len(columns), "table row width does not match columns")
        require(all(isinstance(cell, str) for cell in row), "table cells must be strings")
        body.append("<tr>" + "".join(f"<td>{escape(cell)}</td>" for cell in row) + "</tr>")
    return ('<div class="table-scroll" tabindex="0" role="region" aria-label="数据表">'
            f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table></div>")


def figure(row, directory):
    image = Path(field(row, "image"))
    require(not image.is_absolute() and not image.anchor, "image must be relative to the reading packet")
    path = (directory / image).resolve()
    require(path.is_relative_to(directory), "image must stay inside the reading packet directory")
    data = path.read_bytes()
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
    elif data.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    else:
        raise ValueError("only PNG and JPEG images can be embedded")
    return f'<figure><img src="data:{mime};base64,{enc(data)}" alt="{escape(field(row, "alt"))}"></figure>'


def passage(row, key, directory, coverage):
    kind = field(row, "kind")
    require(kind in {"paragraph", "figure", "table", "equation", "gap"}, f"{key}: unknown block type")
    require(kind != "gap" or coverage != "complete", f"{key}: a gap requires partial or excerpt coverage")
    locator = escape(field(row, "locator"))
    marks = row.get("highlights", [])
    if kind == "gap":
        require(not marks and "original" not in row, f"{key}: a gap cannot supply or mark source text")
        left = f'<div class="original"><span class="label">来源缺口</span><p>{escape(field(row, "note"))}</p></div>'
    else:
        original = highlighted(field(row, "original"), marks, key)
        label = "英文原文" if coverage != "excerpt" else "英文摘录"
        extra = ""
        if kind == "figure":
            extra = figure(row, directory)
        elif kind == "table":
            extra = table(row.get("table"))
        elif kind == "equation":
            extra = f'<pre aria-label="公式">{escape(field(row, "formula"))}</pre>'
        left = f'<div class="original" lang="en"><span class="label" lang="zh-CN">{label}</span><p>{original}</p>{extra}</div>'
        left += f'<div class="translation" lang="zh-CN"><span class="label">中文译文</span><p>{escape(field(row, "translation"))}</p></div>'
    note = obj(row.get("annotation"), f"{key}.annotation")
    tone = note.get("category", "")
    require(tone == "" or (isinstance(tone, str) and tone in COLORS), f"{key}: invalid annotation color")
    points = (
        ("function", "段落功能"), ("role", "逻辑角色"), ("technique", "论证技巧或证据缺口"),
    )
    description = "".join(f"<dt>{title}</dt><dd>{escape(field(note, name))}</dd>" for name, title in points)
    return (
        f'<div class="row" id="{key}"><div class="reading-column">'
        f'<div class="anchor"><a href="#{key}" aria-label="本段链接">¶</a> {locator}</div>'
        f'{left}</div><aside class="annotation {tone}" aria-label="中文批注">'
        f'<span class="label">中文批注</span><dl>{description}</dl></aside></div>'
    )


def backlinks(value, known, *, required=False):
    refs = array(value, "refs", nonempty=required)
    links = []
    for ref in refs:
        require(isinstance(ref, str) and ref in known, f"unresolved passage reference: {ref}")
        links.append(f'<a href="#{ref}">{escape(known[ref])}</a>')
    return ' <span class="backlinks">（' + " · ".join(links) + "）</span>" if links else ""


def render(packet, directory):
    packet, directory = obj(packet, "packet"), Path(directory).resolve()
    title, mode, coverage = (field(packet, key) for key in ("title", "mode", "coverage"))
    require(mode in {"full", "overview", "module", "trace", "evidence"}, "unknown analysis mode")
    require(coverage in {"complete", "partial", "excerpt", "focused"}, "unknown coverage")
    require((mode == "full" and coverage != "focused") or (mode != "full" and coverage != "complete"),
            "complete is for full reports; focused is for local modes")
    source = escape(field(packet, "source"))
    metadata = f'<p class="source">来源与覆盖范围：{source}</p>'
    if coverage != "complete":
        labels = {"partial": "部分阅读", "excerpt": "摘录与释义", "focused": "局部阅读"}
        metadata += f'<p class="status">{labels[coverage]}：{escape(field(packet, "coverage_note"))}</p>'
    course = packet.get("course")
    course = f"<p>课程：{escape(string(course, 'course'))}</p>" if course else ""
    navigation, sections, known = [], [], {}
    for section_number, value in enumerate(array(packet.get("sections"), "sections", nonempty=True), 1):
        section = obj(value, "section")
        section_id, name = f"section-{section_number}", escape(field(section, "title"))
        navigation.append(f'<a href="#{section_id}">{name}</a>')
        rows = []
        for row_number, value in enumerate(array(section.get("blocks"), "blocks", nonempty=True), 1):
            row = obj(value, "block")
            key = f"p-{section_number}-{row_number}"
            known[key] = field(row, "locator")
            rows.append(passage(row, key, directory, coverage))
        sections.append(f'<section id="{section_id}"><h2>{name}</h2>{"".join(rows)}</section>')
    overview = obj(packet.get("summary"), "summary")
    summary_rows = []
    for key, label in SUMMARY.items():
        item = obj(overview.get(key), key)
        text = escape(field(item, "text"))
        # A missing argument or unavailable source can be reported without fabricating a paragraph link.
        missing = item.get("unavailable", False)
        require(isinstance(missing, bool), f"{key}.unavailable must be boolean")
        require(not missing or (key == "rebuttal" or coverage != "complete"),
                f"{key}: unavailable is only for rebuttals or limited source material")
        refs = backlinks(item.get("refs", []), known, required=not missing)
        summary_rows.append(f"<dt>{label}</dt><dd>{text}{refs}</dd>")
    navigation.append('<a href="#argument">论证总览</a>')
    summary = f'<section id="argument" class="synthesis"><h2>论证结构总览</h2><dl>{"".join(summary_rows)}</dl></section>'
    stages = obj(packet.get("stages", {}), "stages")
    valid_ids = {str(i) for i in range(1, len(STAGES) + 1)}
    require(stages.keys() <= valid_ids, "unknown stage number")
    if mode == "full" and coverage == "complete":
        require(stages.keys() == valid_ids, "complete full reports require all eight stages")
    analysis = ""
    if stages:
        navigation.append('<a href="#analysis">深读分析</a>')
        items = []
        for ix, name in enumerate(STAGES, 1):
            blocks = stages.get(str(ix))
            if blocks is None and not (mode == "full" and coverage == "complete"):
                continue
            fragments = []
            for block in array(blocks, f"stage {ix}", nonempty=True):
                block = obj(block, f"stage {ix} block")
                if "table" in block:
                    fragments.append(table(block["table"]))
                else:
                    text = escape(field(block, "text"))
                    refs = backlinks(block.get("refs", []), known)
                    if block.get("answer"):
                        fragments.append(f"<details><summary>展开自测答案</summary><p>{text}{refs}</p></details>")
                    else:
                        fragments.append(f"<p>{text}{refs}</p>")
            items.append(f'<section class="stage"><h3>{ix}. {name}</h3>{"".join(fragments)}</section>')
        caption = "八阶段深读" if mode == "full" and stages.keys() == valid_ids else "深读分析（按覆盖范围）"
        analysis = (
            f'<section id="analysis"><h2>{caption}</h2><details><summary>展开{caption}</summary>'
            + "".join(items) + "</details></section>"
        )
    font_css, font_licenses = font_assets()
    return Template((ASSETS / "annotated-paper.html").read_text(encoding="utf-8")).substitute(
        title=escape(title), course=course, font_css=font_css, font_licenses=font_licenses,
        legend="".join(f'<li class="{key}">{name}</li>' for key, name in COLORS.items()),
        navigation="".join(navigation), metadata=metadata, sections="\n".join(sections),
        synthesis=summary, analysis=analysis,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path, help="UTF-8 JSON reading packet")
    parser.add_argument("output", type=Path, help="new .html file")
    args = parser.parse_args()
    try:
        require(args.output.suffix.lower() == ".html", "output must end in .html")
        packet = json.loads(args.packet.read_text(encoding="utf-8"))
        result = render(packet, args.packet.resolve().parent)
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(result)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Cannot render reading: {error}\n")
    print(args.output)


if __name__ == "__main__":
    main()
