import streamlit as st
import asyncio
import pdfplumber
import edge_tts
import os

# 페이지 설정
st.set_page_config(page_title="소방 오디오 브리퍼", page_icon="🎧", layout="centered")

st.title("🎧 나만의 소방 오디오 브리퍼")
st.markdown("수험서나 법령 PDF를 올리면, **잡담 0% 핵심 수치·조항 위주**의 깨끗한 오디오 브리핑 파일로 변환해 드립니다.")

# 사이드바 설정 (목소리 선택)
st.sidebar.header("⚙️ 음성 설정")
voice_option = st.sidebar.selectbox(
    "AI 음성 선택",
    (
        "ko-KR-SunHiNeural (차분한 여성 톤)",
        "ko-KR-InJoonNeural (신뢰감 있는 남성 톤)"
    )
)
selected_voice = voice_option.split(" ")[0]

# 파일 업로드
uploaded_file = st.file_uploader("📂 소방 법령/요약본 PDF 파일을 업로드하세요", type=["pdf"])

def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            extracted = page.extract_text()
            if extracted:
                text += f"\n[페이지 {page_num}]\n" + extracted + "\n"
    return text

def format_text_for_speech(raw_text):
    lines = raw_text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("Page") and not line.isdigit():
            cleaned_lines.append(line)
    return " ".join(cleaned_lines)

async def generate_audio(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

if uploaded_file is not None:
    st.success("✅ 파일 업로드 완료!")
    
    if st.button("🚀 오디오 브리핑 생성하기", type="primary"):
        with st.spinner("📄 PDF 텍스트를 분석하고 고품질 음성으로 변환 중입니다..."):
            # 1. 텍스트 추출
            raw_text = extract_text_from_pdf(uploaded_file)
            
            if not raw_text.strip():
                st.error("⚠️ PDF에서 텍스트를 추출할 수 없습니다. (이미지 스캔본인지 확인해주세요)")
            else:
                # 2. 텍스트 정돈
                clean_text = format_text_for_speech(raw_text)
                
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
                        mime="audio/mp3"
                    )