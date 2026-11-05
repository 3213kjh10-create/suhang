"""진로 나침반 — 실행: streamlit run app.py
Python 3.10+. GitHub 저장소에 이 파일과 requirements.txt를 올린 뒤
Streamlit Community Cloud에서 app.py를 배포하세요. GitHub Pages는 Python을 실행하지 않습니다.
배포 후 앱의 'QR 공유' 화면에 실제 https://…streamlit.app 주소를 입력하세요.
외부 API/로그인 없이 작동. 선택 정보는 해당 브라우저의 Streamlit 세션에만 유지됩니다.
자료 참고: 커리어넷 직업백과 / 한국고용정보원 한국직업사전.
아래 분류·설명·교과·미션은 교육용으로 재구성한 예시이며 공식 적성검사나 직업 전체 목록이 아닙니다.
"""
from __future__ import annotations
import io
import json
from urllib.parse import urlparse
import streamlit as st
import qrcode

st.set_page_config(page_title="진로 나침반", page_icon="🧭", layout="centered", initial_sidebar_state="collapsed")
CAREER_URL = "https://info.career.go.kr/cloud/w/job/list"
WORK_URL = "https://www.work.go.kr/consltJobCarpa/srch/jobDic/jobDicSrchByJobmap.do?pageType=jobDicSrchByJobmap"
CLASS_URL = "https://www.data.go.kr/data/15119096/fileData.do"

