import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import platform
import re
from collections import Counter

# 한글 폰트 설정 (OS별 깨짐 방지)
if platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
elif platform.system() == 'Darwin':  # Mac
    plt.rc('font', family='AppleGothic')
else:
    plt.rc('font', family='NanumGothic')
plt.rcParams['axes.unicode_minus'] = False

# 긍정 및 부정 키워드 사전 정의
POSITIVE_WORDS = ['좋아요', '맛있어요', '재미있어요', '편리해요', '친절해요', '즐거워요', '도움이', '예뻐서']
NEGATIVE_WORDS = ['피곤해요', '불편해요', '힘들어요', '아쉬워요', '부족해요', '후회돼요', '붐벼서', '멀어서', '비싸서']

# 1. 제목
st.title("📊 인문사회대 생활습관 및 만족도 분석 대시보드")
st.write("학생회에서 학우들의 일상 습관과 학교생활 만족도, 생생한 의견을 분석하는 페이지입니다.")

# 2. CSV 파일 업로드
uploaded_file = st.file_uploader("📂 캠퍼스 라이프 CSV 파일을 업로드해주세요", type=["csv"])

if uploaded_file is not None:
    # 데이터 로드
    raw_df = pd.read_csv(uploaded_file)

    # 3. 데이터 보기
    st.subheader("1. 원본 데이터 미리보기")
    st.dataframe(raw_df.head())

    # 4. 전처리 결과 및 제외 건수 표시
    st.subheader("2. 데이터 전처리 결과")

    cleaned_df = raw_df.copy()
    cleaned_df['만족도'] = pd.to_numeric(cleaned_df['만족도'], errors='coerce')
    cleaned_df['공부시간'] = pd.to_numeric(cleaned_df['공부시간'], errors='coerce')

    # 결측치/이상 데이터 집계 및 제거
    total_count = len(raw_df)
    drop_count = cleaned_df[['공부시간', '만족도', '수면시간', '스마트폰']].isna().any(axis=1).sum()
    cleaned_df = cleaned_df.dropna(subset=['공부시간', '만족도', '수면시간', '스마트폰'])
    valid_count = len(cleaned_df)

    col1, col2, col3 = st.columns(3)
    col1.metric("전체 응답 수", f"{total_count}건")
    col2.metric("제외된 불량/결측 데이터", f"{drop_count}건")
    col3.metric("분석 활용 데이터", f"{valid_count}건")

    # 5. 학과 선택 필터
    st.subheader("3. 학과 선택")
    dept_list = ["전체"] + sorted(cleaned_df['학과'].dropna().unique().tolist())
    selected_dept = st.selectbox("확인하고 싶은 학과를 선택하세요:", dept_list)

    # 선택 학과에 따른 데이터 필터링
    if selected_dept == "전체":
        dept_df = cleaned_df
    else:
        dept_df = cleaned_df[cleaned_df['학과'] == selected_dept]

    avg_satisfaction = dept_df['만족도'].mean()
    st.info(f"💡 **[{selected_dept}]** 학생들의 평균 학교생활 만족도: **{avg_satisfaction:.2f}점** / 10점 만점")

    # 6. 그래프 결과
    st.subheader(f"4. [{selected_dept}] 시각화 및 한 줄 의견 분석 결과")

    # (1) 산점도: 공부시간 vs 만족도
    st.markdown("#### 📌 생활습관(공부시간)과 만족도 관계 (산점도)")
    fig1, ax1 = plt.subplots(figsize=(7, 4))
    sns.scatterplot(data=dept_df, x='공부시간', y='만족도', hue='학년', palette='viridis', s=100, ax=ax1)
    ax1.set_title(f"{selected_dept} - 공부시간에 따른 학교생활 만족도")
    ax1.set_xlabel("하루 평균 공부시간(시간)")
    ax1.set_ylabel("만족도 점수")
    ax1.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig1)

    # (2) 히트맵: 생활습관 변수 간 상관관계 분석
    st.markdown("#### 📌 생활습관 및 만족도 상관관계 분석 (히트맵)")
    num_cols = ['통학시간', '공부시간', '스마트폰', '수면시간', '만족도']
    if len(dept_df) > 1:
        corr_matrix = dept_df[num_cols].corr()
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5, ax=ax2)
        ax2.set_title(f"{selected_dept} - 생활요소 간 상관계수 히트맵")
        st.pyplot(fig2)
    else:
        st.warning("데이터 수가 부족하여 상관관계 히트맵을 생성할 수 없습니다.")

    # (3) 워드클라우드
    st.markdown("#### 📌 한 줄 의견 워드클라우드")
    opinions = dept_df['한줄의견'].dropna().astype(str).tolist()
    text_data = " ".join(opinions)

    if text_data.strip():
        wc = WordCloud(
            font_path='NanumGothic' if platform.system() != 'Windows' else 'malgun',
            background_color='white',
            width=800,
            height=350
        ).generate(text_data)

        fig3, ax3 = plt.subplots(figsize=(8, 3.5))
        ax3.imshow(wc, interpolation='bilinear')
        ax3.axis('off')
        st.pyplot(fig3)
    else:
        st.write("등록된 한 줄 의견이 없습니다.")

    # (4) [추가 기능] 한 줄 의견 단어 빈도 Top 10 막대그래프
    st.markdown("#### 📌 한 줄 의견 최다 등장 단어 상위 10개")
    # 한글 단어 추출 (2글자 이상)
    words = re.findall(r'[가-힣]{2,}', text_data)
    word_counts = Counter(words)
    top_10_words = word_counts.most_common(10)

    if top_10_words:
        top_df = pd.DataFrame(top_10_words, columns=['단어', '빈도'])
        fig4, ax4 = plt.subplots(figsize=(7, 4))
        sns.barplot(data=top_df, x='빈도', y='단어', palette='Blues_r', ax=ax4)
        ax4.set_title(f"[{selected_dept}] 자주 등장하는 단어 Top 10")
        ax4.set_xlabel("등장 횟수")
        ax4.set_ylabel("단어")
        st.pyplot(fig4)
    else:
        st.write("분석할 단어 데이터가 충분하지 않습니다.")

    # (5) [추가 기능] 긍정 단어 vs 부정 단어 등장 횟수 분석
    st.markdown("#### 📌 한 줄 의견 긍정/부정 감성 단어 빈도")
    pos_count = sum(word_counts[w] for w in POSITIVE_WORDS)
    neg_count = sum(word_counts[w] for w in NEGATIVE_WORDS)

    col_pos, col_neg = st.columns(2)
    col_pos.metric("😊 긍정 단어 등장 횟수", f"{pos_count}회")
    col_neg.metric("😟 부정 단어 등장 횟수", f"{neg_count}회")

    # 긍정/부정 비교 막대그래프
    sentiment_df = pd.DataFrame({
        '감성': ['긍정 단어', '부정 단어'],
        '등장횟수': [pos_count, neg_count]
    })
    fig5, ax5 = plt.subplots(figsize=(5, 3))
    sns.barplot(data=sentiment_df, x='감성', y='등장횟수', palette=['#4CAF50', '#FF5722'], ax=ax5)
    ax5.set_title(f"[{selected_dept}] 긍정 vs 부정 단어 빈도 비교")
    ax5.set_ylabel("총 등장 횟수")
    for i, v in enumerate([pos_count, neg_count]):
        ax5.text(i, v + 0.1, f"{v}회", ha='center', fontweight='bold')
    st.pyplot(fig5)

else:
    st.info("좌측 또는 상단의 업로드 창에서 CSV 파일을 업로드하면 대시보드가 활성화됩니다.")