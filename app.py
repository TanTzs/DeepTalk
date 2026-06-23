import streamlit as st
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from storage import (
    load_data, save_data, add_person,
    update_chat_records, update_person_analysis,
    update_person_history, update_global_history, delete_person,
)
from agents import analyze_relationship, chat_with_person, chat_with_global_agent
from auth import register, verify, is_admin_login, get_display_name, list_users, delete_user

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DeepTalk",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background-color: #f5f7fa; }

#MainMenu, footer, header { visibility: hidden; }

.person-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 24px 20px 18px;
    text-align: center;
    transition: all 0.25s ease;
    margin-bottom: 4px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.person-card:hover {
    border-color: #3d6bff;
    box-shadow: 0 4px 20px rgba(61,107,255,0.14);
    transform: translateY(-2px);
}

.avatar {
    width: 56px; height: 56px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; font-weight: 600; color: #fff;
    margin: 0 auto 12px; letter-spacing: 1px;
}

.tag {
    display: inline-block;
    background: #eff3ff;
    color: #3d6bff;
    border: 1px solid #c7d6ff;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 11px;
    margin: 2px 2px;
}

.health-track {
    height: 3px; border-radius: 2px;
    background: #e8edf5; margin-top: 12px; overflow: hidden;
}
.health-fill { height: 100%; border-radius: 2px; }

.section-label {
    color: #94a3b8; font-size: 11px;
    font-weight: 600; letter-spacing: 2px;
    text-transform: uppercase; margin-bottom: 12px;
}

.records-panel {
    background: #fafbfc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px;
    height: 480px;
    overflow-y: auto;
    font-size: 13px;
    line-height: 1.7;
    color: #4a5568;
    white-space: pre-wrap;
    font-family: 'SF Mono', 'Fira Code', monospace;
}

.info-box {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.stat-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.auth-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 20px;
    padding: 40px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
}

