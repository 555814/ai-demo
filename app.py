import streamlit as st
import pandas as pd
import anthropic
import base64
from PIL import Image
import io

# ==========================================
# 1. 页面基本配置
# ==========================================
st.set_page_config(page_title="AI 广告素材自动化质检台", layout="wide")
st.title("🎯 唯品会 AI 广告素材质检与分析 Agent (Demo)")
st.markdown("模拟场景：批量检测 AI 生成的商品图文素材，打分并输出优化建议。")

# ==========================================
# 2. 侧边栏：配置与模拟数据
# ==========================================
with st.sidebar:
    st.header("⚙️ Agent 配置")
    # 替换为你自己的 Claude API Key
    api_key = st.text_input("输入 Anthropic API Key", type="password")
    
    st.divider()
    st.header("📊 历史投放数据分析")
    st.markdown("通过 Pandas 分析历史打分与点击率(CTR)的关系")
    
    # 使用 Pandas 快速生成一些模拟数据来秀一下你的数据素养
    mock_data = {
        "素材ID": ["A01", "A02", "A03", "A04", "A05"],
        "AI视觉风格": ["极简风", "赛博朋克", "极简风", "二次元", "极简风"],
        "Agent质检得分": [85, 42, 91, 60, 88],
        "实际点击率(CTR)": ["3.2%", "0.8%", "4.1%", "1.5%", "3.8%"]
    }
    df = pd.DataFrame(mock_data)
    st.dataframe(df, hide_index=True)
    st.caption("洞察：极简风且质检得分>80的素材，CTR表现最佳。")

# ==========================================
# 3. 主界面：素材上传与质检逻辑
# ==========================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("上传待检素材")
    uploaded_file = st.file_uploader("上传一张 AI 生成的商品图", type=["jpg", "jpeg", "png"])
    ad_copy = st.text_area("输入配套的广告文案", value="春季新款连衣裙，纯棉材质，穿上你就是仙女本仙！限时特惠，赶紧抢购！")

with col2:
    st.subheader("Agent 质检报告")
    if uploaded_file is not None:
        # 显示图片
        image = Image.open(uploaded_file)
        st.image(image, caption="待审核图片", use_column_width=True)
        
        if st.button("🚀 运行自动化质检 Agent", type="primary"):
            if not api_key:
                st.error("请先在侧边栏输入 API Key！")
            else:
                with st.spinner("Agent 正在深度分析图像与文案..."):
                    try:
                        # 图片转 Base64，准备发给 Claude
                        buffered = io.BytesIO()
                        img_to_save = image.convert("RGB") if image.mode == "RGBA" else image
                        img_to_save.save(buffered, format="JPEG")
                        img_str = base64.b64encode(buffered.getvalue()).decode()

                        # 初始化 Claude 客户端
                        client = anthropic.Anthropic(api_key=api_key)

                        # 这里是 Agent 的“灵魂”：Prompt 设计
                        prompt_text = f"""
                        你现在是唯品会的资深广告审核专家。请分析我提供的这张 AI 生成的广告图，以及配套文案："{ad_copy}"。
                        请从以下三个维度进行严格审查：
                        1. 图像幻觉：模特是否有六指、肢体扭曲、背景穿模等 AI 生成瑕疵？
                        2. 品牌调性：是否符合电商平台的审美？
                        3. 文案转化：文案是否有吸引力，是否契合图片？
                        
                        请直接输出一段结构化的 JSON 格式报告，包含：
                        "总分" (0-100), 
                        "主要缺陷" (数组), 
                        "Prompt重写建议" (教 AI 怎么重新画这张图)。
                        """

                        response = client.messages.create(
                            model="claude-3-5-sonnet-20240620",
                            max_tokens=1000,
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_str}},
                                        {"type": "text", "text": prompt_text}
                                    ]
                                }
                            ]
                        )
                        
                        st.success("质检完成！")
                        st.markdown(response.content[0].text)

                    except Exception as e:
                        st.error(f"调用 API 失败: {e}")