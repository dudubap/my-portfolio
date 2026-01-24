import streamlit as st
from github import Github
import json

st.title("🕵️‍♂️ 포트폴리오 파일 정밀 진단")

# 1. Secrets 확인
try:
    token = st.secrets["github"]["token"]
    repo_name = st.secrets["github"]["repo_name"]
    st.success(f"✅ Secrets 설정 확인됨: {repo_name}")
except:
    st.error("🚨 Secrets 설정이 안 되어 있습니다!")
    st.stop()

# 2. GitHub 연결
try:
    g = Github(token)
    repo = g.get_repo(repo_name)
    st.success(f"✅ GitHub 저장소 연결 성공: {repo.full_name}")
except Exception as e:
    st.error(f"❌ GitHub 연결 실패: {e}")
    st.stop()

# 3. portfolio.json 파일 찾기
st.write("---")
st.write("### 📂 파일 확인 결과")

file_path = "portfolio.json"

try:
    # 파일 내용 가져오기 시도
    contents = repo.get_contents(file_path)
    file_content = contents.decoded_content.decode("utf-8")
    
    st.success(f"🎉 '{file_path}' 파일을 찾았습니다!")
    
    # 내용 보여주기
    st.write("👇 **파일 안에 들어있는 실제 내용:**")
    st.code(file_content, language='json')
    
    # JSON 변환 테스트
    try:
        data = json.loads(file_content)
        item_count = len(data)
        st.info(f"📊 데이터 분석: 총 **{item_count}개**의 자산이 들어있습니다.")
        
        if item_count == 0:
            st.warning("⚠️ 파일은 있지만 내용이 비어있습니다 (`[]`). 자산을 새로 추가해야 합니다.")
            
    except json.JSONDecodeError:
        st.error("❌ 파일 내용은 있는데, JSON 형식이 깨져있습니다! (오타나 콤마 확인 필요)")

except Exception as e:
    # 파일을 못 찾았을 때
    if "404" in str(e):
        st.error(f"❌ '{file_path}' 파일이 GitHub 저장소에 없습니다.")
        st.info("👉 **해결책:** 앱에서 자산을 하나 '신규 등록' 하면 자동으로 생성됩니다.")
        st.info("혹시 컴퓨터에 있는 데이터를 쓰고 싶으시다면, GitHub 웹사이트에서 파일을 업로드해야 합니다.")
    else:
        st.error(f"❌ 파일을 읽는 도중 알 수 없는 에러 발생: {e}")
