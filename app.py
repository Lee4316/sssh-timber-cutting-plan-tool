import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from collections import Counter

# 設定網頁標題與配置
st.set_page_config(page_title="建築模型材料裁切規劃器", layout="centered")

# =========================================================
# 🎨 【萬用全域 CSS 注入】
# 1. 徹底消滅所有圖表旁邊或下方的 "字" 方框、輔助說明與替代文字小按鈕
# 2. 將統計數據卡片 (st.metric) 的字體縮小至最適合手機觀看的 1.5rem
# =========================================================
st.markdown(
    """
    <style>
    /* 暴力隱藏所有 Streamlit 圖表自帶的無障礙與輔助按鈕(不論官方怎麼改名都一律隱藏) */
    button[aria-label*="chart" i], 
    button[aria-label*="string" i],
    button[data-testid*="Caption" i],
    .stMainBlockContainer button {
        display: none !important;
    }
    /* 重新放行正常按鈕，只單純隱藏圖表小圖示 */
    .stButton button, .stDownloadButton button {
        display: inline-flex !important;
    }
    
    /* 統計數據卡片字體縮小修復 */
    [data-testid="stMetricValue"], .stMetric value {
        font-size: 1.5rem !important; 
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"], .stMetric label {
        font-size: 0.9rem !important; 
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🏗️ 建築模型材料裁切智慧規劃")
st.write("請在下方表格直接點擊輸入您需要的木條尺寸與數量。")
st.write("💡 *提示：可直接修改格子內的數字。尺寸可輸入至小數點後一位。*")

st.write("---")
st.subheader("📋 材料需求清單輸入")

# =========================================================
# 📊 【終極防呆防錯表格】使用 st.data_editor
# 徹底解決原本手機版會跑位、寬度不一與底色失效的問題！
# =========================================================
# 預先建立 10 行乾淨的初始資料框架
default_df = pd.DataFrame(
    {
        "📐 尺寸 (cm)": [0.0] * 10,
        "🔢 數量 (根)": [0] * 10
    }
)

# 渲染出一個超級適合手機操作、且防呆性極強的試算表元件
edited_df = st.data_editor(
    default_df,
    num_rows="fixed", # 固定 10 行，不能隨便新增刪除，方便課堂管理
    use_container_width=True, # 自動完美填滿手機螢幕寬度
    hide_index=True, # 隱藏最左邊的 0~9 序號，畫面更乾淨
    column_config={
        "📐 尺寸 (cm)": st.column_config.NumberColumn(
            min_value=0.0,
            max_value=90.0,
            step=0.1,
            format="%.1f", # 嚴格資料驗證：限制到小數點後一位
            required=True,
        ),
        "🔢 數量 (根)": st.column_config.NumberColumn(
            min_value=0,
            max_value=100,
            step=1,
            format="%d", # 嚴格資料驗證：強制必須為整數
            required=True,
        ),
    }
)

# 篩選出學生真正有輸入（大於0）的有效數據納入計算
input_data = []
for index, row in edited_df.iterrows():
    size_val = row["📐 尺寸 (cm)"]
    qty_val = row["🔢 數量 (根)"]
    if size_val > 0.0 and qty_val > 0:
        input_data.append((size_val, qty_val))


st.write("---")
st.subheader("🛠️ 裁切排程結果")

# 核心裁切排程計算與繪圖函數
def calculate_and_draw(demands_list, stock_length=90, max_stocks=10):
    if not demands_list:
        st.info("💡 請在上方表格輸入至少一組材料尺寸與數量，系統將自動開始規劃！")
        return False

    all_items = []
    total_needed_length = 0.0
    for length, qty in sorted(demands_list, key=lambda x: x, reverse=True):
        all_items.extend([length] * qty)
        total_needed_length += float(length) * qty
        
    stocks_remain = [float(stock_length)] * max_stocks
    stocks_layout = [[] for _ in range(max_stocks)]
    unplaced_items = []
    
    for item in all_items:
        best_idx = -1
        min_waste = float(stock_length) + 1.0
        
        for i in range(max_stocks):
            if stocks_remain[i] >= item:
                waste_after_cut = stocks_remain[i] - item
                if waste_after_cut < min_waste:
                    min_waste = waste_after_cut
                    best_idx = i
                    
        if best_idx != -1:
            stocks_remain[best_idx] -= item
            stocks_layout[best_idx].append(item)
        else:
            unplaced_items.append(item)
            
    if unplaced_items:
        unplaced_counts = Counter(unplaced_items)
        def fmt(n): return f"{int(n)}" if n.is_integer() else f"{n:.1f}"
        items_str = "、".join([f"{fmt(len_)}公分的{qty}根" for len_, qty in unplaced_counts.items()])
        st.error(f"材料超標，現在還有 {items_str} 排不進去，請重新修正再送出")
        return False

    # 計算統計數據
    total_stock_length = float(stock_length * max_stocks)
    total_leftover = total_stock_length - total_needed_length
    utilization_rate = (total_needed_length / total_stock_length) * 100
    
    metric_col1, metric_col2 = st.columns(2)
    with metric_col1:
        st.metric(label="♻️ 剩餘木條總共剩", value=f"{total_leftover:.1f} 公分")
    with metric_col2:
        st.metric(label="📈 總材料利用率高達", value=f"{utilization_rate:.1f} %")
    st.write("") 

    # 繪製裁切圖
    fig, ax = plt.subplots(figsize=(10, 6))
    for i in range(max_stocks):
        y_pos = max_stocks - 1 - i
        ax.barh(y_pos, stock_length, left=0, height=0.4, color='#E0E0E0', edgecolor='gray', align='center')
        
        current_left = 0.0
        for segment in stocks_layout[i]:
            ax.barh(y_pos, segment, left=current_left, height=0.4, color='#F9F9F9', edgecolor='#B0B0B0', align='center')
            
            mid_point = current_left + segment / 2
            seg_text = f"{int(segment)}" if segment.is_integer() else f"{segment:.1f}"
            ax.text(mid_point, y_pos, seg_text, ha='center', va='center', color='black', fontsize=10, weight='bold')
            
            current_left += segment
            if current_left < stock_length:
                ax.vlines(current_left, y_pos - 0.25, y_pos + 0.25, colors='red', linestyles='solid', linewidth=1.5)
                
        ax.text(-2, y_pos, f"木條 {i+1}", ha='right', va='center', fontsize=10, weight='bold')
        
    ax.set_xlim(-5, stock_length + 5)
    ax.set_ylim(-0.5, max_stocks - 0.5)
    ax.set_xlabel("長度 (cm)", fontsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.set_xticks(np.arange(0, stock_length + 1, 10))
    
    plt.tight_layout()
    st.pyplot(fig)
    return True

# 執行即時計算
calculate_and_draw(input_data)
