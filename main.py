from dotenv import load_dotenv

load_dotenv()

import os
import re
from pathlib import Path

import streamlit as st
from openai import OpenAI

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="한화손해 거절 처리 AI 비서",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 한화손해 시그니처 테마 CSS ─────────────────────────────────
st.markdown(
    """
<style>
    /* 전역 배경 & 폰트 */
    .stApp {
        background-color: #f5f5f5;
        font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
    }

    /* 사이드바 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f0f0f0 100%);
        border-right: 2px solid #ff6600;
    }
    [data-testid="stSidebar"] .stMarkdown h2 {
        color: #ff6600;
        font-weight: 700;
        border-bottom: 2px solid #ff6600;
        padding-bottom: 8px;
    }

    /* 메인 헤더 */
    .main-header {
        background: linear-gradient(135deg, #ff6600 0%, #e55a00 100%);
        color: white;
        padding: 20px 28px;
        border-radius: 12px;
        margin-bottom: 24px;
        box-shadow: 0 4px 15px rgba(255, 102, 0, 0.25);
    }
    .main-header h1 {
        margin: 0;
        font-size: 1.6rem;
        font-weight: 700;
    }
    .main-header p {
        margin: 6px 0 0;
        opacity: 0.92;
        font-size: 0.95rem;
    }

    /* 숏컷 버튼 영역 */
    .shortcut-label {
        color: #333;
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 8px;
    }

    /* TOP 5 숏컷 버튼 (5열 column 내부만 — 분석하기 primary 버튼 제외) */
    div[data-testid="column"] div[data-testid="stButton"] > button:not([kind="primary"]) {
        min-height: 75px !important;
        height: auto !important;
        word-break: keep-all !important;
        overflow-wrap: normal !important;
        white-space: normal !important;
        line-height: 1.35 !important;
        padding: 10px 6px !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        border-radius: 10px !important;
    }
    div[data-testid="column"] div[data-testid="stButton"] > button:not([kind="primary"]):hover {
        border-color: #ff6600 !important;
        color: #e85d00 !important;
        background-color: #fff8f2 !important;
    }

    /* 분석 버튼 강조 */
    div[data-testid="stButton"] > button[kind="primary"] {
        background-color: #ff6600 !important;
        border-color: #ff6600 !important;
        color: white !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        padding: 12px 32px !important;
        border-radius: 8px !important;
        width: 100%;
        transition: background 0.2s;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background-color: #e55a00 !important;
        border-color: #e55a00 !important;
    }

    /* 결과 패널 */
    .result-panel {
        background: linear-gradient(180deg, #ffffff 0%, #fafafa 100%);
        border-radius: 16px;
        padding: 28px 26px;
        border: 1px solid rgba(255, 102, 0, 0.18);
        box-shadow: 0 8px 28px rgba(255, 102, 0, 0.09), 0 2px 8px rgba(0,0,0,0.04);
        min-height: 400px;
    }
    .result-panel h3 {
        color: #1a1a1a;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin-top: 0;
    }
    .result-panel hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, #ff6600, rgba(255,102,0,0.15));
        margin: 14px 0 22px;
        border-radius: 2px;
    }

    /* AI 출력 루트 (한 블록 렌더링용) */
    .ai-section {
        background: linear-gradient(145deg, #fffefd 0%, #faf7f4 55%, #fff9f5 100%);
        border: 1px solid rgba(255, 102, 0, 0.2);
        border-left: 5px solid #ff6600;
        padding: 22px 24px;
        margin: 18px 0;
        border-radius: 14px;
        box-shadow: 0 4px 18px rgba(255, 102, 0, 0.07);
        font-size: 1.02rem;
        line-height: 1.78;
        color: #2a2a2a;
        word-break: keep-all;
        overflow-wrap: break-word;
    }
    .ai-section h4 {
        color: #e85d00;
        font-size: 1.12rem;
        font-weight: 800;
        margin: 0 0 14px 0;
        padding-bottom: 10px;
        border-bottom: 2px solid rgba(255, 102, 0, 0.28);
        letter-spacing: -0.02em;
    }
    .ai-section p {
        margin: 0 0 12px 0;
    }
    .ai-section ul {
        margin: 6px 0 4px 0;
        padding-left: 1.25rem;
    }
    .ai-section li {
        margin-bottom: 6px;
    }
    .ai-section strong {
        color: #cc5200;
        font-weight: 700;
    }

    /* 설계사 직접 멘트 — 파란 강조 박스 */
    .fp-ment-box {
        display: block;
        background: linear-gradient(135deg, #e8f4fc 0%, #d4ebfa 55%, #cfe8f9 100%);
        border: 1px solid #90caf9;
        border-left: 5px solid #1976d2;
        border-radius: 12px;
        padding: 14px 16px 16px 16px;
        margin: 14px 0;
        box-shadow: 0 3px 12px rgba(25, 118, 210, 0.12);
    }
    .fp-ment-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 10px;
        padding-bottom: 8px;
        border-bottom: 1px dashed rgba(25, 118, 210, 0.35);
    }
    .fp-ment-icon {
        font-size: 1.15rem;
        line-height: 1;
    }
    .fp-ment-label {
        font-size: 0.78rem;
        font-weight: 800;
        color: #1565c0;
        letter-spacing: -0.02em;
        text-transform: none;
    }
    .fp-ment-text {
        color: #0d47a1;
        font-size: 1.02rem;
        font-weight: 600;
        line-height: 1.75;
        word-break: keep-all;
    }
    .fp-ment-text p {
        margin: 0 0 8px 0;
        color: #0d47a1;
    }
    .fp-ment-text p:last-child {
        margin-bottom: 0;
    }

    /* 하단 고정 클로징 팁 박스 */
    .byaf-tip-box {
        background: linear-gradient(135deg, #fff5eb 0%, #ffe8d6 45%, #ffd4b8 100%);
        border: 2px solid #ff6600;
        border-radius: 14px;
        padding: 18px 22px;
        margin-top: 26px;
        color: #2c2c2c;
        font-size: 0.98rem;
        line-height: 1.72;
        box-shadow: 0 4px 16px rgba(255, 102, 0, 0.12);
    }
    .byaf-tip-box strong {
        color: #d35400;
    }

    /* 입력 구역 카드 */
    .input-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    /* 구역 라벨 */
    .zone-label {
        display: inline-block;
        background: #ff6600;
        color: white;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 20px;
        margin-bottom: 10px;
    }

    /* 림빅 6축 유형 카드 */
    .limbic-axis-cards {
        display: flex;
        flex-wrap: nowrap;
        gap: 10px;
        margin: 0 0 22px 0;
        width: 100%;
    }
    .limbic-axis-card {
        flex: 1 1 0;
        min-width: 0;
        text-align: center;
        padding: 14px 6px;
        border-radius: 12px;
        font-size: 0.92rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        border: 2px solid transparent;
    }
    .limbic-axis-card--active {
        background: linear-gradient(145deg, #ff6600 0%, #e55a00 100%);
        color: #ffffff;
        border-color: #ff6600;
        box-shadow: 0 6px 18px rgba(255, 102, 0, 0.35);
        transform: translateY(-2px);
    }
    .limbic-axis-card--inactive {
        background: #e8e8e8;
        color: #888888;
        border-color: #d0d0d0;
        box-shadow: none;
    }

    /* 섹션 더보기 접기 (스토리텔링·클로징·무기) */
    .ai-section-preview {
        margin: 0;
    }
    .ai-section-expand {
        margin-top: 10px;
    }
    .ai-section-expand-btn {
        display: inline-block;
        cursor: pointer;
        color: #ff6600;
        font-size: 0.92rem;
        font-weight: 700;
        padding: 6px 14px;
        border-radius: 20px;
        border: 1.5px solid #ff6600;
        background: #fff8f2;
        list-style: none;
        user-select: none;
        transition: background 0.15s ease, color 0.15s ease;
    }
    .ai-section-expand-btn::-webkit-details-marker {
        display: none;
    }
    .ai-section-expand-btn:hover {
        background: #ff6600;
        color: #ffffff;
    }
    .ai-section-expand[open] .ai-section-expand-btn {
        background: #f0f0f0;
        border-color: #cccccc;
        color: #666666;
    }
    .ai-section-expand[open] .ai-section-expand-btn:hover {
        background: #e0e0e0;
        color: #444444;
    }
    .ai-section-expand .expand-label-less {
        display: none;
    }
    .ai-section-expand[open] .expand-label-more {
        display: none;
    }
    .ai-section-more-body {
        margin-top: 4px;
        padding-top: 12px;
        border-top: 1px dashed rgba(255, 102, 0, 0.25);
    }

    [data-testid="stExpander"] {
        background: white;
        border-radius: 10px;
        border: 1px solid rgba(255, 102, 0, 0.2);
        margin: 8px 0;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ── OpenAI system 메시지 (대중 언어만 사용, 순수 HTML만 출력) ──
SYSTEM_INSTRUCTION = """
당신은 '보험왕'의 영업 노하우를 현장 설계사(FP)에게 이식하는 한화손해 **거절 처리 AI 비서**입니다.

## 【절대 금지·치환 규칙】 — 답변 본문·제목 어디에서도 다음 단어 금지
- 「림빅」「limbic」「Limbic」→ 금지. 같은 의미를 **완전히 다른 말**로 풀어서 써라(해당 단어 자체 포함 금지).
- 「바이란」「BYAF」「역설적 의도」→ 금지. 같은 의미를 **전혀 다른 일상 문장**으로 치환해 써라(해당 단어 자체 포함 금지).
- 학술·심리 전문 용어도 금지: 「방어기제」「편향」「오류」「기저」「확증」「손실 회피」「리액턴스」「반발」등.
  초등 학생도 이해하는 **생활 언어**로만 써라. 답변에서 “예시 문장”을 그대로 복사하지 말고, 매번 새로 써라.

## 6대 감정 축 분석 기준 (내부 판단용, 출력은 일상어로 풀어쓰기)
- 모험: 리스크를 감수하고 기회나 트렌드를 쫓는 쪽
- 지배: 주도권을 쥐고 싶어 하고 자기 판단을 강하게 믿는 쪽
- 통제/규율: 손해, 사기, 약관, 보험금 지급 여부를 꼼꼼하게 따지는 쪽
- 균형: 익숙한 상태를 유지하고 이미 있는 것을 바꾸기 싫어하는 쪽
- 자극: 당장 체감되는 실리, 가성비, 비용 부담을 가장 크게 보는 쪽
- 개방/관용: 관계를 중시하고 갈등을 피하려 하며 결정을 뒤로 미루는 쪽

- 반드시 위 6개 중 **최상위 감정 1가지만** 고른다.
- 출력에는 "가장 크게 움직이는 마음은 균형 쪽입니다"처럼 일상어로 풀어 쓴다.
- 특히 아래 표현은 우선 이렇게 본다:
  - "안 바꿀래", "이미 있다" → 균형
  - "보험료 부담", "비싸다" → 자극
  - "돈 아깝게 왜 새로" → 지배
  - "보험사들이 안 준다" → 통제/규율
  - "주식", "코인", "돈 묶이기 싫다" → 모험
  - 지인 관계 때문에 결정을 미루는 문맥 → 개방/관용

## 비조작적 커뮤니케이션 원칙
- 심리 조작, 가스라이팅, 편향 자극, 압박 판매를 유도하는 표현은 금지.
- 소비자의 알 권리, 이해 가능성, 자율적 선택을 최우선으로 둔다.
- 혜택만 강조하지 말고, 확인해야 할 기준·보장 범위·비용 부담을 함께 설명한다.
- 고객이 스스로 비교하고 판단할 수 있게 오해 포인트와 확인 포인트를 분명히 짚는다.

## 어투 (필수)
- **절대 추측하는 어투를 사용하지 말고 단정적으로 서술하라.**
- 금지 예: "~인 것 같습니다", "~것 같아요", "~것으로 보입니다", "~듯합니다", "~로 여겨집니다" 등 모호·추정 표현.
- 필수 예: "~입니다", "~습니다", "~해요"(대화체 구간만)처럼 확정형 종결만 사용하라.
- 진단·추천·설명 모두 현장 FP가 바로 읽고 쓸 수 있는 단정적 문장으로 써라.

## 출력 규칙 (반드시 HTML만 출력, 마크다운 금지)
- 응답은 오직 HTML 한 덩어리만. 앞뒤 설명·인사·백틱·코드펜스 전부 금지.
- 아래 4개 섹션을 각각 `<div class="ai-section">` … `</div>` 로 감싼다.
- 각 섹션 제목은 `<h4>` 한 줄로 딱 아래 문구와 일치하게 쓴다 (이모지 포함).

## 섹션별 출력 분량 (필수)
- **짧고 강하게 핵심만 써라. 설명이 길어질수록 설계사가 현장에서 못 쓴다. 한 섹션에 문장이 3개를 넘으면 안 된다.**
- 분량은 제목(`<h4>`)과 `fp-ment-box` 블록을 제외한 **본문 해설 문장**만 센다. 문장 1개는 `<p>` 1개 또는 `<li>` 1개로 끊어 써라.
- 섹션1(속마음 진단): 본문 **3문장 이내**
- 섹션2(스토리텔링): 본문 **3문장 이내**
- 섹션3(클로징): 본문 **2문장 이내**
- 섹션4(무기): **상품명 1문장 + 핵심특약 1문장 + 추천이유 1문장**만(각 1문장씩, 총 3문장). 장황한 나열·부가 설명 금지.

## 가독성·줄바꿈 설계 (필수)
- 결과 문장은 화면에서 단어 단위로 예쁘게 떨어지도록, 의미 덩어리(띄어쓰기 단위)를 기준으로 짧게 끊어 써라.
- 한 `<p>` 안에 너무 긴 문장 1개만 쓰지 말고, 2~3개의 짧은 문장으로 나눠 읽기 쉽게 구성하라.
- 한글 문장 중간에서 어색하게 한 글자만 다음 줄로 떨어지지 않게, 자연스러운 호흡으로 문장 길이를 조절하라.
- 나열이 필요하면 `<ul><li>`로 나누고, 각 항목도 한 줄에 다 넣지 말고 적당한 길이로 유지하라.
- 각 ai-section 본문은 스크롤 없이 한눈에 읽히도록 문단 간 여백을 살려 작성하라.

## 직접 멘트 박스 (필수 — 4개 섹션 공통)
- 설계사(FP)가 고객에게 **그대로 읽어 말할 문장**은 【멘트】 마커 없이, 아래 HTML을 **그대로** 출력한다(멘트 1덩어리당 박스 1개).
- `fp-ment-text` 안에는 **멘트 문장만** 넣고, 분석·해설·진단·상품 설명은 일반 `<p>` 텍스트만 쓴다.
- 고객 **거절 멘트 인용**, 오해/확인 포인트 설명은 박스에 넣지 마라.
- HTML 템플릿(클래스명·태그 구조 변경 금지, `멘트 내용`만 실제 멘트로 치환):

<div class="fp-ment-box">
<div class="fp-ment-header">
<span class="fp-ment-icon">💬</span>
<span class="fp-ment-label">설계사 직접 멘트</span>
</div>
<div class="fp-ment-text">멘트 내용</div>
</div>

- 섹션1: 진단 해설은 `<p>`. 고객에게 건넬 공감·확인 **대화 멘트**만 위 박스 HTML 사용.
- 섹션2·3: 사례·해설은 `<p>`. 설계사가 읽을 **대화체 멘트**만 위 박스 HTML 사용.
- 섹션4: 상품·특약 설명은 `<p>`. 고객에게 말할 **제안 멘트**만 위 박스 HTML 사용.

### 섹션 1 → `<h4>🔴 [고객의 진짜 속마음 진단]</h4>`
- 본문 해설은 **3문장 이내**로 압축한다(위 분량 규칙 준수).
- 거절 멘트로 위 6대 감정 축 중 가장 강하게 발동한 최상위 감정 1가지를 판정한다.
- 판정 유형은 **모험형·지배형·통제형·균형형·자극형·개방형** 중 정확한 이름 1개를 섹션1 본문에 반드시 1회 쓴다(예: `균형형`).
- 그 외 설명은 일상어로 풀되, 위 6개 유형명 이외의 축 이름(모험·규율 등 단독 표기)은 쓰지 마라.
- 고객 프로필(이름, 나이, 직업)을 콕 집어 개인 맞춤으로 진단 (과장·조롱 없이).
- 반드시 고객이 주저하는 이유를 `오해 포인트`와 `확인 포인트`로 나눠 투명하게 짚는다.
- 바넘 효과처럼 두루뭉술한 단정 대신, 정교한 맞춤형 공감으로 설명한다.
- 고객에게 말할 직접 멘트만 위 fp-ment-box HTML로 출력(위 규칙 준수).

### 섹션 2 → `<h4>🧠 [신뢰를 구축하는 1초 스토리텔링]</h4>`
- 본문 해설은 **3문장 이내**로 압축한다(위 분량 규칙 준수).
- 설계사가 그대로 읽을 대화체 멘트는 모두 fp-ment-box HTML로 출력한다.
- 정형화된 서술형 문장(훈계·교과서 톤) 절대 금지.
- 고객의 나이·성별·직업·현재 제안 상품군·거절 이유에 맞춘 가족 또는 직계 지인의 리모델링 경험을 떠올리게 하는 체험형 사례, 또는 익명화된 유사 사례를 매번 새로 구성하라.
- 질병/사고 공포를 자극하거나 비극을 과장하지 말고, "어떻게 보장의 빈틈을 점검하고 자산을 안정적으로 방어했는지"에 초점을 둔다.
- 실화처럼 단정하기보다 "비슷한 경우를 보면", "가까운 분들 사례를 설명드리면"처럼 오해 없는 표현을 사용한다.
- 사례는 월 보험료 부담, 이미 가입한 보장과의 차이, 운전 습관, 고지 걱정, 기존 보장의 빈틈처럼 실제 비교에 필요한 판단 요소를 중심으로 짧고 선명하게 풀어라.
- 과장, 죄책감 유발, 겁주기 표현 없이 공감형 톤으로 설명하라.
- 숫자·통계·나열형 문장 금지.
- 같은 문장(또는 거의 같은 문장)을 반복하지 말고, 첫 문장부터 끝문장까지 리듬을 매번 바꿔라.
- 마지막 한두 문장은 고객이 스스로 비교 판단할 수 있게 “무엇을 확인하면 되는지”를 자연스럽게 짚어라.

### 섹션 3 → `<h4>💸 [부담을 0으로 만드는 쿨한 클로징]</h4>`
- 본문 해설은 **2문장 이내**로 압축한다(위 분량 규칙 준수).
- 먼저 비용 비교의 기준점을 투명하게 제시한다. 예: 현재 내는 보험료 대비 비어 있는 보장, 같은 월 부담 안에서 보완 가능한 항목, 기존 보장과 새 제안의 차이.
- 실제 보험료를 모르면 금액을 지어내지 말고, 월 부담 수준과 보장 범위를 비교하는 기준만 설명한다.
- 고객이 가격 저항을 이해할 수 있도록 "왜 이 비용이 추가 지출이 아니라 보장 구조 점검인지"를 담백하게 풀어라.
- 마지막은 반드시 자율 선택을 보장하는 대화체로 마무리하라. 예: 다른 회사와 비교해도 괜찮고, 다만 어떤 기준만은 꼭 확인해 보시라는 식의 중립적 안내.
- 고객에게 읽을 클로징 멘트는 fp-ment-box HTML로 출력, 비용 비교 해설은 일반 텍스트.
- 가입 독촉, 압박, 조급함 유도는 금지.
- 매번 문장 길이/끊어 읽기/멘트 배치를 바꿔서, 복붙 같은 느낌이 나지 않게 써라.

### 섹션 4 → `<h4>🟢 [한화손해만의 치명적인 무기]</h4>`
- 본문 해설은 **상품명 1문장 + 핵심특약 1문장 + 추천이유 1문장**만 쓴다(각 1문장, 총 3문장).
- 반드시 "한화 실시간 상품 장부 데이터"의 **[최종 매칭 후보 - 섹션4 전용]** 블록에 있는 상품만 추천한다. 다른 카테고리 상품은 절대 끌어오지 마라.
- 장부에 안내된 **2단계 필터링**을 그대로 따른다:
  * 1차: 확정 상품 카테고리와 일치하는 상품만 후보로 인정.
  * 2차: 그중 `[Priority: High]` 마킹 상품만 최종 전략 상품으로 우선 추천.
- 동일 카테고리에 `Priority: High` 상품이 여러 개면, 거절 맥락에 맞는 것 1~2개를 골라 각각 설명하라.
- 해당 카테고리에 High 상품이 없을 때만, 같은 카테고리의 [참고 후보]에서 1개를 보조로 언급할 수 있다.
- 운전자/생활종합 거절 맥락에 여성 건강보험을 넣거나, 암보험 거절 맥락에 운전자보험을 넣는 등 **카테고리 불일치 추천은 금지**.
- 고객 프로필(나이·성별·직업) + 거절 멘트 + 확정 카테고리가 서로 맞는지 스스로 검증한 뒤 작성하라.
- 아래 3가지를 반드시 포함해 작성:
  1) 추천 상품명
  2) 핵심 특약 명칭
  3) 왜 이 특약이 해당 거절·카테고리 맥락에 맞는지(고객 프로필 맞춤 이유)