# 영역 → 분야 → (직업명, 하는 일, 연계 교과, 탐구 미션)
DATA = {
    "💻 기술·공학": {
        "소프트웨어·데이터": [
            ("소프트웨어 개발자", "사용자의 문제를 해결하는 프로그램을 설계하고 개발합니다.", "정보 · 수학", "학교생활의 불편 한 가지를 해결하는 앱 화면 3개를 그려보세요."),
            ("데이터 분석가", "자료를 정리하고 분석해 의사결정을 돕는 정보를 찾습니다.", "수학 · 정보", "공공데이터 한 가지로 질문을 만들고 그래프를 그려보세요.")],
        "기계·로봇": [
            ("로봇공학 기술자", "센서·기계·제어 기술을 결합해 로봇을 설계하고 시험합니다.", "물리학 · 정보", "분리수거 로봇의 센서와 동작 순서를 설계해보세요."),
            ("기계공학 기술자", "기계 장치의 구조와 작동을 설계하고 성능을 개선합니다.", "물리학 · 수학", "주변 기계 하나의 에너지 전달 과정을 그림으로 설명해보세요.")],
        "건축·공간": [
            ("건축가", "사람의 생활과 안전을 고려해 건축 공간을 계획하고 설계합니다.", "수학 · 미술", "학교 쉼터를 설계하고 이동 동선과 채광을 표시해보세요."),
            ("도시계획가", "교통·주거·환경을 고려해 도시 공간의 이용을 계획합니다.", "지리 · 사회", "학교 주변의 보행 위험 지점과 개선안을 지도에 표시해보세요.")]
    },
    "🧬 자연·생명": {
        "생명·바이오": [
            ("생명과학 연구원", "생명체의 구조와 기능을 실험·관찰로 연구합니다.", "생명과학 · 화학", "발아 조건에 관한 가설을 세우고 통제 변인을 정해보세요."),
            ("생명공학 연구원", "생명 현상을 활용해 의료·식품 등에서 쓰이는 기술을 연구합니다.", "생명과학 · 화학", "발효 기술의 활용 사례 두 가지를 비교해보세요.")],
        "환경·에너지": [
            ("환경공학 기술자", "물·대기·폐기물 문제를 줄이는 시설과 기술을 개발합니다.", "화학 · 지구과학", "교내 쓰레기 발생 원인을 관찰하고 감량 실험을 설계해보세요."),
            ("에너지공학 기술자", "에너지 생산·전환·효율 개선 기술을 연구하고 설계합니다.", "물리학 · 수학", "태양광과 풍력의 설치 조건과 한계를 비교해보세요.")],
        "기초과학": [
            ("화학 연구원", "물질의 성질과 반응을 연구하고 새로운 물질이나 공정을 탐구합니다.", "화학 · 수학", "생활 속 소재 두 가지의 성질과 쓰임을 조사해보세요."),
            ("천문학 연구원", "관측 자료와 이론으로 천체와 우주의 현상을 연구합니다.", "물리학 · 수학", "공개된 천체 관측 자료로 궁금한 질문 세 가지를 만들어보세요.")]
    },
    "🩺 건강·돌봄": {
        "의료·간호": [
            ("의사", "질병과 손상을 진단하고 치료하며 건강 관리를 돕습니다.", "생명과학 · 화학", "한 질환의 예방 정보를 공신력 있는 자료 두 곳에서 비교해보세요."),
            ("간호사", "대상자의 건강 상태를 살피고 간호와 건강 교육을 제공합니다.", "생명과학 · 보건", "환자가 이해하기 쉬운 손 씻기 안내문을 만들어보세요.")],
        "재활·영양": [
            ("물리치료사", "신체 기능 회복을 위해 평가와 운동·물리적 치료를 수행합니다.", "생명과학 · 체육", "재활 분야의 보조 도구 하나를 조사하고 사용 목적을 설명해보세요."),
            ("영양사", "영양 상태와 필요를 고려해 식단과 급식·영양 교육을 관리합니다.", "가정 · 생명과학", "학교 급식 한 끼의 식품군 구성을 분석해보세요.")],
        "상담·복지": [
            ("상담 전문가", "상담을 통해 정서·관계·적응 문제를 이해하고 해결을 돕습니다.", "사회 · 심리학", "친구의 고민을 들을 때 쓸 열린 질문 다섯 가지를 적어보세요."),
            ("사회복지사", "도움이 필요한 사람을 지원 서비스와 연결하고 복지 활동을 수행합니다.", "사회 · 윤리", "지역 복지기관 한 곳의 대상과 서비스를 조사해보세요.")]
    },
    "🎨 예술·미디어": {
        "디자인": [
            ("시각디자이너", "글자·색·이미지로 정보를 명확하게 전달하는 시각물을 만듭니다.", "미술 · 국어", "학교 행사 포스터를 만들고 정보의 우선순위를 설명해보세요."),
            ("UX/UI 디자이너", "사용자의 경험을 조사하고 디지털 서비스의 흐름과 화면을 설계합니다.", "미술 · 정보", "앱 하나의 불편한 화면을 개선하고 친구에게 사용해보게 하세요.")],
        "영상·콘텐츠": [
            ("방송 연출가", "방송 콘텐츠의 기획과 제작 과정을 이끌어갑니다.", "국어 · 예술", "학교를 소개하는 1분 영상의 구성안과 장면표를 써보세요."),
            ("영상 편집자", "촬영된 영상과 소리를 구성해 의도에 맞는 결과물로 편집합니다.", "예술 · 정보", "직접 찍은 영상으로 30초 이야기를 만들어보세요.")],
        "글·공연": [
            ("작가", "관찰과 상상을 바탕으로 문학·방송 등 다양한 글을 씁니다.", "국어 · 사회", "같은 사건을 서로 다른 인물의 시점으로 써보세요."),
            ("배우", "인물과 상황을 해석해 몸과 목소리로 역할을 표현합니다.", "국어 · 예술", "짧은 대사를 두 가지 감정으로 표현하고 차이를 기록해보세요.")]
    },
    "📊 경영·사회": {
        "경영·금융": [
            ("경영 컨설턴트", "조직의 문제를 분석하고 운영과 전략의 개선안을 제안합니다.", "경제 · 수학", "학교 매점의 문제를 가정하고 근거 있는 개선안을 제안해보세요."),
            ("회계사", "회계 정보를 검토하고 감사·회계·세무 관련 전문 업무를 수행합니다.", "수학 · 경제", "가상의 동아리 수입과 지출을 기록하고 잔액을 검산해보세요.")],
        "마케팅·유통": [
            ("마케팅 전문가", "고객과 시장을 분석해 제품·서비스의 전달과 판매 전략을 세웁니다.", "경제 · 사회", "같은 상품의 광고 두 개를 비교하고 목표 고객을 추론해보세요."),
            ("상품기획자", "고객 수요와 시장을 바탕으로 상품의 구성과 출시 방향을 기획합니다.", "경제 · 미술", "친구 세 명의 필요를 듣고 새 학용품의 기획안을 작성해보세요.")],
        "법·공공": [
            ("변호사", "법률 상담과 사건 대리 등을 통해 의뢰인의 권리 보호를 돕습니다.", "사회 · 국어", "생활 속 갈등 사례를 정하고 양쪽의 주장과 쟁점을 정리해보세요."),
            ("행정공무원", "공공 정책과 행정 서비스를 기획·집행하며 주민의 필요에 대응합니다.", "사회 · 국어", "지역 민원 하나를 골라 해결 제안서를 한 쪽으로 작성해보세요.")]
    },
    "🌱 교육·생활": {
        "교육": [
            ("교사", "학생의 배움과 성장을 돕고 수업·평가·생활교육을 수행합니다.", "국어 · 관심 교과", "좋아하는 개념을 설명하는 5분 수업을 설계해보세요."),
            ("직업상담사", "개인의 특성과 직업정보를 함께 살펴 진로와 취업 계획을 돕습니다.", "사회 · 국어", "관심 직업 두 개의 업무와 준비 경로를 비교해보세요.")],
        "식품·관광": [
            ("조리사", "식재료와 조리법을 활용해 위생과 품질을 고려한 음식을 만듭니다.", "가정 · 화학", "같은 재료의 조리법을 바꾸었을 때 생기는 차이를 기록해보세요."),
            ("여행상품 개발자", "여행자의 필요와 지역 자원을 살펴 여행 일정과 상품을 기획합니다.", "지리 · 외국어", "지역의 문화와 이동 시간을 반영한 하루 여행을 기획해보세요.")],
        "농업·스포츠": [
            ("스마트팜 전문가", "센서와 정보기술을 활용해 농작물의 재배 환경을 관리합니다.", "생명과학 · 정보", "작물 재배에 필요한 환경 변수와 측정 방법을 정리해보세요."),
            ("스포츠 지도자", "대상자의 특성과 목표에 맞춰 운동 기술과 훈련을 지도합니다.", "체육 · 생명과학", "초보자를 위한 안전한 운동 계획과 주의사항을 조사해보세요.")]
    }
}

