import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

# 設定網頁標題與配置
st.set_page_config(page_title="建築模型材料裁切規劃小工具", layout="centered")

# 🎨 【視覺美化】注入網頁樣式 (CSS)
st.markdown(
    """
    <style>
    /* 透過 nth-of-type(2) 精準鎖定每行右邊第二個欄位(數量)的背景色 */
    div[data-testid="column"]:nth-of-type(2) div[data-testid="stNumberInput"] div[data-baseweb="input"] {
        background-color: #FFF9E6 !important; /* 溫柔的淺黃色底 */
        border-color: #FFE0B2 !important;     /* 淡淡的黃橙色邊框 */
    }
    div[data-testid="column"]:nth-of-type(2) div[data-testid="stNumberInput"] div[data-baseweb="input"]:focus-within {
        border-color: #FFA726 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("建築模型材料裁切規劃小工具")
st.write("[for 生活科技課-抗震建築結構單元]")
st.write("請在下方表格輸入您需要的木條尺寸與數量。")

st.write("---")
st.subheader("📋 材料需求清單輸入")
st.write("尺寸只能到小數點後一位(若為[斜桿]請將RSAP給你的數值無條件進位到.0或.5)")
st.write("數量只能是整數")

# 建立暫存資料的清單
input_data = []

# 產生 10 行輸入框
for i in range(10):
    c1, c2 = st.columns([5.5, 4.5])
    
    with c1:
        size = st.number_input(
            f"項目 {i+1} 尺寸 (cm)", 
            min_value=0.0, 
            max_value=90.0, 
            value=0.0, 
            step=0.1, 
            format="%.1f", 
            key=f"size_{i}"
        )
    with c2:
        qty = st.number_input(
            f"項目 {i+1} 數量 (根)", 
            min_value=0, 
            max_value=100, 
            value=0, 
            step=1, 
            key=f"qty_{i}"
        )
    
    if size > 0.0 and qty > 0:
        input_data.append((size, qty))

st.write("---")
st.subheader("🛠️ 裁切排程結果")
st.write("同學記得截圖留存在你手機喔~因為接下來幾周你可能會需要再打開來查看!")

# 核心裁切排程計算與繪圖函數（支援浮點數尺寸、新增統計數據功能）
def calculate_and_draw(demands_list, stock_length=90, max_stocks=10):
    if not demands_list:
        st.info("💡 請在上方表格輸入至少一組材料尺寸與數量，系統將自動開始規劃！")
        return False

    # 1. 展開並由大到小排序所有目標尺寸
    all_items = []
    total_needed_length = 0.0  # 統計學生總共需要的木條總長度
    for length, qty in sorted(demands_list, key=lambda x: x, reverse=True):
        all_items.extend([length] * qty)
        total_needed_length += float(length) * qty
        
    # 2. 初始化 10 根 90cm 的原料木條
    stocks_remain = [float(stock_length)] * max_stocks
    stocks_layout = [[] for _ in range(max_stocks)]
    unplaced_items = []
    
    # 3. 執行最佳配對裝箱演算法 (Best Fit)
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
            
    # 4. 判斷是否超標
    if unplaced_items:
        unplaced_counts = Counter(unplaced_items)
        def fmt(n): return f"{int(n)}" if n.is_integer() else f"{n:.1f}"
        items_str = "、".join([f"{fmt(len_)}公分的{qty}根" for len_, qty in unplaced_counts.items()])
        st.error(f"材料超標，現在還有 {items_str} 排不進去，請重新修正再送出")
        return False

    # =========================================================
    # 【新增功能】計算並呈現環保與省料統計數據
    # =========================================================
    total_stock_length = float(stock_length * max_stocks)  # 總材料供應長度 = 90cm * 10 = 900cm
    total_leftover = total_stock_length - total_needed_length  # 剩餘木條總共剩幾公分
    utilization_rate = (total_needed_length / total_stock_length) * 100  # 總材料利用率 XX%
    
    # 使用 Streamlit 的 columns 做出漂亮的雙數據卡片
    metric_col1, metric_col2 = st.columns(2)
    with metric_col1:
        st.metric(label="♻️ 剩餘木條總共剩", value=f"{total_leftover:.1f} 公分")
    with metric_col2:
        st.metric(label="📈 總材料利用率高達", value=f"{utilization_rate:.1f} %")
    st.write("") # 留一點空白
    # =========================================================

    # 5. 未超標，開始繪製裁切圖
    fig, ax = plt.subplots(figsize=(10, 6))
    for i in range(max_stocks):
        y_pos = max_stocks - 1 - i
        # 繪製 90cm 原始灰色木條
        ax.barh(y_pos, stock_length, left=0, height=0.4, color='#E0E0E0', edgecolor='gray', align='center')
        
        current_left = 0.0
        for segment in stocks_layout[i]:
            # 繪製各材料區段
            ax.barh(y_pos, segment, left=current_left, height=0.4, color='#F9F9F9', edgecolor='#B0B0B0', align='center')
            
            # 標註尺寸數字
            mid_point = current_left + segment / 2
            seg_text = f"{int(segment)}" if segment.is_integer() else f"{segment:.1f}"
            ax.text(mid_point, y_pos, seg_text, ha='center', va='center', color='black', fontsize=10, weight='bold')
            
            current_left += segment
            if current_left < stock_length:
                # 繪製紅色裁切線
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

# 執行即時計算與繪圖
calculate_and_draw(input_data)