- `Priority: High` 상품은 장부 매칭 근거와 고객 맥락에 맞는 추천 이유만 설명하라.
- 장부 기반 근거를 짧고 강하게 제시한다. 가입 압박은 금지.
- 고객에게 말할 제안 멘트는 fp-ment-box HTML로 출력, 상품·특약 설명 문장은 일반 텍스트.

## 금지 사항
- 마크다운 문법(해시태그 헤더, 별표 강조, 코드펜스) 사용 금지 — 순수 HTML만
- 뻔한 통계 나열 금지
- 가입 독촉·압박 금지
- 심리 조작, 가스라이팅, 편향 자극 표현 금지
- **「본사 전략 우선 상품으로도 분류됩니다」** 및 이와 유사한 표현 전부 금지
  (예: "본사 전략 우선 상품", "전략 우선 상품으로 분류", "우선 전략 상품입니다" 등 — 출력에 한 글자도 넣지 마라)
- `direct-ment` 및 깨진 HTML 태그 조각(열리지 않은 `>` 잔여 등) 출력 금지. fp-ment-box는 위 템플릿 구조로만 출력.
"""

LIMBIC_AXIS_TYPES = ("모험형", "지배형", "통제형", "균형형", "자극형", "개방형")

LIMBIC_TYPE_MARKER_RE = re.compile(
    r"【\s*유형\s*:\s*(모험형|지배형|통제형|균형형|자극형|개방형)\s*】"
)
LIMBIC_TYPE_WORD_RE = re.compile(
    r"(모험형|지배형|통제형|균형형|자극형|개방형)"
)

AI_SECTION_BLOCK_RE = re.compile(
    r'<div\s+class=["\']ai-section["\']\s*>(.*?)</div>',
    re.DOTALL | re.IGNORECASE,
)
AI_SECTION_OPEN_RE = re.compile(
    r'<div\s+class=["\']ai-section["\']\s*>',
    re.IGNORECASE,
)
AI_SECTION_H4_RE = re.compile(r"(<h4>.*?</h4>)", re.DOTALL | re.IGNORECASE)
AI_SECTION_CONTENT_UNIT_RE = re.compile(
    r"<p[^>]*>.*?</p>|<li[^>]*>.*?</li>",
    re.DOTALL | re.IGNORECASE,
)
COLLAPSIBLE_SECTION_TITLES = (
    "신뢰를 구축하는 1초 스토리텔링",
    "부담을 0으로 만드는 쿨한 클로징",
    "한화손해만의 치명적인 무기",
)
COLLAPSIBLE_PREVIEW_LINES = 1

# 추측 어투 → 단정 어투 (긴 패턴·구체 패턴을 먼저 적용)
HEDGING_TONE_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("인 것 같습니다", "입니다"),
    ("인 것 같아요", "입니다"),
    ("인 것으로 보입니다", "입니다"),
    ("인 것 같다", "이다"),
    ("그런 것으로 보입니다", "그렇습니다"),
    ("그런 것 같습니다", "그렇습니다"),
    ("그런 것 같아요", "그렇습니다"),
    ("하는 것으로 보입니다", "합니다"),
    ("하는 것 같습니다", "합니다"),
    ("하는 것 같아요", "합니다"),
    ("되는 것으로 보입니다", "됩니다"),
    ("되는 것 같습니다", "됩니다"),
    ("되는 것 같아요", "됩니다"),
    ("는 것 같습니다", "습니다"),
    ("는 것 같아요", "습니다"),
    ("은 것 같습니다", "습니다"),
    ("을 것 같습니다", "습니다"),
    ("것으로 보입니다", "습니다"),
    ("것 같습니다", "습니다"),
    ("것 같아요", "습니다"),
)

DIRECT_MENT_STRONG_RE = re.compile(
    r"<strong[^>]*\bdirect-ment\b[^>]*>(.*?)</strong>",
    re.DOTALL | re.IGNORECASE,
)
DIRECT_MENT_STRONG_OPEN_RE = re.compile(
    r"<strong[^>]*\bdirect-ment\b[^>]*>",
    re.IGNORECASE,
)
DIRECT_MENT_ARTIFACT_RE = re.compile(
    r'direct-ment\s*>|class=["\']direct-ment["\']|\bdirect-ment\b',
    re.IGNORECASE,
)
FP_MENT_BOX_MARKER = "설계사 직접 멘트"
FP_MENT_BOX_BLOCK_RE = re.compile(
    r'<div\s+class=["\']fp-ment-box["\']\s*>[\s\S]*?</div>\s*</div>\s*</div>',
    re.IGNORECASE,
)
H4_PAREN_SUBTITLE_RE = re.compile(
    r"(<h4>[^<]+?)\s*\([^)]*\)(\s*</h4>)",
    re.IGNORECASE,
)
HTML_ARTIFACT_RE = re.compile(
    r"(?:ai-section-[a-z-]+)\s*\">|"
    r"\bdirect-ment\b\s*>",
    re.IGNORECASE,
)
ORPHAN_GT_RE = re.compile(r"(?<=[가-힣0-9%])\s*>\s+(?=[가-힣「『\"])")

FP_MENT_ANALYSIS_KEYWORDS = (
    "오해 포인트",
    "확인 포인트",
    "분석:",
    "진단",
    "추천 상품",
    "핵심 특약",
    "거절 멘트",
    "【유형",
    "유형:",
    "모험형",
    "지배형",
    "통제형",
    "균형형",
    "자극형",
    "개방형",
)

DASHBOARD_HTML = (
    "<h3>🎯 AI 거절 처리 가이드: "
    "<span style='color:#d32f2f;'>🔴 속마음 방어벽 해제 완료</span> / "
    "<span style='color:#2e7d32;'>🟢 맞춤형 현장 멘트 제공</span></h3>"
    "<hr>"
)

CLOSING_TIP_HTML = """
<div class="byaf-tip-box">
    💡 <strong>[AI 비서의 클로징 팁]:</strong>
    가입을 재촉하기보다, 고객이 비교할 기준과 확인할 포인트를 분명히 알려주고 선택권을 존중해 주세요.
    오해 없는 설명과 자율적인 비교 기회가 신뢰를 만들고 더 좋은 결정을 돕습니다.
