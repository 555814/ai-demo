import streamlit as st
import json
import hashlib
import os

# 用户数据文件
USER_DB = os.path.join(os.path.dirname(__file__), "users.json")


def load_users():
    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as f:
            return json.load(f)
    return {}


def save_users(users):
    with open(USER_DB, "w") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


st.set_page_config(page_title="登录系统", layout="centered")
st.title("登录系统")

# 初始化 session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "page" not in st.session_state:
    st.session_state.page = "login"

# 已登录界面
if st.session_state.logged_in:
    st.success(f"欢迎回来，{st.session_state.username}！")
    st.balloons()
    if st.button("退出登录"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

else:
    # 登录 / 注册 切换
    tab1, tab2 = st.tabs(["登录", "注册"])

    with tab1:
        st.subheader("账号登录")
        login_user = st.text_input("账号", key="login_user")
        login_pass = st.text_input("密码", type="password", key="login_pass")

        if st.button("登录", type="primary"):
            if not login_user or not login_pass:
                st.error("请输入账号和密码")
            else:
                users = load_users()
                if login_user in users and users[login_user] == hash_password(login_pass):
                    st.session_state.logged_in = True
                    st.session_state.username = login_user
                    st.rerun()
                else:
                    st.error("账号或密码错误")

    with tab2:
        st.subheader("注册新账号")
        reg_user = st.text_input("设置账号", key="reg_user")
        reg_pass = st.text_input("设置密码", type="password", key="reg_pass")
        reg_pass2 = st.text_input("确认密码", type="password", key="reg_pass2")

        if st.button("注册", type="primary"):
            if not reg_user or not reg_pass:
                st.error("账号和密码不能为空")
            elif len(reg_pass) < 6:
                st.error("密码至少6位")
            elif reg_pass != reg_pass2:
                st.error("两次密码不一致")
            else:
                users = load_users()
                if reg_user in users:
                    st.error("该账号已存在")
                else:
                    users[reg_user] = hash_password(reg_pass)
                    save_users(users)
                    st.success("注册成功！请切换到登录页面登录")
