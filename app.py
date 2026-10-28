import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

# 設定網頁標題與手機版面配置
st.set_page_config(page_title="建築模型材料裁切規劃器", layout="centered")

st.title("建築模型材料裁切規劃小工具")
st.write("[for 松山高中-生活科技課-抗震建築結構單元]")
st.write("請在下方表格輸入您需要的木條尺寸與數量。")

st.write("---")
st.subheader("📋 材料需求清單輸入")

# 建立 10 行輸入欄位，並將資料暫存於字典中
input_data = []

# 使用 Streamlit 的 columns 功能做出左右並排的精美表格
col1, col2 = st.columns(2)
with col1:
    st.caption("📐 尺寸 (公分, cm) — 可至小數點第一位")
with col2:
    st.caption("🔢 數量 (根) — 必須為整數")

# 產生 10 行輸入框
for i in range(10):
    c1, c2 = st.columns(2)
    with c1:
        # number_input 自帶數位驗證，step=0.1 限制到小數點後一位，min_value=0.0 防止輸入負數
        size = st.number_input(
            f"項目 {i+1} 尺寸", 
            min_value=0.0, 
            max_value=90.0, 
            value=0.0, 
            step=0.1, 
            format="%.1f", 
            label_visibility="collapsed",
            key=f"size_{i}"
        )
    with c2:
        # step=1 且 value=0 確保只能輸入整數，min_value=0 防止輸入負數
        qty = st.number_input(
            f"項目 {i+1} 數量", 
            min_value=0, 
            max_value=100, 
            value=0, 
            step=1, 
            label_visibility="collapsed",
            key=f"qty_{i}"
        )
    
    # 只要尺寸與數量都大於 0，才納入計算
    if size > 0.0 and qty > 0:
        input_data.append((size, qty))

st.write("---")
st.subheader("🛠️ 裁切排程結果")
st.write("請同學記得將以下結果，用手機截圖留存，因為你接下來幾周可能還會點開查看!")

# 核心裁切排程計算與繪圖函數（支援浮點數尺寸）
def calculate_and_draw(demands_list, stock_length=90, max_stocks=10):
    # 如果學生什麼都沒填，直接溫馨提示
    if not demands_list:
        st.info("💡 請在上方表格輸入至少一組材料尺寸與數量，系統將自動開始規劃！")
        return False

    # 1. 展開並由大到小排序所有目標尺寸（支援浮點數）
    all_items = []
    for length, qty in sorted(demands_list, key=lambda x: x[0], reverse=True):
        all_items.extend([length] * qty)
        
    # 2. 初始化 10 根 90cm 的原料木條（使用 float 應對小數點）
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
        # 將浮點數尺寸格式化為顯示好看的字串（如果剛好是整數就去小數點，否則保留一位）
        def fmt(n): return f"{int(n)}" if n.is_integer() else f"{n:.1f}"
        items_str = "、".join([f"{fmt(len_)}公分的{qty}根" for len_, qty in unplaced_counts.items()])
        
        # 嚴格遵照規格要求輸出錯誤訊息
        st.error(f"材料超標，現在還有 {items_str} 排不進去，請重新修正再送出")
        return False

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
            
            # 標註尺寸數字（若是整數則顯示整數，否則顯示小數點後一位）
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
