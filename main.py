import streamlit as st
from github import Github

st.title("🕵️‍♂️ GitHub 연결 진단기")

# 1. 시크릿 정보 읽기
try:
    token = st.secrets["github"]["token"]
    repo_name = st.secrets["github"]["repo_name"]
    
    # 공백이 있는지 눈으로 확인하기 위해 앞뒤로 대괄호를 붙여서 출력
    st.write("### 1. 입력된 정보 확인")
    st.write(f"- 🔑 토큰 길이: **{len(token)}** 글자 (보통 40자여야 함)")
    st.write(f"- 📁 저장소 이름: `[{repo_name}]`")
    
    if " " in repo_name:
        st.error("🚨 저장소 이름에 공백(띄어쓰기)이 포함되어 있습니다! Secrets를 수정하세요.")
    
except Exception as e:
    st.error(f"❌ Secrets를 읽지 못했습니다: {e}")
    st.stop()

# 2. GitHub 로그인 시도
st.write("---")
st.write("### 2. GitHub 로그인 시도")
try:
    g = Github(token)
    user = g.get_user()
    login_id = user.login
    st.success(f"✅ 로그인 성공! 현재 토큰의 주인은: **{login_id}** 님입니다.")
except Exception as e:
    st.error(f"❌ 토큰 로그인 실패: {e}")
    st.info("👉 토큰 값이 잘못되었거나 삭제된 토큰입니다.")
    st.stop()

# 3. 저장소 찾기 시도
st.write("---")
st.write("### 3. 저장소 찾기 시도")
try:
    repo = g.get_repo(repo_name)
    st.success(f"✅ 저장소 발견! (`{repo.full_name}`)")
    st.balloons()
except Exception as e:
    st.error(f"❌ 저장소를 찾을 수 없습니다 (404/403 Error)")
    st.code(str(e))
    
    st.warning("👇 **체크리스트**")
    st.markdown(f"""
    1. 위에서 로그인한 **{login_id}** 님이 **`{repo_name}`** 저장소의 주인이 맞나요?
    2. 혹시 저장소 주인이 다른 사람(조직)인가요?
    3. 토큰 만들 때 **`repo`** 체크박스 진짜 체크 하셨나요? (로그인은 되는데 저장소만 못 찾으면 이게 원인 1순위)
    """)