st.markdown("""<style>
[data-testid="stAppViewContainer"] {background:linear-gradient(145deg,#f5f7ff,#f0fdfa)}
.block-container {max-width:780px;padding-top:1.1rem;padding-bottom:1rem}
h1 {font-size:1.8rem!important;letter-spacing:-.06rem;color:#16324f}
h2,h3 {color:#16324f}
.stButton>button {min-height:2.6rem;border-radius:14px;font-weight:650}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:18px}
[data-testid="stCaptionContainer"] {color:#475569}
@media(max-width:600px){.block-container{padding:0.7rem 1rem 1rem}h1{font-size:1.45rem!important}}
</style>""", unsafe_allow_html=True)

DEFAULTS = {"step":0,"domain":None,"field":None,"job":None,"view":"하는 일","share":False,"source":False,"choice_page":0}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value
s = st.session_state


def move(step):
    s.step = step
    s.choice_page = 0
    st.rerun()


def choose(items, prefix):
    """세로로 최대 세 개 선택지: 모바일의 무한 스크롤 대신 페이지 이동."""
    per_page = 3
    pages = (len(items) + per_page - 1) // per_page
    s.choice_page = min(s.choice_page, pages - 1)
    start = s.choice_page * per_page
    for i, label in enumerate(items[start:start + per_page], start):
        if st.button(label, key=f"{prefix}_{i}", use_container_width=True):
            return label
    if pages > 1:
        left, middle, right = st.columns([1,1,1])
        if left.button("← 이전", disabled=s.choice_page == 0, use_container_width=True):
            s.choice_page -= 1
            st.rerun()
        middle.caption(f"선택지 {s.choice_page + 1} / {pages}")
        if right.button("다음 →", disabled=s.choice_page == pages - 1, use_container_width=True):
            s.choice_page += 1
            st.rerun()
    return None