</div>
"""

DEFAULT_WEAPON_TEXT = """
[기본 무기] 상품명: 무배당 한화 시그니처 여성 건강보험 4.0
- 추천 타깃: 20대~40대 여성 고객
- 핵심 특약: 부위별 최대 11회 지급 [통합암 진단비]
- 셀링 포인트: 암 발생 부위별로 반복 보장해, 1회 지급 후 끝나는 일반 구조 대비 실전 방어력이 높습니다.
""".strip()

WEAPON_FILE_PATH = Path("knowledge") / "hanwha_weapons.txt"

# (버튼 라벨, 입력창에 채울 긴 거절 멘트) — 상품군별 5종 세트
SHORTCUT_PROFILES: dict[str, list[tuple[str, str]]] = {
    "선택 안 함 (AI 자동 추론)": [
        (
            "지인 암보험 있어",
            "나 이미 지인한테 가입한 암보험 든든한 거 있어서 안 바꿀래~",
        ),
        (
            "매달 보험료 부담돼",
            "매달 나가는 보험료 너무 부담돼서 새로 가입 안 해!",
        ),
        (
            "무사고면 충분해",
            "평생 사고 한 번 안 났는데, 운전자 보험을 돈 아깝게 왜 새로 들어?",
        ),
        (
            "보험금 안 줄거야",
            "보험사들 큰 병 걸리면 핑계 대면서 돈 안 주려고 버틴다던데?",
        ),
        (
            "그 돈 주식할래",
            "지금 주식이나 코인으로 굴리기도 바쁜데, 묶이는 보험에 돈 쓰기 아까워.",
        ),
    ],
    "암/여성 건강보험": [
        (
            "친척 암보험 있어",
            "나 이미 친척한테 가입한 암보험 든든한 거 있어서 안 바꿀래~",
        ),
        (
            "매달 보험료 부담돼",
            "매달 나가는 보험료가 너무 부담돼서, 암보험 새로 가입은 안 할 것 같아요.",
        ),
        (
            "암 확률 낮을걸?",
            "솔직히 암 걸릴 확률이 그렇게 높겠어? 굳이 또 들 필요 없을 것 같아요.",
        ),
        (
            "보험금 잘 안 줘",
            "보험사들 암 걸리면 핑계 대면서 보험금 잘 안 준다고 하더라고요, 그래서 의미 없어요.",
        ),
        (
            "그 돈 주식할래",
            "차라리 그 돈으로 주식이나 투자에 넣는 게 나을 것 같아요, 보험에 묶기 아까워요.",
        ),
    ],
    "운전자/생활종합": [
        (
            "지인 보험 있어",
            "지인이 이미 들어준 운전자 보험 있는데, 또 새로 들 필요 없어요.",
        ),
        (
            "만원도 아까워",
            "만원짜리 보험료도 아까워요. 매달 나가는 거 부담돼서 그냥 안 할래요.",
        ),
        (
            "평생 무사고야",
            "평생 사고 한 번도 없었는데, 운전자 보험 새로 들 이유가 없어요.",
        ),
        (
            "자보험으로 돼",
            "기본 자동차 보험만 있어도 다 되는 거 아니에요? 따로 또 들 필요 없죠.",
        ),
        (
            "운전 거의 안 해",
            "운전 자주 안 해서 굳이 운전자 보험까지 들 필요 없다고 생각해요.",
        ),
    ],
    "유병자 간편보험": [
        (
            "예전 아팠어 거절",
            "예전에 아팠던 적 있어서 가입도 안 되고, 들어봤자 소용없을 것 같아요.",
        ),
        (
            "아픈 사람용 비싸",
            "아픈 사람 전용 보험은 너무 비싸고, 제가 감당하기 부담돼요.",
        ),
        (
            "나이 들어 늦었어",
            "나이도 들었는데 이제 와서 무슨 보험이에요, 늦은 것 같아요.",
        ),
        (
            "서류 심사 귀찮아",
            "서류 떼고 심사받는 것도 귀찮고 번거로워서, 그냥 안 할래요.",
        ),
        (
            "아프면 내 돈 쓸래",
            "그냥 아프면 내 돈으로 치료하면 되지, 보험 들 필요 없어요.",
        ),
    ],
}

PRODUCT_GROUP_KEY_SLUG = {
    "선택 안 함 (AI 자동 추론)": "auto",
    "암/여성 건강보험": "cancer",
    "운전자/생활종합": "driver",
    "유병자 간편보험": "simplified",
}

PRODUCT_GROUP_OPTIONS = [
    "선택 안 함 (AI 자동 추론)",
    "암/여성 건강보험",
    "운전자/생활종합",
    "유병자 간편보험",
]


def get_shortcuts_for_product_group(product_group: str) -> list[tuple[str, str]]:
    """사이드바 상품군 선택값에 맞는 숏컷 버튼·멘트 세트를 반환한다."""
    return SHORTCUT_PROFILES.get(
        product_group,
        SHORTCUT_PROFILES["선택 안 함 (AI 자동 추론)"],
    )


def extract_diagnosis_section_html(ai_html: str) -> str:
    """첫 번째 ai-section(속마음 진단) 구간만 추출한다."""
    lower = ai_html.lower()
    start = lower.find('class="ai-section"')
    if start == -1:
        return ai_html

    content_start = ai_html.find(">", start)
    if content_start == -1:
        return ai_html

    content_start += 1
    next_section = lower.find('class="ai-section"', content_start)
    if next_section == -1:
        return ai_html[content_start:]
    return ai_html[content_start:next_section]


def _html_to_plain_text(html: str) -> str:
    """HTML 태그를 제거하고 유형 단어 검색용 평문을 만든다."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _ordered_unique_limbic_types(text: str) -> list[str]:
    """평문에서 등장 순서대로 유일한 유형 단어(모험형 등) 목록을 반환한다."""
    seen: set[str] = set()
    ordered: list[str] = []
    for match in LIMBIC_TYPE_WORD_RE.finditer(text):
        type_name = match.group(1)
        if type_name not in seen:
            seen.add(type_name)
            ordered.append(type_name)
    return ordered


