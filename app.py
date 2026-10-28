import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

# 設定網頁標題與手機版面配置
st.set_page_config(page_title="建築模型材料裁切規劃小工具", layout="centered")

st.title("建築模型材料裁切規劃小工具")
st.write("[for 松山高中-生活科技課-抗震建築結構單元]")
st.write("請在下方表格輸入您需要的木條尺寸與數量。")

st.write("---")
st.subheader("📋 材料需求清單輸入")

# 建立暫存資料的清單
input_data = []

# 產生 10 行輸入框
for i in range(10):
    # 【手機直式優化】使用等比例切分欄位，在手機上也能強制維持水平並排不跑調
    # 5.5 : 4.5 的比例既能留出空間給小數點，也能完美塞下單位
    c1, c2 = st.columns([5.5, 4.5])
    
    with c1:
        # 使用 placeholder 提示，並加上切實的明示標籤（專為手機盲區設計）
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
        # 加上「根」的明示標籤
        qty = st.number_input(
            f"項目 {i+1} 數量 (根)", 
            min_value=0, 
            max_value=100, 
            value=0, 
            step=1, 
            key=f"qty_{i}"
        )
    
    # 只要尺寸與數量都大於 0，才納入計算
    if size > 0.0 and qty > 0:
        input_data.append((size, qty))

st.write("---")
st.subheader("🛠️ 裁切排程結果")

# 核心裁切排程計算與繪圖函數（支援浮點數尺寸）
def calculate_and_draw(demands_list, stock_length=90, max_stocks=10):
    if not demands_list:
        st.info("💡 請在上方表格輸入至少一組材料尺寸與數量，系統將自動開始規劃！")
        return False

    all_items = []
    for length, qty in sorted(demands_list, key=lambda x: x, reverse=True):
        all_items.extend([length] * qty)
        
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

# 執行即時計算與繪圖
calculate_and_draw(input_data)