def selected_record():
    return next(row for row in DATA[s.domain][s.field] if row[0] == s.job)


def valid_public_url(value):
    try:
        u = urlparse(value)
        host = (u.hostname or "").lower()
        # QR 대상 검증일 뿐 서버가 해당 URL을 요청하지는 않습니다.
        return (u.scheme == "https" and bool(host) and "." in host
                and host not in {"localhost", "127.0.0.1", "0.0.0.0"}
                and not u.username and not u.password and len(value) <= 1500)
    except ValueError:
        return False


st.title("🧭 진로 나침반")
st.caption("정답을 고르는 대신, 나의 다음 가능성을 발견해요.")
nav1, nav2, nav3 = st.columns(3)
if nav1.button("🏠 처음", use_container_width=True):
    for key, value in DEFAULTS.items():
        s[key] = value
    st.rerun()
if nav2.button("🔗 QR 공유", use_container_width=True):
    s.share, s.source = not s.share, False
    st.rerun()
if nav3.button("📚 출처", use_container_width=True):
    s.source, s.share = not s.source, False
    st.rerun()

if s.share:
    st.subheader("QR로 바로 접속하기")
    st.caption("배포된 앱의 공개 HTTPS 주소를 넣어주세요. 휴대폰에서 QR을 스캔하면 열립니다.")
    address = st.text_input("공개 앱 주소", placeholder="https://your-app.streamlit.app", max_chars=1500).strip()
    if address:
        if valid_public_url(address):
            image = qrcode.make(address)
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            st.image(buffer.getvalue(), width=190)
            st.download_button("QR 이미지 저장", buffer.getvalue(), "career-qr.png", "image/png")
            st.caption("입력한 주소를 QR로 변환합니다. 실제 공개 접속 여부는 휴대폰으로 확인하세요.")
        else:
            st.warning("공개된 https:// 주소를 입력하세요. 로컬 실행 주소는 공유할 수 없습니다.")
    if st.button("탐색으로 돌아가기", use_container_width=True):
        s.share = False
        st.rerun()
    st.stop()

if s.source:
    st.subheader("정보를 읽는 방법")
    st.markdown(f"[커리어넷 직업백과]({CAREER_URL}) · 직업별 업무와 준비 경로 확인\n\n[한국고용정보원 한국직업사전]({WORK_URL}) · 직무 중심의 직업 분류 참고\n\n[워크넷 직업분류 공개자료]({CLASS_URL}) · 계층형 직업분류 구조 참고")
    st.info("이 앱은 위 자료를 참고해 6개 영역·18개 분야·36개 직업을 교육용으로 재구성했습니다. 공식 분류의 복제, 실시간 API 연동, 공식 적성검사 결과가 아닙니다.")
    st.caption("설명·교과 연결·탐구 미션은 앱에서 작성한 예시입니다. 임금·취업률·전망 수치는 제공하지 않습니다. 자격·면허와 진학 경로는 공식 사이트에서 별도로 확인하세요. 자료 참고일: 2026-11-05.")
    if st.button("탐색으로 돌아가기", use_container_width=True):
        s.source = False
        st.rerun()
    st.stop()