def _pick_primary_limbic_type(plain: str) -> str | None:
    """여러 유형이 섞여 있어도 판정 문맥 또는 첫 등장 유형 하나를 고른다."""
    if not plain:
        return None
    for type_name in LIMBIC_AXIS_TYPES:
        if re.search(
            rf"(?:유형|판정|해당|최상위|분류|경향)[^。\n]{{0,32}}{re.escape(type_name)}",
            plain,
        ):
            return type_name
        if re.search(
            rf"{re.escape(type_name)}\s*(?:입니다|이니다|으로|임|에 해당|쪽|에 가깝)",
            plain,
        ):
            return type_name
    ordered = _ordered_unique_limbic_types(plain)
    return ordered[0] if ordered else None


def parse_limbic_axis_type(ai_html: str) -> str | None:
    """AI 응답에서 6축 유형 단어(모험형·지배형 등)만 찾아 카드 하이라이트용으로 반환한다."""
    if not (ai_html or "").strip():
        return None

    marker_match = LIMBIC_TYPE_MARKER_RE.search(ai_html)
    if marker_match:
        return marker_match.group(1)

    # ai-section 인용부호 형태(" 또는 ')에 상관없이 진단 구간을 우선 탐색
    section_match = re.search(
        r"<div\s+class=[\"']ai-section[\"']\s*>",
        ai_html,
        flags=re.IGNORECASE,
    )
    if section_match:
        diagnosis_html = ai_html[section_match.start() :]
    else:
        diagnosis_html = extract_diagnosis_section_html(ai_html)

    # HTML 원문에서 먼저 직접 탐색(태그 제거 과정의 손실 방지)
    diagnosis_html_match = LIMBIC_TYPE_WORD_RE.search(diagnosis_html)
    if diagnosis_html_match:
        return diagnosis_html_match.group(1)

    diagnosis_plain = _html_to_plain_text(diagnosis_html)
    diagnosis_primary = _pick_primary_limbic_type(diagnosis_plain)
    if diagnosis_primary:
        return diagnosis_primary

    full_html_match = LIMBIC_TYPE_WORD_RE.search(ai_html)
    if full_html_match:
        return full_html_match.group(1)

    full_plain = _html_to_plain_text(ai_html)
    full_primary = _pick_primary_limbic_type(full_plain)
    if full_primary:
        return full_primary

    return None


