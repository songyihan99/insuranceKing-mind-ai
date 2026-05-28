# -*- coding: utf-8 -*-
from pathlib import Path

lines = Path("main.py").read_text(encoding="utf-8").splitlines()
ns: dict = {}
chunk = lines[471:579] + lines[719:1084] + lines[1086:1103]
exec("import re\n" + "\n".join(chunk), ns)

sample = (
    '<div class="ai-section"><h4>진단</h4><p>균형형입니다.</p></div>'
    '<div class="ai-section"><h4>스토리</h4><p>1</p><p>2</p></div>'
)
assert ns["parse_limbic_axis_type"](sample) == "균형형"
assert "limbic-axis-card--active" in ns["build_limbic_axis_cards_html"]("균형형")
assert len(ns["_balanced_ai_section_blocks"](sample)) == 2
out = ns["apply_direct_ment_bold"](
    '<div class="ai-section"><h4>x</h4>'
    "【멘트】고객님 비교 기준만 확인해 보시죠.【/멘트】</div>"
)
assert "fp-ment-box" in out
prev, more = ns["_split_section_preview_and_more"]("<p>a</p><p>b</p>")
assert prev == "<p>a</p>" and more
print("ok")