labels = ["관심 영역", "세부 분야", "직업 선택", "탐구 카드"]
st.progress((s.step + 1) / 4, text=f"{s.step + 1} / 4 · {labels[s.step]}")
if s.step > 0:
    st.caption(" › ".join(x for x in [s.domain, s.field if s.step >= 2 else None, s.job if s.step >= 3 else None] if x))

if s.step == 0:
    st.subheader("어떤 세상이 궁금한가요?")
    st.caption("관심 가는 영역을 선택하세요. 언제든 돌아와 바꿀 수 있어요.")
    picked = choose(list(DATA), "domain")
    if picked:
        s.domain, s.field, s.job = picked, None, None
        move(1)
elif s.step == 1:
    st.subheader("조금 더 좁혀볼까요?")
    picked = choose(list(DATA[s.domain]), "field")
    if picked:
        s.field, s.job = picked, None
        move(2)
elif s.step == 2:
    st.subheader("먼저 알아보고 싶은 직업은?")
    picked = choose([row[0] for row in DATA[s.domain][s.field]], "job")
    if picked:
        s.job, s.view = picked, "하는 일"
        move(3)
else:
    job, description, subjects, mission = selected_record()
    st.subheader(job)
    view = st.selectbox("카드 내용", ["하는 일", "준비와 탐구", "나의 계획", "공식 정보"], key="view", label_visibility="collapsed")
    if view == "하는 일":
        with st.container(border=True):
            st.markdown("**이런 일을 해요**")
            st.write(description)
            st.markdown("**연결해 볼 교과**")
            st.write(subjects)
        st.caption("교과는 탐색을 돕는 예시이며 필수 이수 조건이 아닙니다. 이 선택은 적성 판정이 아니에요.")
    elif view == "준비와 탐구":
        with st.container(border=True):
            st.markdown("**이번 주 작은 도전**")
            st.write(mission)
            st.caption("질문 만들기 → 자료 찾기 → 직접 해보기 → 느낀 점 기록")
        st.caption("실험·촬영·운동 활동은 안전과 개인정보를 우선하고 필요하면 교사의 지도를 받으세요.")
    elif view == "나의 계획":
        reason = st.text_input("이 직업이 궁금한 이유", key=f"reason_{job}", max_chars=120)
        action = st.text_input("이번 주에 해볼 한 가지", key=f"action_{job}", max_chars=120)
        reflection = st.text_input("더 확인하고 싶은 질문", key=f"question_{job}", max_chars=120)
        plan = {"관심 영역":s.domain,"세부 분야":s.field,"직업":job,"궁금한 이유":reason,"실천 계획":action,"탐구 질문":reflection,"추천 탐구":mission,"참고":CAREER_URL,"안내":"교육용 탐색 기록이며 적성 진단이 아닙니다."}
        text = "나의 진로 탐구 카드\n\n" + "\n".join(f"{k}: {v}" for k,v in plan.items())
        st.download_button("📝 탐구 카드 저장", text.encode("utf-8-sig"), "나의_진로탐구.txt", "text/plain", use_container_width=True)
        st.caption("계획은 서버의 파일이나 DB에 저장하지 않습니다. 세션이 종료되면 사라질 수 있으니 내려받으세요. 이름·연락처는 쓰지 마세요.")
    else:
        st.write(f"공식 사이트에서 **{job}** 또는 유사 직업명을 검색하세요.")
        st.link_button("커리어넷 직업백과 열기", CAREER_URL, use_container_width=True)
        st.link_button("한국직업사전 열기", WORK_URL, use_container_width=True)
        st.caption("업무 범위, 필요 자격, 교육 경로를 확인해보세요. 링크는 직업별 상세 페이지가 아닌 공식 검색·분류 입구입니다.")

if s.step > 0:
    if st.button("← 이전 단계", use_container_width=True):
        move(s.step - 1)