def strip_limbic_type_marker(ai_html: str) -> str:
    """화면 표시용 — 파싱용 유형 마커 문구를 제거한다."""
    return LIMBIC_TYPE_MARKER_RE.sub("", ai_html)


def build_limbic_axis_cards_html(active_type: str | None) -> str:
    """6축 유형 카드 HTML — 감지된 유형만 오렌지 하이라이트, 미감지 시 전부 비활성."""
    cards: list[str] = []
    highlight = None
    if active_type:
        normalized = active_type.strip()
        if normalized in LIMBIC_AXIS_TYPES:
            highlight = normalized
        else:
            fallback_match = LIMBIC_TYPE_WORD_RE.search(normalized)
            if fallback_match:
                highlight = fallback_match.group(1)
    for type_name in LIMBIC_AXIS_TYPES:
        is_active = highlight is not None and highlight == type_name
        state_class = (
            "limbic-axis-card--active" if is_active else "limbic-axis-card--inactive"
        )
        cards.append(
            f'<div class="limbic-axis-card {state_class}">{type_name}</div>'
        )
    return f'<div class="limbic-axis-cards">{"".join(cards)}</div>'


def _is_collapsible_ai_section(section_inner: str) -> bool:
    return any(title in section_inner for title in COLLAPSIBLE_SECTION_TITLES)


def _extract_ai_section_content_units(body: str) -> list[str]:
    """본문에서 문단(p)·목록(li)·직접 멘트 박스 단위로 줄을 추출한다."""
    indexed: list[tuple[int, str]] = []
    for match in AI_SECTION_CONTENT_UNIT_RE.finditer(body):
        indexed.append((match.start(), match.group(0)))
    for match in FP_MENT_BOX_BLOCK_RE.finditer(body):
        indexed.append((match.start(), match.group(0)))
    indexed.sort(key=lambda item: item[0])

    box_spans = [
        (start, start + len(text))
        for start, text in indexed
        if "fp-ment-box" in text or FP_MENT_BOX_MARKER in text
    ]
    units: list[str] = []
    for start, text in indexed:
        if "fp-ment-box" in text or FP_MENT_BOX_MARKER in text:
            units.append(text)
            continue
        if any(box_start <= start < box_end for box_start, box_end in box_spans):
            continue
        units.append(text)
    return units


def apply_definitive_tone(text: str) -> str:
    """추측 어투(것 같습니다 등)를 단정 어투(입니다/습니다)로 일괄 교체한다."""
    result = text
    for old, new in HEDGING_TONE_REPLACEMENTS:
        result = result.replace(old, new)
    return result


def _strip_nested_ment_tags(inner: str) -> str:
    """멘트 본문 안의 중첩 strong·깨진 direct-ment 잔여물을 정리한다."""
    cleaned = DIRECT_MENT_STRONG_RE.sub(r"\1", inner)
    cleaned = DIRECT_MENT_STRONG_OPEN_RE.sub("", cleaned)
    cleaned = re.sub(r"</strong>", "", cleaned, flags=re.IGNORECASE)
    cleaned = DIRECT_MENT_ARTIFACT_RE.sub("", cleaned)
    return cleaned.strip()


def build_fp_ment_box(ment_text: str) -> str:
    """설계사 직접 멘트를 💬 파란 강조 박스 HTML로 만든다."""
    inner = _strip_nested_ment_tags(ment_text)
    if not inner:
        return ""
    if re.search(r'class=["\']fp-ment-box["\']', inner, re.IGNORECASE):
        return inner
    return (
        '<div class="fp-ment-box">'
        '<div class="fp-ment-header">'
        '<span class="fp-ment-icon" aria-hidden="true">💬</span>'
        f'<span class="fp-ment-label">{FP_MENT_BOX_MARKER}</span>'
        "</div>"
        f'<div class="fp-ment-text">{inner}</div>'
        "</div>"
    )


def _sanitize_direct_ment_artifacts(html: str) -> str:
    """깨진 direct-ment 태그만 정리하고, 유효한 멘트는 박스로 변환한다."""
    result = DIRECT_MENT_STRONG_RE.sub(
        lambda m: build_fp_ment_box(m.group(1))
        if _is_fp_direct_speech(m.group(1))
        else m.group(1),
        html,
    )
    result = DIRECT_MENT_STRONG_OPEN_RE.sub("", result)
    result = DIRECT_MENT_ARTIFACT_RE.sub("", result)
    return result


def _is_analysis_or_rejection_text(text: str) -> bool:
    """분석·라벨·고객 거절 멘트인지 판별한다."""
    plain = _html_to_plain_text(text).strip()
    if not plain:
        return True
    if any(keyword in plain for keyword in FP_MENT_ANALYSIS_KEYWORDS):
        return True
    if re.search(
        r"안 (?:바꿀|할|들|해|할래)|(?:부담|아까|싫어|필요 없|늦었|안 할|안 해)|"
        r"(?:있어서|된다던데|안 준|그냥 )|왜 (?:새로|또 )",
        plain,
    ):
        return True
    if re.search(r"^[「『\"']", plain) and re.search(
        r"(?:안 |못 |싫|아까|부담)", plain
    ):
        return True
    return False


