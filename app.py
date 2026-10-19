import asyncio
import os
import pdfplumber
import re
import streamlit as st

# 페이지 설정
st.set_page_config(page_title="소방 오디오 브리퍼", page_icon="🎧", layout="centered")

st.title("🎧 나만의 소방 오디오 브리퍼")
st.markdown(
    "수험서나 법령 PDF를 올리면, **법제처 머리글 및 메타데이터를 제거하고 핵심"
    " 수치·조항 위주**의 깨끗한 오디오 브리핑 파일로 변환해 드립니다."
)

# 사이드바 설정 (목소리 선택)
st.sidebar.header("⚙️ 음성 설정")
voice_option = st.sidebar.selectbox(
    "AI 음성 선택",
    (
        "ko-KR-SunHiNeural (차분한 여성 톤)",
        "ko-KR-InJoonNeural (신뢰감 있는 남성 톤)",
    ),
)
selected_voice = voice_option.split(" ")[0]

# 파일 업로드
uploaded_file = st.file_uploader(
    "📂 소방 법령/요약본 PDF 파일을 업로드하세요", type=["pdf"]
)


def extract_text_from_pdf(file):
  text = ""
  with pdfplumber.open(file) as pdf:
    for page_num, page in enumerate(pdf.pages, 1):
      extracted = page.extract_text()
      if extracted:
        text += f"\n[페이지 {page_num}]\n" + extracted + "\n"
  return text


def refine_nftc_text(raw_text):
  # 1. 법제처 머리글, 페이지 번호, 공고문 및 개정일자 메타데이터 제거
  text = re.sub(r"법제처\s*\d*\s*국가법령정보센터", "", raw_text)
  text = re.sub(r"페이지\s*\d+", "", text)
  text = re.sub(
      r"소화기구 및 자동소화장치의 화재안전기술기준\(NFTC 101\)", "", text
  )
  text = re.sub(r"\[국립소방연구원공고[^\]]*\]", "", text)
  text = re.sub(r"\[시행\s*[\d\.]+\]", "", text)
  text = re.sub(r"<개정[^>]*>", "", text)
  text = re.sub(r"\[페이지\s*\d+\]", "", page_str if "page_str" in locals() else "")

  # 2. 불필요한 공백 및 빈 줄 정리
  lines = [line.strip() for line in text.split("\n") if line.strip()]
  cleaned_text = " ".join(lines)
  return cleaned_text


async def generate_audio(text, voice, output_path):
  communicate = edge_tts.Communicate(text, voice)
  await communicate.save(output_path)


if uploaded_file is not None:
  st.success("✅ 파일 업로드 완료!")

  if st.button("🚀 오디오 브리핑 생성하기", type="primary"):
    with st.spinner(
        "📄 PDF 텍스트 분석 및 불필요한 메타데이터 정제 중입니다..."
    ):
      # 1. 텍스트 추출
      raw_text = extract_text_from_pdf(uploaded_file)

      if not raw_text.strip():
        st.error(
            "⚠️ PDF에서 텍스트를 추출할 수 없습니다. (이미지 스캔본인지"
            " 확인해주세요)"
        )
      else:
        # 2. NFTC 맞춤형 텍스트 정돈 및 정제
        clean_text = refine_nftc_text(raw_text)

        # 3. 음성 파일 생성
        output_mp3 = "briefing_output.mp3"
        asyncio.run(generate_audio(clean_text, selected_voice, output_mp3))

        st.success("✨ 오디오 브리핑 생성 완료!")

        # 플레이어 및 다운로드 버튼 제공
        st.audio(output_mp3, format="audio/mp3")

        with open(output_mp3, "rb") as f:
          st.download_button(
              label="📥 MP3 파일 다운로드",
              data=f,
              file_name="소방_핵심브리핑.mp3",
              mime="audio/mp3",
          )