.user-row {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

hr { border-color: #e8edf5 !important; }

div[data-testid="stButton"] > button {
    border-radius: 10px !important;
    border: 1px solid #d1d9e8 !important;
    background: #ffffff !important;
    color: #4a5568 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    transition: all 0.2s;
}
div[data-testid="stButton"] > button:hover {
    border-color: #3d6bff !important;
    color: #3d6bff !important;
    background: #f5f8ff !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #2c50c7 0%, #3d6bff 100%) !important;
    border: none !important;
    color: #fff !important;
}

div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {
    background: #ffffff !important;
    border: 1px solid #d1d9e8 !important;
    color: #1e2533 !important;
    border-radius: 10px !important;
}

section[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e2e8f0 !important;
}

div[data-testid="stExpander"] {
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    background: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)


# ─── Helpers ──────────────────────────────────────────────────────────────────
def initials(name: str) -> str:
    return name[:2] if name else "?"

def health_color(score: int) -> str:
    if score >= 7: return "#22c55e"
    if score >= 4: return "#f59e0b"
    return "#ef4444"

def render_network(persons: dict):
    try:
        from pyvis.network import Network
        import streamlit.components.v1 as components

        net = Network(height="360px", width="100%", bgcolor="#f5f7fa", font_color="#4a5568")
        net.add_node("me", label="我", color="#3d6bff", size=30,
                     title="这是你", font={"size": 16, "color": "#1e2533"})

        for pid, p in persons.items():
            score = p.get("analysis", {}).get("health_score", 5)
            color = p.get("color", "#3d6bff")
            rtype = p.get("analysis", {}).get("relationship_type", "")
            net.add_node(pid, label=p["name"], color=color, size=22,
                         title=f"{p['name']} · {rtype}",
                         font={"size": 13, "color": "#1e2533"})
            net.add_edge("me", pid, width=max(1, score / 3),
                         color={"color": color, "opacity": 0.5})

        net.set_options("""{
          "nodes": {"borderWidth": 2, "shadow": true},
          "edges": {"smooth": {"type": "continuous"}},
          "physics": {
            "forceAtlas2Based": {"gravitationalConstant": -60, "springLength": 130},
            "solver": "forceAtlas2Based",
            "stabilization": {"iterations": 120}
          },
          "interaction": {"hover": true, "tooltipDelay": 100}
        }""")

        components.html(net.generate_html(), height=370, scrolling=False)
    except ImportError:
        st.info("安装 pyvis 以显示关系图：`pip install pyvis`")


# ─── Session State ─────────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "logged_in": False,
        "username": None,         # actual login username
        "is_admin": False,
        "view_as": None,          # admin: which user's data to view (None = admin panel)
        "view": "home",
        "selected_pid": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


def current_username() -> str:
    """Returns the username whose data is currently being viewed."""
    if st.session_state.is_admin and st.session_state.view_as:
        return st.session_state.view_as
    return st.session_state.username


def get_user_data(uname: str) -> dict:
    """Load user data from session state cache, falling back to disk."""
    key = f"data_{uname}"
    if st.session_state.get(key) is None:
        st.session_state[key] = load_data(uname)
    return st.session_state[key]


# ─── Auth Views ───────────────────────────────────────────────────────────────
def render_auth():
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown(
            '<div style="text-align:center;margin-bottom:32px;">'
            '<p style="font-size:32px;font-weight:700;color:#1e2533;margin:0;">🕸️ DeepTalk</p>'
            '<p style="color:#94a3b8;font-size:14px;margin-top:4px;">你的 AI 社交关系分析助手</p>'
            '</div>',
            unsafe_allow_html=True,
        )

        tab_login, tab_register = st.tabs(["登录", "注册"])

        with tab_login:
            with st.form("login_form"):
                username = st.text_input("用户名", placeholder="请输入用户名")
                password = st.text_input("密码", type="password", placeholder="请输入密码")
                submitted = st.form_submit_button("登录", type="primary", use_container_width=True)

            if submitted:
                if is_admin_login(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.is_admin = True
                    st.session_state.view_as = None
                    st.rerun()
                elif verify(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.is_admin = False
                    st.rerun()
                else:
                    st.error("用户名或密码错误")

        with tab_register:
            with st.form("register_form"):
                new_username = st.text_input("用户名", placeholder="3-20 个字符", key="reg_u")
                new_display = st.text_input("昵称（可选）", placeholder="显示名称", key="reg_d")
                new_password = st.text_input("密码", type="password", placeholder="至少 6 位", key="reg_p")
                new_password2 = st.text_input("确认密码", type="password", placeholder="再输一遍", key="reg_p2")
                reg_submitted = st.form_submit_button("注册", type="primary", use_container_width=True)

            if reg_submitted:
                if new_password != new_password2:
                    st.error("两次密码不一致")
                else:
                    ok, err = register(new_username, new_password, new_display)
                    if ok:
                        st.success("注册成功，请登录")
                    else:
                        st.error(err)


# ─── Admin Panel ───────────────────────────────────────────────────────────────
def render_admin_panel():
    st.markdown(
        '<p style="font-size:24px;font-weight:700;color:#1e2533;margin:0;">🛡️ 管理员面板</p>',
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    users = list_users()
    if not users:
        st.info("目前还没有注册用户")
        return

    st.markdown('<p class="section-label">所有用户</p>', unsafe_allow_html=True)

    for uname in users:
        udata = load_data(uname)
        n_persons = len(udata.get("persons", {}))
        display = get_display_name(uname)

        col_name, col_stat, col_view, col_del = st.columns([3, 2, 2, 1])
        with col_name:
            st.markdown(
                f'<div style="padding:8px 0;color:#1e2533;font-weight:500;">'
                f'{display} <span style="color:#94a3b8;font-size:12px;">@{uname}</span></div>',
                unsafe_allow_html=True,
            )
        with col_stat:
            st.markdown(
                f'<div style="padding:8px 0;color:#64748b;font-size:13px;">{n_persons} 个联系人</div>',
                unsafe_allow_html=True,
            )
        with col_view:
            if st.button("查看数据", key=f"view_{uname}", use_container_width=True):
                st.session_state.view_as = uname
                st.session_state.view = "home"
                st.session_state.selected_pid = None
                st.rerun()
        with col_del:
            if st.button("删除", key=f"del_{uname}", use_container_width=True):
                delete_user(uname)
                st.rerun()

        st.divider()


# ─── Main App Views ───────────────────────────────────────────────────────────
def render_home(uname: str):
    data = get_user_data(uname)
    st.session_state[f"data_{uname}"] = data
    persons = data.get("persons", {})
    global_history = data.get("global_history", [])

    # Header
    viewing_label = ""
    if st.session_state.is_admin and st.session_state.view_as:
        viewing_label = (
            f' <span style="background:#eff3ff;color:#3d6bff;border-radius:6px;'
            f'padding:2px 10px;font-size:12px;font-weight:500;">'
            f'正在查看 {get_display_name(uname)} 的数据</span>'
        )

    st.markdown(
        f'<p style="font-size:28px;font-weight:700;color:#1e2533;margin:0;">'
        f'🕸️ DeepTalk{viewing_label}</p>'
        f'<p style="color:#94a3b8;font-size:13px;margin:0;">你的 AI 社交关系分析助手</p>',
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    _, col_btn = st.columns([5, 1])
    with col_btn:
        if st.button("＋ 添加联系人", type="primary", use_container_width=True):
            st.session_state.view = "add_person"
            st.rerun()

    st.divider()

    if persons:
        st.markdown('<p class="section-label">社交关系图</p>', unsafe_allow_html=True)
        render_network(persons)
        st.divider()

        st.markdown('<p class="section-label">联系人</p>', unsafe_allow_html=True)
        cols = st.columns(min(4, len(persons)))

        for idx, (pid, person) in enumerate(persons.items()):
            analysis = person.get("analysis", {})
            tags = analysis.get("tags", [])[:3]
            score = analysis.get("health_score", 5)
            rtype = analysis.get("relationship_type", "")
            color = person.get("color", "#3d6bff")
            hcolor = health_color(score)
            tags_html = "".join(f'<span class="tag">{t}</span>' for t in tags)

            with cols[idx % min(4, len(persons))]:
                st.markdown(f"""
<div class="person-card">
  <div class="avatar" style="background:{color};">{initials(person["name"])}</div>
  <div style="color:#1e2533;font-size:16px;font-weight:600;">{person["name"]}</div>
  <div style="color:#94a3b8;font-size:12px;margin:4px 0 10px;">{rtype}</div>
  <div>{tags_html}</div>
  <div class="health-track">
    <div class="health-fill" style="width:{score*10}%;background:{hcolor};"></div>
  </div>
  <div style="color:#94a3b8;font-size:11px;margin-top:6px;">健康度 {score}/10</div>
</div>
""", unsafe_allow_html=True)
                if st.button("💬 打开", key=f"open_{uname}_{pid}", use_container_width=True):
                    st.session_state.selected_pid = pid
                    st.session_state.view = "person_detail"
                    st.rerun()

        st.divider()
    else:
        st.markdown("""
<div style="text-align:center;padding:70px 0;color:#94a3b8;">
  <div style="font-size:52px;margin-bottom:12px;">🤝</div>
  <div style="font-size:18px;color:#64748b;margin-bottom:6px;font-weight:500;">还没有联系人</div>
  <div style="font-size:13px;">点击上方「添加联系人」开始你的社交分析</div>
</div>
""", unsafe_allow_html=True)

    # Global Agent
    st.markdown('<p class="section-label">全局关系顾问</p>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#94a3b8;font-size:13px;margin-bottom:10px;">'
        '了解你所有人际关系的 AI 顾问，可以分析社交模式、提供整体建议</p>',
        unsafe_allow_html=True,
    )

    chat_box = st.container(height=260)
    with chat_box:
        if not global_history:
            st.markdown(
                '<div style="text-align:center;color:#94a3b8;padding:30px;font-size:13px;">'
                '试试问：我的社交关系整体状态如何？</div>',
                unsafe_allow_html=True,
            )
        for msg in global_history[-20:]:
            if msg["role"] == "user":
                st.chat_message("user").write(msg["content"])
            else:
                st.chat_message("assistant").write(msg["content"])

    if g_input := st.chat_input("问全局顾问…", key=f"global_chat_{uname}"):
        with st.spinner("分析中…"):
            reply = chat_with_global_agent(persons, g_input, global_history)
        global_history.append({"role": "user", "content": g_input})
        global_history.append({"role": "assistant", "content": reply})
        update_global_history(uname, data, global_history)
        st.session_state[f"data_{uname}"] = data
        st.rerun()


def render_person_detail(uname: str, pid: str):
    data = get_user_data(uname)
    st.session_state[f"data_{uname}"] = data
    persons = data.get("persons", {})

    if pid not in persons:
        st.error("联系人不存在")
        st.session_state.view = "home"
        return

    person = persons[pid]
    analysis = person.get("analysis", {})
    chat_history = person.get("chat_history", [])

    col_back, col_title, col_del = st.columns([1, 6, 1])
    with col_back:
        if st.button("← 返回", use_container_width=True):
            st.session_state.view = "home"
            st.session_state.selected_pid = None
            st.rerun()
    with col_title:
        color = person.get("color", "#3d6bff")
        score = analysis.get("health_score", 5)
        hcolor = health_color(score)
        st.markdown(
            f'<span style="display:inline-block;background:{color};border-radius:50%;'
            f'width:32px;height:32px;line-height:32px;text-align:center;'
            f'font-weight:600;color:#fff;margin-right:10px;">{initials(person["name"])}</span>'
            f'<span style="font-size:20px;font-weight:700;color:#1e2533;">{person["name"]}</span>'
            f'<span style="color:{hcolor};font-size:12px;margin-left:12px;font-weight:500;">● 健康度 {score}/10</span>',
            unsafe_allow_html=True,
        )
    with col_del:
        if st.button("🗑 删除", use_container_width=True):
            delete_person(uname, data, pid)
            st.session_state[f"data_{uname}"] = data
            st.session_state.view = "home"
            st.session_state.selected_pid = None
            st.rerun()

    st.divider()

    left, right = st.columns([4, 6], gap="large")

    with left:
        st.markdown('<p class="section-label">聊天记录</p>', unsafe_allow_html=True)
        records_text = person.get("chat_records", "")
        display_text = records_text if len(records_text) <= 4000 else records_text[-4000:]
        if len(records_text) > 4000:
            display_text = f"… (显示最近部分)\n\n{display_text}"
        st.markdown(f'<div class="records-panel">{display_text}</div>', unsafe_allow_html=True)

        st.markdown('<p class="section-label" style="margin-top:16px;">追加聊天记录</p>', unsafe_allow_html=True)
        with st.expander("上传或粘贴新聊天记录"):
            tab_up, tab_paste = st.tabs(["📁 文件", "📋 粘贴"])
            with tab_up:
                uploaded = st.file_uploader("选择 txt 文件", type=["txt"], key=f"upload_{uname}_{pid}")
            with tab_paste:
                new_text = st.text_area("粘贴聊天记录", height=140, key=f"paste_{uname}_{pid}")

            if st.button("追加并重新分析", key=f"append_{uname}_{pid}", type="primary", use_container_width=True):
                extra = uploaded.read().decode("utf-8", errors="ignore") if uploaded else new_text
                if extra:
                    with st.spinner("正在更新并重新分析…"):
                        update_chat_records(uname, data, pid, extra)
                        new_analysis = analyze_relationship(person["name"], data["persons"][pid]["chat_records"])
                        update_person_analysis(uname, data, pid, new_analysis)
                    st.session_state[f"data_{uname}"] = data
                    st.success("已更新！")
                    st.rerun()
                else:
                    st.warning("请先上传或粘贴内容")

    with right:
        st.markdown('<p class="section-label">AI 关系顾问</p>', unsafe_allow_html=True)

        tags_html = "".join(f'<span class="tag">{t}</span>' for t in analysis.get("tags", []))
        st.markdown(f"""
<div class="info-box">
  <div style="color:#94a3b8;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">关系分析</div>
  <div style="color:#2d3748;font-size:13px;line-height:1.7;">{analysis.get("summary", "暂无分析")}</div>
  <div style="margin-top:10px;">{tags_html}</div>
  <div style="color:#94a3b8;font-size:11px;margin-top:8px;">互动模式：{analysis.get("interaction_pattern", "暂无")}</div>
</div>
""", unsafe_allow_html=True)

        if st.button("🔄 重新分析关系", key=f"reanalyze_{uname}_{pid}", use_container_width=True):
            with st.spinner("分析中…"):
                new_analysis = analyze_relationship(person["name"], person["chat_records"])
                update_person_analysis(uname, data, pid, new_analysis)
            st.session_state[f"data_{uname}"] = data
            st.success("分析已更新")
            st.rerun()

        chat_box = st.container(height=300)
        with chat_box:
            if not chat_history:
                st.markdown(
                    f'<div style="text-align:center;color:#94a3b8;padding:30px;font-size:13px;">'
                    f'问问 Agent 关于你和 {person["name"]} 的关系吧</div>',
                    unsafe_allow_html=True,
                )
            for msg in chat_history:
                if msg["role"] == "user":
                    st.chat_message("user").write(msg["content"])
                else:
                    st.chat_message("assistant").write(msg["content"])

        if p_input := st.chat_input(f"问关于 {person['name']} 的问题…", key=f"chat_{uname}_{pid}"):
            with st.spinner("思考中…"):
                reply = chat_with_person(
                    person_name=person["name"],
                    chat_records=person["chat_records"],
                    analysis=analysis,
                    user_input=p_input,
                    history=chat_history,
                )
            chat_history.append({"role": "user", "content": p_input})
            chat_history.append({"role": "assistant", "content": reply})
            update_person_history(uname, data, pid, chat_history)
            st.session_state[f"data_{uname}"] = data
            st.rerun()

        if chat_history:
            if st.button("🗑 清空对话记录", key=f"clear_{uname}_{pid}", use_container_width=True):
                update_person_history(uname, data, pid, [])
                st.session_state[f"data_{uname}"] = data
                st.rerun()


def render_add_person(uname: str):
    col_back, col_title = st.columns([1, 8])
    with col_back:
        if st.button("← 返回", use_container_width=True):
            st.session_state.view = "home"
            st.rerun()
    with col_title:
        st.markdown(
            '<p style="font-size:22px;font-weight:700;color:#1e2533;margin:0;">添加联系人</p>',
            unsafe_allow_html=True,
        )

    st.divider()

    _, form_col, _ = st.columns([1, 5, 1])
    with form_col:
        with st.form("add_person_form", clear_on_submit=True):
            col_name, col_color = st.columns([3, 1])
            with col_name:
                name = st.text_input("联系人名称 *", placeholder="输入姓名或昵称")
            with col_color:
                color = st.color_picker("头像色", "#3d6bff")

            st.markdown("**聊天记录 ***")
            tab_up, tab_paste = st.tabs(["📁 上传 txt 文件", "📋 粘贴文本"])
            with tab_up:
                uploaded = st.file_uploader("选择文件", type=["txt"])
            with tab_paste:
                pasted = st.text_area("粘贴聊天记录", height=240, placeholder="将聊天记录粘贴到这里…")

            submitted = st.form_submit_button("🔍 分析并添加", type="primary", use_container_width=True)

        if submitted:
            if not name:
                st.error("请填写联系人名称")
            else:
                records = uploaded.read().decode("utf-8", errors="ignore") if uploaded else pasted
                if not records:
                    st.error("请上传或粘贴聊天记录")
                else:
                    with st.spinner(f"正在分析与 {name} 的关系…"):
                        analysis = analyze_relationship(name, records)
                    data = get_user_data(uname)
                    pid = add_person(uname, data, name, color, records, analysis)
                    st.session_state[f"data_{uname}"] = data
                    st.success(f"✅ 已添加 {name}，关系分析完成！")
                    st.balloons()
                    st.session_state.view = "home"
                    st.rerun()


# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    if st.session_state.logged_in:
        display = get_display_name(st.session_state.username) if not st.session_state.is_admin else "管理员"
        st.markdown(
            f'<p style="color:#1e2533;font-weight:600;font-size:15px;margin-bottom:4px;">👤 {display}</p>'
            f'<p style="color:#94a3b8;font-size:12px;margin-bottom:16px;">@{st.session_state.username}</p>',
            unsafe_allow_html=True,
        )

        if st.session_state.is_admin:
            if st.button("🛡 管理面板", use_container_width=True):
                st.session_state.view_as = None
                st.session_state.view = "admin"
                st.rerun()
            if st.session_state.view_as:
                if st.button("← 退出查看", use_container_width=True):
                    st.session_state.view_as = None
                    st.session_state.view = "admin"
                    st.rerun()

        st.divider()

        uname = current_username()
        if uname:
            data = get_user_data(uname)
            persons = data.get("persons", {})
            n = len(persons)
            avg = (
                sum(p.get("analysis", {}).get("health_score", 5) for p in persons.values()) / n
                if n else 0
            )
            st.markdown(f"""
<div style="display:flex;gap:10px;margin-bottom:16px;">
  <div class="stat-card" style="flex:1;">
    <div style="font-size:22px;font-weight:700;color:#3d6bff;">{n}</div>
    <div style="font-size:11px;color:#94a3b8;">联系人</div>
  </div>
  <div class="stat-card" style="flex:1;">
    <div style="font-size:22px;font-weight:700;color:#22c55e;">{avg:.1f}</div>
    <div style="font-size:11px;color:#94a3b8;">平均健康度</div>
  </div>
</div>
""", unsafe_allow_html=True)

            if persons:
                export_blob = json.dumps(data, ensure_ascii=False, indent=2)
                st.download_button(
                    "📥 导出数据备份",
                    data=export_blob,
                    file_name=f"deeptalk_{uname}_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json",
                    use_container_width=True,
                )

            imp = st.file_uploader("📤 导入数据", type=["json"], key="import_data")
            if imp:
                try:
                    imported = json.loads(imp.read())
                    save_data(uname, imported)
                    st.session_state[f"data_{uname}"] = imported
                    st.success("导入成功！")
                    st.rerun()
                except Exception as e:
                    st.error(f"导入失败：{e}")

        st.divider()
        if st.button("退出登录", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# ─── Router ───────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    render_auth()
elif st.session_state.is_admin and st.session_state.view == "admin":
    render_admin_panel()
else:
    uname = current_username()
    if not uname:
        # Admin hasn't selected a user yet
        render_admin_panel()
    elif st.session_state.view == "add_person":
        render_add_person(uname)
    elif st.session_state.view == "person_detail" and st.session_state.selected_pid:
        render_person_detail(uname, st.session_state.selected_pid)
    else:
        render_home(uname)
