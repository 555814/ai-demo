"""
=============================================================
  Auto-AdScreener — 唯品会 AI 广告素材质检与优化工作流 (Demo)

  展示能力：
  - 产品经理：流程抽象、Agent 落地、数据驱动决策
  - 全栈工程：Streamlit UI、通义千问 VL 视觉 API、Pandas 分析
  - 面试项目：唯品会 AI 产品实习生 Demo

  技术栈：
  - 大模型 API：阿里云百炼 Qwen-VL-Max (通义千问视觉大模型)
  - 调用方式：OpenAI 兼容 SDK (base_url 指向 DashScope)
  - 免费额度：注册即送，支付宝登录
=============================================================
"""

import streamlit as st
import pandas as pd
import base64
from PIL import Image
import io
import json
import hashlib
import os
from datetime import datetime
from openai import OpenAI

# ==========================================
# 0. 页面基础配置 (必须在最顶部调用)
# ==========================================
st.set_page_config(
    page_title="唯品会 AI 广告素材质检与优化工作流 (Demo)",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 全局样式注入 — 现代化 UI
# ==========================================
st.markdown("""
<style>
    .main .block-container { padding-top: 1.5rem; }

    .hero-banner {
        background: linear-gradient(135deg, #FF6B9D 0%, #C44BFF 50%, #6E5CF6 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(196, 75, 255, 0.25);
    }
    .hero-banner h1 { color: white !important; font-size: 1.8rem; margin-bottom: 0.3rem; }
    .hero-banner p { color: rgba(255,255,255,0.9); font-size: 1rem; margin: 0; }

    .metric-card {
        background: linear-gradient(135deg, #f8f9ff, #fff);
        border: 1px solid #e8e8ff;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    }
    .metric-card .num { font-size: 1.8rem; font-weight: 700; color: #6E5CF6; }
    .metric-card .label { font-size: 0.85rem; color: #666; }

    section[data-testid="stSidebar"] > div { padding-top: 1rem; }

    .report-box {
        background: #fafbff;
        border: 1px solid #e0e4ff;
        border-radius: 12px;
        padding: 1.5rem;
    }

    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 20px;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 1. 用户管理系统 — 登录 / 注册
#    展示能力：完整的用户流程抽象
# ==========================================
USER_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")


def load_users():
    """加载用户数据库"""
    if os.path.exists(USER_DB_PATH):
        with open(USER_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_users(users):
    """保存用户数据库"""
    with open(USER_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def hash_password(password):
    """密码哈希（简易版，生产环境应使用 bcrypt）"""
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username, password, role="审核员"):
    """注册新用户"""
    users = load_users()
    if username in users:
        return False, "❌ 用户名已存在，请更换"
    users[username] = {
        "password": hash_password(password),
        "role": role,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    save_users(users)
    return True, "✅ 注册成功！请登录"


def authenticate(username, password):
    """验证用户登录"""
    users = load_users()
    if username not in users:
        return False, "❌ 用户不存在"
    if users[username]["password"] != hash_password(password):
        return False, "❌ 密码错误"
    return True, users[username]


# ==========================================
# 阿里云百炼 Qwen-VL Vision API 调用封装
# 使用 OpenAI 兼容格式，base_url 指向 DashScope
# 模型：qwen-vl-max（视觉能力最强）
# ==========================================
def call_qwen_vision(api_key, img_base64, system_prompt, user_prompt):
    """
    调用阿里云百炼 Qwen-VL 视觉大模型
    通过 OpenAI 兼容接口调用，无需额外 SDK
    文档: help.aliyun.com/zh/model-studio/qwen-vl-compatible-with-openai
    """
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    response = client.chat.completions.create(
        model="qwen-vl-max",
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_base64}"
                        },
                    },
                    {
                        "type": "text",
                        "text": user_prompt,
                    },
                ],
            },
        ],
        max_tokens=4096,
        temperature=0.7,
    )

    content = response.choices[0].message.content
    usage = response.usage
    return content, usage


def login_page():
    """
    登录 / 注册页面
    展示能力：产品经理对用户体验的把控 — 清晰的状态切换、表单校验
    """
    st.markdown("""
    <div style="text-align:center; padding: 3rem 0 1rem 0;">
        <div style="font-size: 3.5rem; margin-bottom: 0.5rem;">🎯</div>
        <h1 style="color: #1a1a2e; font-size: 1.6rem; margin-bottom: 0.3rem;">
            Auto-AdScreener
        </h1>
        <p style="color: #888; font-size: 0.95rem;">
            唯品会 AI 广告素材质检与优化工作流
        </p>
    </div>
    """, unsafe_allow_html=True)

    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"

    spacer_l, center, spacer_r = st.columns([1.2, 1, 1.2])

    with center:
        tab_login, tab_register = st.tabs(["🔑 登录", "📝 注册"])

        with tab_login:
            with st.form("login_form"):
                st.markdown("##### 欢迎回来")
                login_user = st.text_input("账号", placeholder="请输入用户名", key="login_u")
                login_pass = st.text_input("密码", type="password", placeholder="请输入密码", key="login_p")
                login_btn = st.form_submit_button("登 录", width="stretch", type="primary")

                if login_btn:
                    if not login_user or not login_pass:
                        st.error("请填写账号和密码")
                    else:
                        ok, result = authenticate(login_user, login_pass)
                        if ok:
                            st.session_state.logged_in = True
                            st.session_state.username = login_user
                            st.session_state.role = result["role"]
                            st.rerun()
                        else:
                            st.error(result)

            st.info("💡 首次使用请先注册账号，或使用演示账号: `demo` / `demo123`")

        with tab_register:
            with st.form("register_form"):
                st.markdown("##### 创建新账号")
                reg_user = st.text_input("设置用户名", placeholder="3-20 位字母或数字", key="reg_u")
                reg_pass = st.text_input("设置密码", type="password", placeholder="至少 6 位", key="reg_p")
                reg_pass2 = st.text_input("确认密码", type="password", placeholder="再次输入密码", key="reg_p2")
                reg_role = st.selectbox("角色", ["审核员", "设计师", "产品经理"], key="reg_r")
                reg_btn = st.form_submit_button("注 册", width="stretch", type="primary")

                if reg_btn:
                    if not reg_user or not reg_pass:
                        st.error("请填写所有字段")
                    elif len(reg_user) < 3:
                        st.error("用户名至少 3 个字符")
                    elif len(reg_pass) < 6:
                        st.error("密码至少 6 位")
                    elif reg_pass != reg_pass2:
                        st.error("两次密码不一致")
                    else:
                        ok, msg = register_user(reg_user, reg_pass, reg_role)
                        if ok:
                            st.success(msg)
                            st.balloons()
                        else:
                            st.error(msg)

    st.markdown("""
    <div style="text-align:center; margin-top: 3rem; color: #bbb; font-size: 0.8rem;">
        Auto-AdScreener v2.0 · Built for 唯品会 AI 产品实习生面试 Demo<br/>
        Powered by 通义千问 VL + Streamlit
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# 2. 核心功能页面 — 质检工作流
# ==========================================
def main_app():
    """
    主应用界面 — 登录后可见
    展示能力：Agent 自动化质检 + 数据驱动流程优化
    """

    # ------ 顶部 Banner ------
    st.markdown("""
    <div class="hero-banner">
        <h1>🎯 唯品会 AI 广告素材质检与优化工作流</h1>
        <p>
            <strong>Agent 自动化质检</strong>：利用通义千问 VL 多模态能力，自动检测 AI 生成素材中的幻觉缺陷、品牌调性偏移与文案匹配度 &nbsp;|&nbsp;
            <strong>数据驱动优化</strong>：以质检数据反哺 Prompt 优化，形成"生成→质检→优化→再生成"的闭环链路
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ------ 顶部指标栏 ------
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown('<div class="metric-card"><div class="num">1,247</div><div class="label">📸 今日质检素材数</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown('<div class="metric-card"><div class="num">94.2%</div><div class="label">✅ 质检通过率</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown('<div class="metric-card"><div class="num">3.8%</div><div class="label">📈 平均 CTR 提升</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown('<div class="metric-card"><div class="num">67ms</div><div class="label">⚡ 单图分析耗时</div></div>', unsafe_allow_html=True)

    st.markdown("")

    # ==========================================
    # 3. 左侧边栏 — 配置与数据面板
    #    展示能力：数据素养 + Pandas 数据分析能力
    # ==========================================
    with st.sidebar:
        # 用户信息卡
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea, #764ba2);
                    padding: 1.2rem; border-radius: 12px; color: white; margin-bottom: 1rem;">
            <div style="font-size: 1.3rem; font-weight: 600;">
                👤 {st.session_state.username}
            </div>
            <div style="font-size: 0.85rem; opacity: 0.85; margin-top: 0.2rem;">
                角色: {st.session_state.get('role', '审核员')} · 在线
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚪 退出登录", width="stretch"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.divider()

        # --- API 配置区 ---
        st.markdown("### ⚙️ API 配置")
        api_key = st.text_input(
            "阿里云百炼 API Key",
            type="password",
            placeholder="sk-...",
            help="在 bailian.console.aliyun.com 获取 API Key"
        )
        st.caption("🆓 注册即送免费额度，支付宝登录即可")

        st.divider()

        # --- 投放数据洞察区 (Pandas) ---
        # 展示能力：数据分析驱动的业务洞察
        st.markdown("### 📊 投放数据洞察")
        st.caption("基于历史数据的素材表现归因分析")

        mock_data = {
            "素材ID": ["VIP-001", "VIP-002", "VIP-003", "VIP-004", "VIP-005", "VIP-006", "VIP-007"],
            "核心视觉元素": [
                "春日氛围感·真人模特", "赛博朋克·合成人", "春日氛围感·户外实拍",
                "极简纯色·平铺", "春日氛围感·柔光棚拍", "暗黑高冷·AI模特",
                "日系清新·街拍"
            ],
            "Agent质检得分": [95, 38, 92, 72, 96, 45, 83],
            "曝光量": [58000, 61000, 55000, 42000, 63000, 39000, 47000],
            "点击率CTR": ["4.8%", "0.6%", "4.3%", "1.9%", "5.1%", "0.7%", "2.8%"],
            "转化率CVR": ["2.3%", "0.2%", "2.1%", "0.8%", "2.5%", "0.1%", "1.2%"],
        }
        df = pd.DataFrame(mock_data)

        def highlight_top(row):
            if row["Agent质检得分"] >= 90:
                return ["background-color: #f0fff0"] * len(row)
            elif row["Agent质检得分"] < 50:
                return ["background-color: #fff0f0"] * len(row)
            return [""] * len(row)

        st.dataframe(
            df.style.apply(highlight_top, axis=1),
            width="stretch",
            hide_index=True,
            height=300
        )

        st.success(
            "📈 **数据归因结论**：质检得分 ≥90 且包含「春日氛围感」元素的素材，"
            "平均 CTR 为 **4.7%**，CVR 为 **2.3%**，显著高于其他素材 2-5 倍。"
            "建议后续批量生成聚焦此风格方向。"
        )

        st.divider()
        st.markdown(
            '<div style="text-align:center; color:#aaa; font-size:0.75rem;">'
            'Auto-AdScreener v2.0<br/>面试 Demo · 通义千问 VL + Streamlit'
            '</div>',
            unsafe_allow_html=True
        )

    # ==========================================
    # 4. 主界面 — 双列布局：素材输入 + 质检报告
    #    展示能力：Agent 落地、流程抽象
    # ==========================================
    col1, col2 = st.columns([1, 1.2], gap="large")

    # ------ 左列：素材输入区 ------
    with col1:
        st.markdown("### 📤 素材输入区")

        uploaded_file = st.file_uploader(
            "上传 AI 生成的广告素材图",
            type=["jpg", "jpeg", "png", "webp"],
            help="支持 JPG / PNG / WebP，建议分辨率 ≥ 1024px"
        )

        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption=f"📐 {image.size[0]}×{image.size[1]}px · {image.mode} 模式", width="stretch")

        ad_copy = st.text_area(
            "📝 配套广告文案",
            value="春季新款连衣裙，符合唯品会调性，具有春日氛围感的女装，由真实模特穿着展示。",
            height=100,
            help="输入与图片配套的广告文案，Agent 会评估文案与画面的契合度"
        )

        with st.expander("🔧 高级审核参数"):
            strictness = st.slider("审核严格度", 1, 10, 7, help="越高越严格，对 AI 幻觉零容忍")
            focus_dims = st.multiselect(
                "重点审查维度",
                ["AI 幻觉检测", "品牌调性合规", "文案画面契合", "构图美学评估"],
                default=["AI 幻觉检测", "品牌调性合规", "文案画面契合"]
            )

        run_btn = st.button(
            "🚀 运行自动化质检 Agent",
            width="stretch",
            type="primary",
            disabled=not uploaded_file
        )

    # ------ 右列：质检报告与优化输出区 ------
    with col2:
        st.markdown("### 📋 Agent 质检报告")

        if not uploaded_file:
            st.markdown("""
            <div style="text-align:center; padding: 4rem 2rem;
                        background: #f8f9ff; border-radius: 16px;
                        border: 2px dashed #d0d5ff;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🖼️</div>
                <h4 style="color: #666;">等待素材上传</h4>
                <p style="color: #999; font-size: 0.9rem;">
                    请在左侧上传一张 AI 生成的广告素材图<br/>
                    Agent 将自动进行多维度质量审核
                </p>
                <div style="margin-top: 1.5rem; padding: 1rem;
                            background: white; border-radius: 10px; text-align: left;">
                    <p style="color: #666; font-size: 0.85rem; margin: 0;">
                        <strong>🔍 审核维度预览：</strong><br/>
                        ① AI 幻觉检测（多指/结构扭曲/背景穿模）<br/>
                        ② 品牌调性合规度（唯品会视觉标准）<br/>
                        ③ 文案与画面契合度评估<br/>
                        ④ Prompt 逆向优化建议输出
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        elif run_btn:
            if not api_key:
                st.error("⚠️ 请先在左侧边栏输入阿里云百炼 API Key！")
                st.info("🆓 获取方式：[bailian.console.aliyun.com](https://bailian.console.aliyun.com) → 支付宝登录 → API Key 管理")
            else:
                with st.spinner("🤖 Agent 正在通过通义千问 VL 深度分析图像与文案，请稍候..."):
                    try:
                        # ===== 核心：图片转 Base64 =====
                        # 🔧 修复 RGBA → JPEG 错误：PNG 含透明通道，JPEG 不支持
                        buffered = io.BytesIO()

                        if image.mode in ("RGBA", "P", "LA", "PA"):
                            img_for_api = image.convert("RGB")
                        else:
                            img_for_api = image

                        img_for_api.save(buffered, format="JPEG", quality=95)
                        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

                        # ===== 核心：Agent Prompt 设计 =====
                        # 展示能力：Prompt Engineering、产品业务理解
                        focus_str = "、".join(focus_dims) if focus_dims else "AI 幻觉检测、品牌调性合规、文案画面契合"

                        system_prompt = f"""你是唯品会（Vipshop）资深广告素材审核专家 Agent。
你具备以下专业能力：
- 精通 AI 生成图像的常见缺陷识别（Stable Diffusion / Midjourney / DALL-E 等模型的典型幻觉特征）
- 深谙唯品会品牌视觉规范与电商广告合规标准
- 擅长从质检结果逆向推导 Prompt 优化策略

审核严格度等级：{strictness}/10（10 为最严格）
重点审查维度：{focus_str}

请严格按照用户指定的 Markdown 格式输出质检报告。"""

                        user_prompt = f"""请对这张 AI 生成的广告素材图片进行全面质检分析。

**配套广告文案**：「{ad_copy}」

---

请按以下结构输出你的质检报告（使用 Markdown 格式）：

## 📊 整体质检评分

| 维度 | 得分(0-100) | 评级 |
|------|-------------|------|
| AI 幻觉检测 | xx | A/B/C/D |
| 品牌调性合规度 | xx | A/B/C/D |
| 文案画面契合度 | xx | A/B/C/D |
| **综合得分** | **xx** | **X** |

评级标准：A(≥90 优秀) B(≥75 良好) C(≥60 合格) D(<60 不合格)

## 🔍 缺陷诊断（请务必具体）

### 1. AI 幻觉检测
- 检查模特手指数量是否正确（是否出现六指/四指）
- 检查面部五官是否自然（眼睛对称性、鼻子嘴巴比例）
- 检查肢体结构是否合理（关节角度、身体比例）
- 检查背景是否有穿模/融合异常
- 检查服装纹理是否连续自然
- 列出所有发现的具体问题

### 2. 品牌调性合规度
- 是否符合唯品会「品质生活」定位
- 色调是否温暖有品质感
- 场景氛围是否符合春季主题
- 模特姿态是否自然得体
- 整体视觉是否达到电商平台审美标准

### 3. 文案画面契合度
- 文案描述的元素在图中是否得到体现
- 风格调性是否一致
- 目标受众感知是否匹配

## 🛠️ Prompt 逆向重写建议

基于当前素材的优缺点，请提供 **优化后的完整 Prompt**，使业务人员可以直接用于 AI 图像生成工具（如 Midjourney / Stable Diffusion），批量生成 50 张更完美的同款模特图。

请写出：
1. **优化后的正向 Prompt**（英文，包含具体的画面描述、光影、构图指令）
2. **负向 Prompt**（英文，明确排除当前发现的缺陷）
3. **关键参数建议**（推荐的模型、采样步数、CFG Scale 等）

## 📌 最终结论

用一段话总结该素材是否可以投放，以及最需要优先改进的 1-2 个方向。"""

                        # ===== 调用阿里云百炼 Qwen-VL API =====
                        report_text, usage = call_qwen_vision(
                            api_key, img_base64, system_prompt, user_prompt
                        )

                        # ===== 渲染质检报告 =====
                        st.success("✅ 质检完成！Agent 已生成完整报告")

                        st.markdown(
                            '<div class="report-box">',
                            unsafe_allow_html=True,
                        )
                        st.markdown(report_text)
                        st.markdown("</div>", unsafe_allow_html=True)

                        # Token 用量统计
                        st.divider()
                        tc1, tc2, tc3 = st.columns(3)
                        if usage:
                            tc1.metric("输入 Tokens", f"{usage.prompt_tokens:,}")
                            tc2.metric("输出 Tokens", f"{usage.completion_tokens:,}")
                        else:
                            tc1.metric("输入 Tokens", "N/A")
                            tc2.metric("输出 Tokens", "N/A")
                        tc3.metric("模型", "Qwen-VL-Max")

                    except Exception as e:
                        err_str = str(e)
                        st.error(f"❌ 调用失败，原始错误：")
                        st.code(err_str[:800], language=None)

                        if "InvalidApiKey" in err_str or "401" in err_str or "Unauthorized" in err_str:
                            st.info("🔑 API Key 无效。请前往 [bailian.console.aliyun.com](https://bailian.console.aliyun.com) 检查")
                        elif "Throttling" in err_str or "429" in err_str:
                            st.info("⏳ 请求频率超限，请稍后再试")
                        elif "InsufficientBalance" in err_str or "Arrearage" in err_str:
                            st.info("💰 账户余额不足，请前往百炼控制台充值")
                        else:
                            st.info("💡 获取 Key：[bailian.console.aliyun.com](https://bailian.console.aliyun.com) → 支付宝登录 → API-KEY 管理 → 创建")

        elif uploaded_file and not run_btn:
            st.info("👆 已上传素材，请点击左侧「运行自动化质检 Agent」按钮开始分析")


# ==========================================
# 5. 初始化演示账号 & 路由控制
# ==========================================
def init_demo_account():
    """确保演示账号存在"""
    users = load_users()
    if "demo" not in users:
        users["demo"] = {
            "password": hash_password("demo123"),
            "role": "产品经理",
            "created_at": "2025-01-01 00:00",
        }
        save_users(users)


# --- 主路由 ---
init_demo_account()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if st.session_state.logged_in:
    main_app()
else:
    login_page()
