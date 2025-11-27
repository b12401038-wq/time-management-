# study_manager_app.py (最終整合版 - 配合組員原始程式碼)

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from dateutil import parser as dateparser
import time

# *******************************************************************
# 1. 匯入組員的核心計算函式 (optimizer.py)
# *******************************************************************
try:
    from optimizer import optimize_minutes, optimize_blocks, make_blocks
except ImportError:
    st.error("錯誤：找不到組員的核心檔案 optimizer.py。請檢查檔案是否在同資料夾。")
    st.stop()
    
# *******************************************************************
# 2. 匯入組員的提醒系統程式碼 (命名為 reminder_original.py)
#    我們將其命名為 'reminder' 以避免與內建模組衝突
# *******************************************************************
try:
    # 假設組員的原始 Tkinter 程式碼檔案命名為 reminder_original.py
    import reminder_original as reminder
    # 檢查是否包含組員程式中的關鍵函式和變數
    if 'TASK_LIST' not in dir(reminder) or 'check_time_for_task' not in dir(reminder):
        st.error("錯誤：reminder_original.py 結構不符。請確認程式碼完整且已改名為 .py 檔。")
        st.stop()
except ImportError:
    st.error("錯誤：找不到組員的提醒系統檔案 reminder_original.py (請將檔案改名並確認在同資料夾)。")
    st.stop()
    

def start_scheduler_monitoring_wrapper(final_schedule_df: pd.DataFrame):
    """
    【Streamlit 專用的轉接層】
    此函式將 Streamlit 排程結果轉換為組員程式中的 TASK_LIST 格式，並啟動監控。
    """
    
    # 清空組員程式中的全球變數 TASK_LIST
    reminder.TASK_LIST.clear() 
    now = datetime.now()
    
    # 遍歷 Streamlit 生成的排程表
    for index, row in final_schedule_df.iterrows():
        
        # 取得排程時間
        time_str = row['Start Time']
        try:
            h, m = map(int, time_str.split(':'))
            target_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
            
            # 處理時間已過的情況 (與組員原始邏輯一致)
            if target_dt <= now:
                 target_dt += timedelta(days=1)
            
            # 將任務加入組員程式中的 TASK_LIST
            reminder.TASK_LIST.append({
                'title': f"📖 {row['科目']} (30分鐘)",
                # 這裡需要硬編碼延後時間，因為組員程式是寫死的 10 分鐘
                'snooze_minutes': 10, 
                'target_time': target_dt,
                'completed': False 
            })
            
        except ValueError:
            print(f"警告：時間格式錯誤，跳過排程項目: {row['Start Time']}")

    if not reminder.TASK_LIST:
        st.warning("未設定任何任務，排程啟動失敗。")
        return

    # ----------------------------------------------------
    # 啟動多線程 (模仿組員程式 if __name__ == "__main__": 區塊的邏輯)
    # ----------------------------------------------------
    print("\n" + "=" * 40)
    print("    ✅ 已接收 Streamlit 排程，開始背景監控...")
    print("=" * 40)
    
    for task in reminder.TASK_LIST:
        print(f"- 任務啟動：{task['title']}，下次提醒：{task['target_time'].strftime('%H:%M')}")
        # 啟動獨立線程，使用組員程式中的 check_time_for_task 函式
        thread = reminder.threading.Thread(target=reminder.check_time_for_task, args=(task,))
        thread.daemon = True
        thread.start()
        
    print("\n所有任務線程已在背景運行...")

# --- Streamlit 應用程序主體 (其餘程式碼保持不變) ---

st.set_page_config(page_title="📚 讀書時間管理工具", layout="wide")

st.title("📚 讀書時間管理工具：排程設定")

# -------------------------------------------------------------------
# 步驟一：上傳檔案與數據處理
# -------------------------------------------------------------------
# ... (此處程式碼與你的原程式碼相同，不重複貼出) ...
with st.container(border=True):
    st.header("步驟 1/4：上傳課表")
    uploaded_file = st.file_uploader(
        "上傳你的課表 (CSV 或 XLSX 格式)。請確保檔案包含: course_name, credits, difficulty, exam_date 等欄位", 
        type=["csv", "xlsx"]
    )

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(uploaded_file)
            
            required_cols = ['course_name', 'credits'] 
            if not all(col in df.columns for col in required_cols):
                 st.error(f"課表缺少必要的欄位。請確認至少包含 {required_cols}。")
                 st.stop()
            
            st.success("檔案讀取成功！")
            st.session_state['df'] = df

        except Exception as e:
            st.error(f"讀取檔案時發生錯誤: {e}")
            st.stop()

