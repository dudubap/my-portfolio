import streamlit as st
from github import Github

st.title("📂 저장소 목록 조회기")

# 1. 로그인
try:
    token = st.secrets["github"]["token"]
    g = Github(token)
    user = g.get_user()
    st.success(f"✅ 로그인 성공: {user.login}님")
except Exception as e:
    st.error(f"로그인 실패: {e}")
    st.stop()

# 2. 내 눈에 보이는 저장소 다 출력해보기
st.write("---")
st.header("👀 이 토큰으로 볼 수 있는 저장소 목록")

try:
    # 모든 저장소 가져오기 (비공개 포함)
    repos = user.get_repos()
    
    found = False
    repo_list = []
    
    for repo in repos:
        repo_list.append(repo.full_name)
        # 우리가 찾는 저장소가 있는지 확인
        if repo.full_name == st.secrets["github"]["repo_name"]:
            found = True
            st.success(f"🎉 찾았다!! -> {repo.full_name}")
            st.write("권한도 있고 이름도 정확합니다. 이제 원래 코드로 돌아가도 됩니다.")
            break
            
    if not found:
        st.error(f"❌ '{st.secrets['github']['repo_name']}' 저장소가 목록에 없습니다.")
        st.write("👇 **현재 보이는 저장소들:**")
        st.json(repo_list)
        st.warning("위 목록에 없다면 'repo' 체크박스를 체크하지 않고 토큰을 만든 것입니다.")

except Exception as e:
    st.error(f"목록 불러오기 실패: {e}")