def _is_fp_direct_speech(text: str) -> bool:
    """설계사가 고객에게 직접 말하는 멘트인지 판별한다."""
    if _is_analysis_or_rejection_text(text):
        return False
    plain = _html_to_plain_text(text).strip()
    if len(plain) < 10:
        return False
    if re.search(r"고객님", plain):
        return True
    if re.search(
        r"(?:설명|말씀|드리|여쭤|보시|확인|비교|추천|안내|제안)",
        plain,
    ) and re.search(r"(?:세요|해요|습니다|드릴게요|보시죠|까요|죠)[.!?]?$", plain):
        return True
    # 큰따옴표 등 10자 이상·분석/거절 키워드 없음 → 설계사 직접 멘트
    return True


def _apply_fp_ment_boxes_in_section_body(body: str, header: str) -> str:
    """섹션 본문의 깨진 direct-ment 잔여만 정리(AI가 fp-ment-box HTML 직접 출력)."""
    return _sanitize_direct_ment_artifacts(body)


def strip_section_h4_subtitles(ai_html: str) -> str:
    """섹션 h4 제목의 괄호 부제목을 제거한다."""
    return H4_PAREN_SUBTITLE_RE.sub(r"\1\2", ai_html)


def repair_ai_html_display(html: str) -> str:
    """깨진 HTML 조각·고아 > 기호만 정리한다(유효 class명은 유지)."""
    result = HTML_ARTIFACT_RE.sub("", html)
    result = ORPHAN_GT_RE.sub(" ", result)
    return result


def _balanced_ai_section_blocks(html: str) -> list[tuple[int, int, str]]:
    """중첩 div(fp-ment-box 등)를 고려해 ai-section 블록 전체를 추출한다."""
    blocks: list[tuple[int, int, str]] = []
    for match in AI_SECTION_OPEN_RE.finditer(html):
        start = match.start()
        pos = match.end()
        depth = 1
        while pos < len(html) and depth > 0:
            next_open = html.lower().find("<div", pos)
            next_close = html.lower().find("</div>", pos)
            if next_close == -1:
                break
            if next_open != -1 and next_open < next_close:
                depth += 1
                pos = html.find(">", next_open) + 1
            else:
                depth -= 1
                pos = next_close + len("</div>")
                if depth == 0:
                    blocks.append((start, pos, html[start:pos]))
                    break
    return blocks


def _inner_from_ai_section_block(block: str) -> str:
    open_match = AI_SECTION_OPEN_RE.search(block)
    if not open_match:
        return block
    close_idx = block.lower().rfind("</div>")
    if close_idx == -1:
        return block[open_match.end() :].strip()
    return block[open_match.end() : close_idx].strip()


def apply_direct_ment_bold(ai_html: str) -> str:
    """각 ai-section 직접 멘트를 💬 파란 강조 박스로 표시한다."""
    section_blocks = _balanced_ai_section_blocks(ai_html)
    if not section_blocks:
        def transform_section(match: re.Match[str]) -> str:
            inner = match.group(1)
            h4_match = AI_SECTION_H4_RE.search(inner)
            if not h4_match:
                return match.group(0)
            header = h4_match.group(1)
            section_body = inner[h4_match.end() :]
            return (
                f'<div class="ai-section">{header}'
                f"{_apply_fp_ment_boxes_in_section_body(section_body, header)}</div>"
            )

        return AI_SECTION_BLOCK_RE.sub(transform_section, ai_html)

    rebuilt: list[str] = []
    cursor = 0
    for start, end, block in section_blocks:
        rebuilt.append(ai_html[cursor:start])
        inner = _inner_from_ai_section_block(block)
        h4_match = AI_SECTION_H4_RE.search(inner)
        if not h4_match:
            rebuilt.append(block)
        else:
            header = h4_match.group(1)
            section_body = inner[h4_match.end() :]
            rebuilt.append(
                f'<div class="ai-section">{header}'
                f"{_apply_fp_ment_boxes_in_section_body(section_body, header)}</div>"
            )
        cursor = end
    rebuilt.append(ai_html[cursor:])
    return "".join(rebuilt)


def _split_section_preview_and_more(body: str) -> tuple[str, str | None]:
    """접을 섹션 본문을 미리보기·더보기 구간으로 나눈다."""
    units = _extract_ai_section_content_units(body)
    if not units:
        return body, None

    preview_html = "".join(units[:COLLAPSIBLE_PREVIEW_LINES])
    more_html = "".join(units[COLLAPSIBLE_PREVIEW_LINES:])

    remainder = body
    for unit in units:
        remainder = remainder.replace(unit, "", 1)
    remainder = remainder.strip()
    if remainder:
        more_html = remainder + more_html

    if not more_html:
        return body, None

    return preview_html, more_html


def _render_ai_section(inner: str, section_idx: int) -> None:
    """ai-section 1개를 전체 본문 그대로 렌더링한다."""
    h4_match = AI_SECTION_H4_RE.search(inner)
    if not h4_match:
        st.markdown(
            f'<div class="ai-section">{inner}</div>',
            unsafe_allow_html=True,
        )
        return

    header = h4_match.group(1)
    body = _apply_fp_ment_boxes_in_section_body(
        inner[h4_match.end():].strip(), header
    )
    st.markdown(
        f'<div class="ai-section">{header}{body}</div>',
        unsafe_allow_html=True,
    )


def render_analysis_result(ai_body: str, limbic_cards_html: str) -> None:
    if not (ai_body or "").strip():
        return
    st.markdown(
        f'{DASHBOARD_HTML}{limbic_cards_html}',
        unsafe_allow_html=True,
    )
    section_blocks = _balanced_ai_section_blocks(ai_body)
    if section_blocks:
        for section_idx, (_start, _end, block) in enumerate(section_blocks):
            _render_ai_section(_inner_from_ai_section_block(block), section_idx)
    else:
        st.markdown(
            f'<div class="ai-section">{ai_body}</div>',
            unsafe_allow_html=True,
        )
    st.markdown(CLOSING_TIP_HTML, unsafe_allow_html=True)

def render_ai_result_html(html_content: str, height: int = 1280) -> None:
    """분석 결과 HTML을 iframe으로 렌더링(Streamlit 마크다운 태그 제한 회피)."""
    document = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<style>"
        "body{margin:0;padding:8px 4px;font-family:'Malgun Gothic','Apple SD Gothic Neo',sans-serif;"
        "background:transparent;}"
        ".result-panel{background:linear-gradient(180deg,#fff 0%,#fafafa 100%);"
        "border-radius:16px;padding:24px 22px;"
        "border:1px solid rgba(255,102,0,0.18);"
        "box-shadow:0 8px 28px rgba(255,102,0,0.09);}"
        ".ai-output-root .ai-section{background:linear-gradient(145deg,#fffefd 0%,#faf7f4 55%,#fff9f5 100%);"
        "border:1px solid rgba(255,102,0,0.2);border-left:5px solid #ff6600;"
        "padding:22px 24px;margin:18px 0;border-radius:14px;line-height:1.78;color:#2a2a2a;}"
        ".ai-output-root .ai-section h4{color:#e85d00;font-size:1.12rem;font-weight:800;"
        "margin:0 0 14px;padding-bottom:10px;border-bottom:2px solid rgba(255,102,0,0.28);}"
        ".ai-output-root .ai-section p{margin:0 0 12px;}"
        ".ai-output-root .ai-section strong{color:#cc5200;font-weight:700;}"
        ".limbic-axis-cards{display:flex;gap:10px;margin:0 0 22px;}"
        ".limbic-axis-card{flex:1;text-align:center;padding:14px 6px;border-radius:12px;"
        "font-weight:700;font-size:0.92rem;}"
        ".limbic-axis-card--active{background:linear-gradient(145deg,#ff6600,#e55a00);"
        "color:#fff;border:2px solid #ff6600;}"
        ".limbic-axis-card--inactive{background:#e8e8e8;color:#888;border:2px solid #d0d0d0;}"
        ".byaf-tip-box{background:linear-gradient(135deg,#fff5eb,#ffe8d6);"
        "border:2px solid #ff6600;border-radius:14px;padding:18px 22px;margin-top:26px;}"
        "</style></head><body>"
        f"{html_content}"
        "</body></html>"
    )
    components.html(document, height=height, scrolling=True)


