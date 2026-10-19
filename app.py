import asyncio
import os
import pdfplumber
import re
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="소방 오디오 브리퍼", page_icon="🎧", layout="centered"
)

st.title("🎧 나만의 소방 오디오 브리퍼")
st.markdown(
    "PDF 파일을 올려서 대본을 추출하거나, **직접 다듬은 대본을 붙여넣어**"
    " 오디오 브리핑 파일로 변환하세요."
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


def extract_text_from_pdf(file):
  text = ""
  with pdfplumber.open(file) as pdf:
    for page_num, page in enumerate(pdf.pages, 1):
      extracted = page.extract_text()
      if extracted:
        text += f"\n[페이지 {page_num}]\n" + extracted + "\n"
  return text


def refine_nftc_text(raw_text):
  text = re.sub(r"법제처\s*\d*\s*국가법령정보센터", "", raw_text)
  text = re.sub(r"페이지\s*\d+", "", text)
  text = re.sub(
      r"소화기구 및 자동소화장치의 화재안전기술기준\(NFTC 101\)", "", text
  )
  text = re.sub(r"\[국립소방연구원공고[^\]]*\]", "", text)
  text = re.sub(r"\[시행\s*[\d\.]+\]", "", text)
  text = re.sub(r"<개정[^>]*>", "", text)

  lines = [line.strip() for line in text.split("\n") if line.strip()]
  return "\n".join(lines)


# ---------------------------------------------------------
# edge_tts 안전 실행 및 예외 처리 함수
# ---------------------------------------------------------
async def generate_audio_async(text, voice, output_path):
  import edge_tts

  communicate = edge_tts.Communicate(text, voice)
  await communicate.save(output_path)


def run_generate_audio(text, voice, output_path):
  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)
  try:
    loop.run_until_complete(generate_audio_async(text, voice, output_path))
    return True
  except Exception as e:
    st.error(
        f"⚠️ 음성 파일 생성 중 오류가 발생했습니다: {e}\n\n(참고: Streamlit"
        " Cloud 환경에서 edge-tts 이용 시 패키지 버전이나 네트워크 방화벽"
        " 문제일 수 있습니다.)"
    )
    return False
  finally:
    loop.close()


# ---------------------------------------------------------
# 입력방식 선택 탭 (PDF 업로드 / 대본 직접 입력)
# ---------------------------------------------------------
tab1, tab2 = st.tabs(
    ["📄 PDF 파일 업로드", "✏️ 대본 직접 붙여넣기 (추천)"]
)

with tab1:
  uploaded_file = st.file_uploader(
      "📂 소방 법령/요약본 PDF 파일을 업로드하세요",
      type=["pdf"],
      key="pdf_uploader",
  )
  if uploaded_file is not None:
    st.success("✅ PDF 업로드 완료!")
    if st.button("🔍 PDF 텍스트 추출 및 정제", type="primary"):
      with st.spinner("📄 PDF 분석 중..."):
        raw_text = extract_text_from_pdf(uploaded_file)
        if raw_text.strip():
          clean_pdf_text = refine_nftc_text(raw_text)
          st.session_state["script_text"] = clean_pdf_text
          st.success("✨ 대본 추출 완료! 아래 대본 박스를 확인하세요.")
        else:
          st.error("⚠️ PDF에서 텍스트를 추출할 수 없습니다.")

with tab2:
  st.markdown("💡 **제가 작성해 드린 요약 대본을 아래에 복사+붙여넣기 하세요!**")
  pasted_text = st.text_area(
      "대본 붙여넣기 상자",
      value=st.session_state.get("script_text", ""),
      height=300,
      placeholder="여기에 대본을 붙여넣으세요 (Ctrl+V)...",
      key="manual_script_input",
  )
  if pasted_text:
    st.session_state["script_text"] = pasted_text

# ---------------------------------------------------------
# 음성 생성 영역
# ---------------------------------------------------------
st.divider()

if "script_text" in st.session_state and st.session_state["script_text"].strip():
  st.subheader("🎙️ 오디오 생성하기")
  st.info(
      f"현재 준비된 대본 길이: 약 {len(st.session_state['script_text'])}자"
  )

  if st.button("🚀 이 대본으로 오디오 파일 생성하기", type="primary"):
    with st.spinner("🎙️ 고품질 음성 파일(MP3) 생성 중입니다..."):
      output_mp3 = "briefing_output.mp3"

      success = run_generate_audio(
          st.session_state["script_text"], selected_voice, output_mp3
      )

      if success and os.path.exists(output_mp3):
        st.success("✨ 오디오 브리핑 생성 완료!")
        st.audio(output_mp3, format="audio/mp3")

        with open(output_mp3, "rb") as f:
          st.download_button(
              label="📥 MP3 파일 다운로드",
              data=f,
              file_name="소방_핵심브리핑.mp3",
              mime="audio/mp3",
          )
else:
  st.info(
      "💡 PDF를 업로드하여 대본을 추출하거나, [✏️ 대본 직접 붙여넣기] 탭에 대본을"
      " 입력해 주세요."
  )
