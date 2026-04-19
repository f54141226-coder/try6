# %%
import streamlit as st
import random
import pandas as pd
import os

# --- 1. 頁面基本設定 ---
st.set_page_config(page_title="成大美食導航 NCKU Foodie", page_icon="🍱", layout="centered")

# 設定資料檔案 (版本更新至 v5 以適配 5 分制邏輯)
DATA_FILE = "restaurants_v5.csv"

def load_data():
    # 預設名單 (回歸 5 分制)
    default_list = [
        {"name": "元味屋", "price": 150, "rating": 4.4, "count": 1},
        {"name": "成大館", "price": 100, "rating": 4.0, "count": 1},
        {"name": "麥當勞", "price": 120, "rating": 4.2, "count": 1},
        {"name": "活力小廚", "price": 80, "rating": 4.3, "count": 1},
        {"name": "府川食堂", "price": 100, "rating": 4.5, "count": 1}
    ]
    
    if os.path.exists(DATA_FILE):
        try:
            user_data = pd.read_csv(DATA_FILE).to_dict('records')
            if not user_data:
                return default_list
            return user_data
        except:
            return default_list
    return default_list

def save_data(data):
    pd.DataFrame(data).to_csv(DATA_FILE, index=False)

if 'restaurant_db' not in st.session_state:
    st.session_state.restaurant_db = load_data()

# --- 2. 側邊欄：篩選與管理員功能 ---
with st.sidebar:
    st.title("🍔 搜尋過濾")
    budget = st.slider("💰 預算上限", 0, 500, 200, 10)
    # 篩選拉桿改回 1.0 ~ 5.0
    min_rating = st.slider("⭐ 最低評分要求 (1-5)", 1.0, 5.0, 3.5, 0.1)
    
    st.divider()
    with st.expander("🔐 管理員入口"):
        admin_pw = st.text_input("請輸入管理密碼", type="password")
        if admin_pw == "Ddiego950930":
            st.warning("管理員權限已開啟")
            if st.session_state.restaurant_db:
                all_names = [res['name'] for res in st.session_state.restaurant_db]
                target_delete = st.selectbox("選擇要刪除的餐廳", all_names)
                if st.button("❌ 刪除這家餐廳"):
                    st.session_state.restaurant_db = [res for res in st.session_state.restaurant_db if res['name'] != target_delete]
                    save_data(st.session_state.restaurant_db)
                    st.rerun()

# --- 3. 主頁面標題 ---
st.title("🍴 成大生今天吃什麼？")
st.caption("利用群眾智慧，讓校園美食評價更真實！")

# --- 4. 隨機抽選區 ---
st.divider()
if st.button("🚀 幫我選一家！", type="primary", use_container_width=True):
    filtered_list = [
        res for res in st.session_state.restaurant_db 
        if int(res['price']) <= budget and float(res['rating']) >= min_rating
    ]
    
    if filtered_list:
        selected = random.choice(filtered_list)
        st.session_state.last_pick = selected
        st.balloons()
    else:
        st.error("找不到符合條件的餐廳，試著放寬條件吧！")
        st.session_state.last_pick = None

# 顯示結果與互動評價
if 'last_pick' in st.session_state and st.session_state.last_pick:
    res = st.session_state.last_pick
    st.success(f"### 🎊 推薦你吃：**{res['name']}**")
    c1, c2, c3 = st.columns(3)
    c1.metric("預估消費", f"${res['price']}")
    c2.metric("平均評分", f"⭐ {res['rating']:.1f}")
    c3.metric("評價次數", f"{int(res['count'])} 次")
    
    map_url = f"https://www.google.com/maps/search/{res['name']}+成大"
    st.markdown(f"**[📍 點我開啟 Google 地圖導航]({map_url})**")
    
    # 造訪後給評
    st.divider()
    st.info("📣 **吃完了嗎？** 您的評價能讓數據更精準！")
    with st.expander(f"✨ 幫「{res['name']}」打分數"):
        # 評分拉桿改回 1.0 ~ 5.0
        new_score = st.slider("您的評價 (1-5 星)", 1.0, 5.0, 4.0, 0.1, key="feedback_slider")
        if st.button("提交評價"):
            for item in st.session_state.restaurant_db:
                if item['name'] == res['name']:
                    # 計算權重平均
                    item['rating'] = round((item['rating'] * item['count'] + new_score) / (item['count'] + 1), 1)
                    item['count'] += 1
                    break
            save_data(st.session_state.restaurant_db)
            st.success("感謝回饋！評分已即時更新。")
            st.rerun()

# --- 5. 新增餐廳功能 ---
st.divider()
st.subheader("📝 貢獻新餐廳")
with st.form("add_restaurant_form", clear_on_submit=True):
    name = st.text_input("餐廳名稱 (必填)")
    c1, c2 = st.columns(2)
    price = c1.number_input("平均價位 ($)", min_value=0, value=100, step=10)
    # 初始評分改回 1.0 ~ 5.0
    rating = c2.slider("初始評分 (1-5 星)", 1.0, 5.0, 4.0, 0.1)
    
    submitted = st.form_submit_button("✅ 提交餐廳資料", use_container_width=True)
    if submitted and name:
        if any(r['name'] == name for r in st.session_state.restaurant_db):
            st.warning("這家店已經在清單中囉！")
        else:
            new_entry = {"name": name, "price": int(price), "rating": float(rating), "count": 1}
            st.session_state.restaurant_db.append(new_entry)
            save_data(st.session_state.restaurant_db)
            st.toast("感謝貢獻！")
            st.rerun()

# --- 6. 數據統計與展示 ---
st.divider()
st.subheader("📊 校園美食數據")
if st.session_state.restaurant_db:
    df = pd.DataFrame(st.session_state.restaurant_db)
    with st.expander("📂 查看完整清單 (5 分制)"):
        # 設定表格顯示格式
        st.dataframe(
            df, 
            column_config={
                "name": "餐廳名稱",
                "price": st.column_config.NumberColumn("價位", format="$%d"),
                "rating": st.column_config.NumberColumn("平均評分", format="%.1f ⭐"),
                "count": "評價次數"
            },
            use_container_width=True, 
            hide_index=True
        )