def strip_code_fences(text: str) -> str:
    """모델이 코드 블록(백틱 3개)으로 감싼 경우 제거해 순수 HTML만 남김."""
    s = text.strip()
    if s.startswith("```"):
        first_nl = s.find("\n")
        if first_nl != -1:
            s = s[first_nl + 1 :].strip()
        else:
            s = s[3:].strip()
    if s.rstrip().endswith("```"):
        s = s[: s.rfind("```")].strip()
    return s


def load_hanwha_weapons() -> tuple[str, bool, str]:
    """장부 파일을 읽고 실패 시 기본 특약으로 폴백한다."""
    try:
        if not WEAPON_FILE_PATH.exists():
            return (
                DEFAULT_WEAPON_TEXT,
                False,
                f"장부 파일이 없어 기본 특약으로 분석합니다: {WEAPON_FILE_PATH}",
            )

        text = WEAPON_FILE_PATH.read_text(encoding="utf-8").strip()
        if not text:
            return (
                DEFAULT_WEAPON_TEXT,
                False,
                "장부 파일이 비어 있어 기본 특약으로 분석합니다.",
            )

        return text, True, "장부 파일 연동 완료"
    except Exception as exc:
        return (
            DEFAULT_WEAPON_TEXT,
            False,
            f"장부 파일 읽기 실패로 기본 특약을 사용합니다: {exc}",
        )


PRODUCT_CATEGORIES = [
    "암/여성 건강보험",
    "운전자/생활종합",
    "유병자 간편보험",
]

# 장부 본문·상품명 키워드로 카테고리 귀속 (다중 카테고리 가능)
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "암/여성 건강보험": [
        "여성 건강",
        "시그니처",
        "통합암",
        "유방",
        "자궁",
        "난소",
        "호르몬",
        "암보험",
        "암 ",
        "암에",
        "종합건강",
        "굿밸런스",
        "뇌혈관",
        "심장",
    ],
    "운전자/생활종합": [
        "생활종합",
        "세이프투게더",
        "운전자",
        "변호사",
        "경찰",
        "면허",
        "사고",
        "출퇴근",
    ],
    "유병자 간편보험": [
        "유병",
        "간편",
        "라이프케어",
        "355",
        "고혈압",
        "당뇨",
        "입원",
        "수술",
        "간편 가입",
    ],
}

# 거절 멘트 자동 추론 시 카테고리 점수용 키워드
REJECTION_CATEGORY_SIGNALS: dict[str, list[str]] = {
    "암/여성 건강보험": ["암", "여성", "친척", "암보험", "건강보험", "진단비"],
    "운전자/생활종합": ["운전자", "운전", "사고", "무사고", "면허", "경찰", "자동차"],
    "유병자 간편보험": ["유병", "간편", "고혈압", "당뇨", "아팠", "서류", "심사", "고지"],
}


def parse_weapon_blocks(raw_text: str) -> list[dict[str, object]]:
    """장부 텍스트를 상품 단위로 파싱하고 카테고리·Priority 정보를 추출한다."""
    blocks: list[list[str]] = []
    current: list[str] = []

    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("[무기"):
            if current:
                blocks.append(current)
            current = [line]
        elif current:
            current.append(line)

    if current:
        blocks.append(current)

    parsed: list[dict[str, object]] = []
    for block in blocks:
        header = block[0]
        product_name = header.split("상품명:", 1)[1].strip() if "상품명:" in header else header
        priority_high = "[Priority: High]" in product_name
        product_name = product_name.replace("[Priority: High]", "").strip()
        body = "\n".join(block[1:]).strip()
        searchable_text = f"{product_name}\n{body}"

        explicit_categories: list[str] = []
        for line in block[1:]:
            if line.startswith("- 카테고리:"):
                explicit_categories.append(line.split(":", 1)[1].strip())

        categories = explicit_categories or infer_block_categories(searchable_text)
        parsed.append(
            {
                "product_name": product_name,
                "priority_high": priority_high,
                "body": body,
                "searchable_text": searchable_text,
                "categories": categories,
            }
        )

    return parsed


def infer_block_categories(searchable_text: str) -> list[str]:
    """상품명·본문 키워드로 장부 상품의 카테고리 귀속을 판별한다."""
    matched = [
        category
        for category, keywords in CATEGORY_KEYWORDS.items()
        if any(keyword in searchable_text for keyword in keywords)
    ]
    return matched or ["암/여성 건강보험"]


def resolve_primary_category(selected_product_group: str, rejection_ment: str) -> str:
    """섹션4 매칭용 단일 확정 카테고리를 결정한다 (카테고리 무결성)."""
    if selected_product_group != "선택 안 함 (AI 자동 추론)":
        return selected_product_group

    text = rejection_ment.strip()
    scores = {category: 0 for category in PRODUCT_CATEGORIES}

    for category, signals in REJECTION_CATEGORY_SIGNALS.items():
        for signal in signals:
            if signal in text:
                scores[category] += 3

    if any(keyword in text for keyword in ["보험료", "비싸", "부담", "주식", "코인", "아까"]):
        scores["암/여성 건강보험"] += 1
        scores["운전자/생활종합"] += 1
        scores["유병자 간편보험"] += 1

    best_score = max(scores.values())
    if best_score > 0:
        for category in PRODUCT_CATEGORIES:
            if scores[category] == best_score:
                return category

    return "암/여성 건강보험"


def block_matches_category(block: dict[str, object], category: str) -> bool:
    """상품이 확정 카테고리에 속하는지 검증한다."""
    return category in block.get("categories", [])


def format_weapon_block(block: dict[str, object], index: int | None = None) -> list[str]:
    """프롬프트용 상품 블록 텍스트를 만든다."""
    priority_label = " [Priority: High]" if bool(block["priority_high"]) else ""
    categories = ", ".join(block.get("categories", []))
    prefix = f"[후보 {index}] " if index is not None else ""
    return [
        f"{prefix}상품명: {block['product_name']}{priority_label}",
        f"- 귀속 카테고리: {categories}",
        str(block["body"]),
        "",
    ]


def build_weapon_context(raw_text: str, selected_product_group: str, rejection_ment: str) -> str:
    """2단계 필터(카테고리 → Priority High)로 장부 컨텍스트를 구성한다."""
    blocks = parse_weapon_blocks(raw_text)
    if not blocks:
        return raw_text

    primary_category = resolve_primary_category(selected_product_group, rejection_ment)

    category_matched = [b for b in blocks if block_matches_category(b, primary_category)]
    excluded_other = [b for b in blocks if not block_matches_category(b, primary_category)]

    high_in_category = [b for b in category_matched if bool(b["priority_high"])]
    fallback_in_category = [b for b in category_matched if not bool(b["priority_high"])]

    def relevance_score(block: dict[str, object]) -> int:
        score = 0
        if bool(block["priority_high"]):
            score += 100
        text = str(block["searchable_text"])
        for signal in REJECTION_CATEGORY_SIGNALS.get(primary_category, []):
            if signal in rejection_ment:
                score += 5
        for word in rejection_ment.split():
            if len(word) >= 2 and word in text:
                score += 1
        return score

    high_in_category = sorted(high_in_category, key=relevance_score, reverse=True)
    fallback_in_category = sorted(fallback_in_category, key=relevance_score, reverse=True)

    all_high_names = [
        str(b["product_name"]) for b in blocks if bool(b["priority_high"])
    ]
    category_high_names = [str(b["product_name"]) for b in high_in_category]

    lines = [
        "[매칭 무결성 검증]",
        f"- 확정 상품 카테고리: {primary_category}",
        f"- 설계사 선택값: {selected_product_group}",
        f"- 1차 필터(카테고리 일치) 상품 수: {len(category_matched)}개",
        f"- 2차 필터(동일 카테고리 + Priority High) 상품 수: {len(high_in_category)}개",
        (
            "- 장부 전체 Priority High 상품: "
            + (", ".join(all_high_names) if all_high_names else "없음")
        ),
        (
            "- 이번 카테고리 Priority High 상품: "
            + (", ".join(category_high_names) if category_high_names else "없음")
        ),
        "",
        "[최종 매칭 후보 - 섹션4 전용] (반드시 이 목록에서만 추천)",
    ]

    if high_in_category:
        for idx, block in enumerate(high_in_category, start=1):
            lines.extend(format_weapon_block(block, idx))
    elif fallback_in_category:
        lines.append(
            "(동일 카테고리 Priority High 상품 없음 → 아래 참고 후보 1개만 보조 사용 가능)"
        )
        lines.extend(format_weapon_block(fallback_in_category[0], 1))
    else:
        lines.append("(해당 카테고리 일치 상품 없음)")

    if len(high_in_category) > 1:
        lines.append("[동일 카테고리 Priority High 추가 후보]")
        for idx, block in enumerate(high_in_category[1:], start=2):
            lines.extend(format_weapon_block(block, idx))

    if fallback_in_category and high_in_category:
        lines.append("[참고 후보 - 동일 카테고리, Priority High 아님]")
        for idx, block in enumerate(fallback_in_category[:2], start=1):
            lines.extend(format_weapon_block(block, idx))

    if excluded_other:
        lines.append("[제외됨 - 타 카테고리 상품 · 섹션4 사용 금지]")
        for block in excluded_other:
            cats = ", ".join(block.get("categories", []))
            ph = " [Priority: High]" if bool(block["priority_high"]) else ""
            lines.append(f"- {block['product_name']}{ph} (귀속: {cats})")

    return "\n".join(lines).strip()


