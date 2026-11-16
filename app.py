import os
from io import BytesIO

import qrcode
import streamlit as st

st.set_page_config(
    page_title="먹다남은 음식 살리기",
    page_icon="🥕",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    #MainMenu, footer, header {visibility:hidden;}
    [data-testid="stAppViewContainer"] {background:#f7f8f7;}
    .block-container {
        max-width: 570px !important;
        margin: 0 auto !important;
        padding: .65rem .8rem 1rem !important;
    }
    [data-testid="stVerticalBlock"] {gap:.45rem;}
    [data-testid="stHorizontalBlock"] {gap:.5rem;}
    h1 {font-size:1.35rem !important; margin:0 !important;}
    h2 {font-size:1rem !important; margin:0 0 .25rem !important;}
    p, label, .stMarkdown {font-size:.83rem;}
    .intro {color:#65716a;font-size:.78rem;margin:.1rem 0 .45rem;}
    .card {
        background:#fff; border:1px solid #e7ebe8; border-radius:14px;
        padding:10px 11px; margin:4px 0;
    }
    .card-title {font-size:.93rem;font-weight:750;margin-bottom:5px;}
    .food-row {
        display:flex;justify-content:space-between;align-items:center;
        background:#f6f8f6;border-radius:9px;padding:7px 9px;
        margin:4px 0;font-size:.81rem;
    }
    .sub {color:#78827c;font-size:.72rem;}
    .tip {
        background:#f1f8f3;border-radius:9px;padding:8px 9px;
        margin:4px 0;font-size:.78rem;line-height:1.35;
    }
    div[data-testid="stForm"] {border:0;padding:0;}
    .stTextInput input {min-height:2.15rem;}
    .stButton button,.stFormSubmitButton button {
        min-height:2.15rem;border-radius:9px;font-weight:650;
        font-size:.8rem;padding:.25rem .45rem;
    }
    @media(max-width:600px) {
        .block-container {padding:.4rem .55rem .7rem !important;}
        h1 {font-size:1.2rem !important;}
        p,label,.stMarkdown {font-size:.78rem;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Food category is inferred to keep registration simple.
CATEGORY_WORDS = {
    "채소": ["당근", "양파", "대파", "애호박", "호박", "버섯", "감자", "고구마", "부추", "오이", "양배추", "상추", "시금치", "파프리카", "브로콜리"],
    "과일": ["사과", "바나나", "딸기", "블루베리", "포도", "귤", "오렌지", "배", "키위", "수박"],
    "밥·면": ["밥", "쌀", "국수", "면", "파스타", "빵", "식빵", "떡"],
    "고기·생선": ["고기", "소고기", "돼지고기", "닭고기", "생선", "참치", "햄", "베이컨", "새우"],
    "유제품": ["우유", "치즈", "요거트", "요구르트", "버터"],
}
RECIPES = [
    ("채소 볶음밥", ["밥", "당근", "양파", "대파", "달걀", "햄", "버섯", "애호박"], "재료를 잘게 썰어 볶고 밥을 넣어 간장으로 간을 맞춰요."),
    ("냉장고 채소전", ["당근", "양파", "대파", "애호박", "버섯", "감자", "부추"], "채소를 썰어 부침가루 반죽에 넣고 노릇하게 부쳐요."),
    ("달걀말이", ["달걀", "당근", "양파", "대파", "햄", "치즈"], "잘게 썬 재료를 달걀물에 섞어 약불에서 말아 익혀요."),
    ("두부 채소 덮밥", ["두부", "양파", "당근", "버섯", "대파", "밥"], "두부와 채소를 볶아 양념한 뒤 밥 위에 올려요."),
    ("감자채 볶음", ["감자", "당근", "양파", "대파"], "감자를 가늘게 썰어 채소와 함께 충분히 볶아요."),
    ("과일 요거트", ["사과", "바나나", "딸기", "블루베리", "요거트"], "과일을 먹기 좋은 크기로 잘라 요거트에 곁들여요."),
    ("참치 주먹밥", ["밥", "참치", "김", "당근", "마요네즈"], "재료를 밥과 섞어 한입 크기로 뭉쳐요."),
]
TIPS = {
    "채소": "채소는 물기를 제거해 밀폐 용기에 보관하고, 무른 부분이 있는지 먼저 확인해요.",
    "과일": "과일은 종류에 맞게 냉장 또는 실온 보관하고 상한 부분이 있는지 확인해요.",
    "밥·면": "조리한 밥과 면은 실온에 오래 두지 말고 소분해 빠르게 냉장·냉동해요.",
    "고기·생선": "다른 식품과 분리해 밀봉하고 포장지의 보관 안내를 지켜요.",
    "유제품": "개봉 후 냉장 보관하고 제품에 표시된 소비기한을 확인해요.",
    "기타": "포장지의 보관 안내를 확인하고 먼저 구입한 식품부터 사용해요.",
}

def guess_category(name: str) -> str:
    clean = name.replace(" ", "")
    for category, words in CATEGORY_WORDS.items():
        if any(word in clean for word in words):
            return category
    return "기타"

if "foods" not in st.session_state:
    st.session_state.foods = []

st.title("🥕 먹다남은 음식 살리기")
st.markdown('<div class="intro">남은 재료를 등록하면 만들 수 있는 요리를 바로 찾아드려요.</div>', unsafe_allow_html=True)

# One simple add action: name and amount only.
st.markdown('<div class="card"><div class="card-title">➕ 재료 간편 등록</div>', unsafe_allow_html=True)
with st.form("quick_add", clear_on_submit=True):
    name_col, amount_col = st.columns([1.5, 1])
    with name_col:
        food_name = st.text_input("재료 이름", placeholder="예: 당근")
    with amount_col:
        amount = st.text_input("남은 양", placeholder="예: 1개")
    add = st.form_submit_button("재료 추가", use_container_width=True)
    if add:
        if food_name.strip():
            st.session_state.foods.append({
                "name": food_name.strip(),
                "amount": amount.strip() or "양 미입력",
                "category": guess_category(food_name.strip()),
            })
            st.rerun()
        else:
            st.warning("재료 이름을 입력해 주세요.")
st.markdown('</div>', unsafe_allow_html=True)

# Match recipes from registered ingredients.
normalized = [item["name"].replace(" ", "").lower() for item in st.session_state.foods]
matches = []
for title, ingredients, how in RECIPES:
    found = [
        ingredient for ingredient in ingredients
        if any(
            ingredient.replace(" ", "").lower() in name
            or name in ingredient.replace(" ", "").lower()
            for name in normalized
        )
    ]
    if found:
        matches.append((len(found), title, found, how))
matches.sort(key=lambda item: item[0], reverse=True)

# Inventory
st.markdown(f'<div class="card"><div class="card-title">🧺 내 재료 <span class="sub">({len(st.session_state.foods)}개)</span></div>', unsafe_allow_html=True)
if st.session_state.foods:
    for index, item in enumerate(st.session_state.foods):
        col_text, col_delete = st.columns([5, 1])
        with col_text:
            st.markdown(
                f'<div class="food-row"><span><b>{item["name"]}</b>　'
                f'<span class="sub">{item["amount"]} · {item["category"]}</span></span></div>',
                unsafe_allow_html=True,
            )
        with col_delete:
            if st.button("삭제", key=f"delete_{index}"):
                st.session_state.foods.pop(index)
                st.rerun()
else:
    st.markdown('<div class="sub">아직 등록된 재료가 없어요. 위에서 간단히 추가해 보세요.</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Recommendations
st.markdown('<div class="card"><div class="card-title">🍳 지금 만들 수 있는 요리</div>', unsafe_allow_html=True)
if matches:
    for _, title, found, how in matches[:3]:
        st.markdown(
            f'<div class="food-row"><span><b>{title}</b><br>'
            f'<span class="sub">활용 재료: {", ".join(found)}</span><br>{how}</span></div>',
            unsafe_allow_html=True,
        )
else:
    st.markdown('<div class="sub">재료를 등록하면 추천 요리가 여기에 자동으로 나타나요.</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Waste prevention tips
st.markdown('<div class="card"><div class="card-title">♻️ 음식물 낭비 줄이는 팁</div>', unsafe_allow_html=True)
if st.session_state.foods:
    categories = list(dict.fromkeys(item["category"] for item in st.session_state.foods))
    for category in categories[:2]:
        st.markdown(f'<div class="tip"><b>{category}</b> · {TIPS[category]}</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="tip">장을 보기 전 냉장고를 확인하고, 먼저 구입한 식품부터 사용해요.</div>', unsafe_allow_html=True)
    st.markdown('<div class="tip">남은 음식은 한 끼 분량으로 나눠 보관하면 편리해요.</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

with st.expander("📱 앱 QR 코드"):
    url = st.text_input("배포한 앱 주소", value=os.getenv("APP_URL", ""), placeholder="https://앱이름.streamlit.app")
    if url.strip().startswith(("https://", "http://")):
        qr = qrcode.QRCode(box_size=5, border=2)
        qr.add_data(url.strip())
        qr.make(fit=True)
        image = qr.make_image(fill_color="#263b2e", back_color="white")
        output = BytesIO()
        image.save(output, format="PNG")
        st.image(output.getvalue(), width=125)
        st.caption("휴대폰 카메라로 QR을 스캔해 접속하세요.")
    else:
        st.caption("배포 후 앱 주소를 입력하면 QR 코드가 만들어져요.")

st.markdown('<div class="sub" style="text-align:center;padding-top:5px;">식품 상태와 소비기한을 확인하고, 이상이 있으면 먹지 마세요.</div>', unsafe_allow_html=True)