# -------------------------------------------------------------------
# 步驟二：設定總時數與計算分鐘分配
# -------------------------------------------------------------------
# ... (此處程式碼與你的原程式碼相同，不重複貼出) ...
if 'df' in st.session_state:
    df = st.session_state['df']
    
    with st.container(border=True):
        st.header("步驟 2/4：計算應讀分鐘")
        
        total_minutes = st.number_input(
            "今日可讀總分鐘數 (將依此分配給各科)", 
            min_value=30, 
            value=180, 
            step=30
        )
        
        col1, col2 = st.columns(2)
        with col1:
            min_minutes = st.number_input("每科最小分鐘數", min_value=0, value=30, step=30)
        with col2:
            round_to = st.number_input("分鐘數四捨五入到 (e.g. 30)", min_value=1, value=30, step=30)

        if st.button("計算今日應讀分鐘", key="calculate_btn"):
            with st.spinner('使用 PuLP 最佳化計算中...'):
                plan_minutes_df = optimize_minutes(
                    df=df, 
                    total_minutes_today=total_minutes, 
                    min_minutes_per_course=min_minutes,
                    round_to=round_to,
                    today=date.today()
                )
            
            st.subheader("✅ 應讀分鐘分配結果")
            st.dataframe(plan_minutes_df[['minutes', 'weight']], use_container_width=True)
            st.session_state['plan_minutes_df'] = plan_minutes_df

# -------------------------------------------------------------------
# 步驟三：設定時段與生成排程表
# -------------------------------------------------------------------
# ... (此處程式碼與你的原程式碼相同，不重複貼出) ...
if 'plan_minutes_df' in st.session_state:
    
    with st.container(border=True):
        st.header("步驟 3/4：生成 30 分鐘讀書排程")
        
        col_start, col_end = st.columns(2)
        with col_start:
            start_time_str = st.text_input("讀書開始時間 (HH:MM)", "19:00")
        with col_end:
            end_time_str = st.text_input("讀書結束時間 (HH:MM)", "22:00")
        
        try:
            today_dt = datetime.now().date()
            start_dt = datetime.combine(today_dt, datetime.strptime(start_time_str, "%H:%M").time())
            end_dt = datetime.combine(today_dt, datetime.strptime(end_time_str, "%H:%M").time())
            
            if start_dt >= end_dt:
                st.error("結束時間必須晚於開始時間！")
                st.stop()

            if st.button("生成 30 分鐘排程表", key="schedule_btn"):
                with st.spinner('排程最佳化中...'):
                    
                    blocks = make_blocks(start=start_dt, end=end_dt, block_minutes=30)
                    final_schedule_df = optimize_blocks(st.session_state['df'], blocks=blocks)
                
                st.subheader("📋 最終讀書排程區塊")
                
                final_schedule_df['Start Time'] = final_schedule_df['block_time'].dt.strftime('%H:%M')
                final_schedule_df['End Time'] = (final_schedule_df['block_time'] + pd.Timedelta(minutes=30)).dt.strftime('%H:%M')
                final_schedule_df['科目'] = final_schedule_df['course_name']
                
                final_blocks_for_display = final_schedule_df[['Start Time', 'End Time', '科目']]
                st.dataframe(final_blocks_for_display, use_container_width=True)
                
                st.session_state['final_blocks'] = final_schedule_df

        except ValueError:
            st.error("請輸入有效的時間格式 (HH:MM)，例如 19:00！")
        except Exception as e:
            st.error(f"排程發生錯誤: {e}")


# -------------------------------------------------------------------
# 步驟四：啟動提醒系統 (呼叫轉接層)
# -------------------------------------------------------------------
if 'final_blocks' in st.session_state:
    
    with st.container(border=True):
        st.header("步驟 4/4：啟動提醒系統")
        
        if st.button("🚀 啟動讀書提醒系統", key="start_btn"):
            # 呼叫我們自己寫的轉接層
            start_scheduler_monitoring_wrapper(st.session_state['final_blocks']) 
            
            # 在 Streamlit 介面上給予回饋
            st.success("✅ 提醒系統已啟動！請勿關閉終端機，並留意您的電腦彈出的視窗。")