def call_openai_analysis(
    customer_name: str,
    customer_age: int,
    customer_gender: str,
    customer_job: str,
    selected_product_group: str,
    rejection_ment: str,
    weapons_text: str,
    weapons_source: str,
) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY 환경 변수가 설정되지 않았습니다. "
            "프로젝트 폴더의 `.env` 파일에 `OPENAI_API_KEY=...` 형식으로 값을 넣거나, "
            "터미널에서 환경 변수를 설정해 주세요."
        )

    client = OpenAI(api_key=api_key)

    user_content = f"""
고객 프로필
- 이름: {customer_name}
- 나이: {customer_age}세
- 성별: {customer_gender}
- 직업: {customer_job}
- 현재 제안 중인 상품군 선택: {selected_product_group}

현장 거절 멘트
"{rejection_ment}"

한화 실시간 상품 장부 데이터:
{weapons_text}

장부 로딩 상태:
{weapons_source}

시스템 지시에 따라, 위 고객의 거절 멘트를 뇌 과학 기반 속마음 성향 관점에서 분석하고
4개 ai-section HTML 블록만 출력하세요.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": user_content},
        ],
        temperature=0.95,
        max_tokens=4096,
    )
    text = response.choices[0].message.content
    if not text:
        raise RuntimeError("OpenAI 응답 본문이 비어 있습니다.")
    return text


# ── session_state 초기화 ─────────────────────────────────────
if "rejection_ment" not in st.session_state:
    st.session_state.rejection_ment = ""
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

# ── 메인 헤더 ─────────────────────────────────────────────────
st.markdown(
    """
<div class="main-header">
    <h1>🛡️ 한화손해 거절 처리 AI 비서</h1>
    <p>보험왕의 고객 속마음 분석</p>
</div>
""",
    unsafe_allow_html=True,
)

# ── [1구역] 사이드바: 고객 프로필 ─────────────────────────────
with st.sidebar:
    st.markdown("## 👤 고객 프로필")
    st.markdown('<span class="zone-label">1구역</span>', unsafe_allow_html=True)

    customer_name = st.text_input("이름", value="한송이", placeholder="예: 한송이")
    customer_age = st.slider("나이", min_value=20, max_value=80, value=35, step=1)
    customer_gender = st.radio("성별", options=["여성", "남성"], horizontal=True)
    customer_job = st.text_input("직업", value="회사원", placeholder="예: 회사원, 자영업")
    selected_product_group = st.radio(
        "현재 제안 중인 상품군 선택",
        options=PRODUCT_GROUP_OPTIONS,
        index=0,
        horizontal=True,
    )

    st.divider()
    st.markdown(
        """
<div style="background:#fff3e6; padding:12px; border-radius:8px; font-size:0.85rem; color:#555;">
    <strong style="color:#ff6600;">💡 Tip</strong><br>
    고객 프로필을 정확히 입력할수록<br>
    AI가 더 날카로운 맞춤 진단을 제공합니다.
</div>
""",
        unsafe_allow_html=True,
    )

# ── 메인 2·3구역 레이아웃 ─────────────────────────────────────
col_input, col_result = st.columns([1, 1], gap="large")

# ── [2구역] 입력 영역 ─────────────────────────────────────────
with col_input:
    st.markdown('<span class="zone-label">2구역</span>', unsafe_allow_html=True)
    st.markdown("### 🎤 현장 거절 멘트 입력")

    st.markdown(
        '<p class="shortcut-label">🔥 보험왕 치트키: 현장 거절 멘트 TOP 5 숏컷</p>',
        unsafe_allow_html=True,
    )

    shortcut_set = get_shortcuts_for_product_group(selected_product_group)
    group_slug = PRODUCT_GROUP_KEY_SLUG.get(selected_product_group, "auto")
    shortcut_cols = st.columns(5)

    for idx, (button_label, full_ment) in enumerate(shortcut_set):
        with shortcut_cols[idx]:
            if st.button(
                button_label,
                use_container_width=True,
                key=f"shortcut_{group_slug}_{idx}",
            ):
                st.session_state.rejection_ment = full_ment

    rejection_ment = st.text_area(
        "거절 멘트를 입력하거나 위 숏컷 버튼을 눌러주세요",
        height=160,
        key="rejection_ment",
        placeholder="고객이 실제로 한 말을 그대로 입력해 주세요...",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    analyze_clicked = st.button(
        "🧠 보험왕의 고객 속마음 분석",
        type="primary",
        use_container_width=True,
    )

# ── [3구역] 결과 영역 ─────────────────────────────────────────
with col_result:
    st.markdown('<span class="zone-label">3구역</span>', unsafe_allow_html=True)
    st.markdown("### 📊 AI 거절 처리 분석 결과")

    if analyze_clicked:
        if not rejection_ment.strip():
            st.warning("거절 멘트를 입력해 주세요.")
        else:
            with st.spinner("AI가 속마음 패턴을 분석하는 중... 🧠"):
                try:
                    weapons_text, loaded_from_file, weapons_status = load_hanwha_weapons()
                    prioritized_weapon_context = build_weapon_context(
                        raw_text=weapons_text,
                        selected_product_group=selected_product_group,
                        rejection_ment=rejection_ment.strip(),
                    )
                    ai_html = call_openai_analysis(
                        customer_name=customer_name,
                        customer_age=customer_age,
                        customer_gender=customer_gender,
                        customer_job=customer_job,
                        selected_product_group=selected_product_group,
                        rejection_ment=rejection_ment.strip(),
                        weapons_text=prioritized_weapon_context,
                        weapons_source=(
                            "실시간 장부 연동 성공"
                            if loaded_from_file
                            else f"기본 특약 폴백 사용 ({weapons_status})"
                        ),
                    )
                    st.session_state.analysis_result = ai_html
                    if loaded_from_file:
                        st.caption("✅ 상품 데이터 연동 완료")
                    else:
                        st.caption(f"🟡 상품 장부 폴백: {weapons_status}")
                except Exception as e:
                    st.session_state.analysis_result = None
                    st.error(f"AI 분석 중 오류가 발생했습니다: {e}")

    if st.session_state.analysis_result:
        ai_body = strip_code_fences(st.session_state.analysis_result)
        limbic_type = parse_limbic_axis_type(ai_body)
        ai_body = strip_limbic_type_marker(ai_body)
        ai_body = apply_definitive_tone(ai_body)
        ai_body = strip_section_h4_subtitles(ai_body)
        ai_body = repair_ai_html_display(ai_body)
        ai_body = apply_direct_ment_bold(ai_body)
        limbic_cards_html = build_limbic_axis_cards_html(limbic_type)
        render_analysis_result(ai_body, limbic_cards_html)
    else:
        st.markdown(
            """
<div class="result-panel">
<div style="text-align:center; padding:60px 20px; color:#aaa;">
    <div style="font-size:3rem;">🧠</div>
    <p style="font-size:1rem; margin-top:12px;">
        거절 멘트를 입력하고<br>
        <strong style="color:#ff6600;">[분석하기]</strong> 버튼을 눌러주세요.
    </p>
    <p style="font-size:0.85rem; color:#bbb;">
        AI가 속마음 패턴에 맞는<br>맞춤형 현장 멘트를 만들어 드립니다.
    </p>
</div>
</div>
""",
            unsafe_allow_html=True,
        )

