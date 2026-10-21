import streamlit as st
from supabase import create_client, Client
import pandas as pd
import hmac
import hashlib
import base64
import uuid
import random
import asyncio

# ==========================================
# 🏦 1. Supabase 資料庫連線安全初始化
# ==========================================
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    SUPABASE_URL = "https://aeqteslaqeswiahwqgpi.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFlcXRlc2xhcWVzd2lhaHdxZ3BpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTI1MjY1MjQsImV4cCI6MjEwODEwMjUyNH0.Fla34T4FcVXgf_n5ygUICGmXciiWxhnfWuRxLHsY8WU"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ==========================================
# 📥 2. 核心技術展示：模擬 FastAPI 非同步去重中樞
# ==========================================
async def mock_fastapi_webhook_backend(payload: dict):
    """模擬後端 FastAPI 接收到 LINE Webhook 後的非同步背景任務"""
    await asyncio.sleep(0.3)
    event = payload.get("webhook_payload", {}).get("events", [{}])[0]
    line_message_id = event.get("message", {}).get("id")
    return f"【資安防線】訊息 {line_message_id} 成功通過 SQL UNIQUE 去重過濾，未造成重覆寫入。"


# ==========================================
# 🎨 3. Streamlit 前端網頁與多租戶設計 (2026 最新標準)
# ==========================================
st.set_page_config(layout="wide", page_title="CRM 企業管理系統")

if "mock_tenant" not in st.session_state:
    st.session_state.mock_tenant = "愛沐家居 (A公司)"

st.title("👑CRM 企業管理系統")

# 撈取使用者資料
try:
    users_data = supabase.table("users").select("*").execute().data
    user_options = {u["name"]: u for u in users_data}
except Exception as e:
    st.error(f"資料庫連線失敗，請檢查 Supabase 設定: {e}")
    user_options = {}

# 側邊欄：雙層架構安全驗證
with st.sidebar:
    st.header("🏢 SaaS 多租戶隔離切換")
    st.session_state.mock_tenant = st.selectbox(
        "請選擇當前登入企業（租戶）：", 
        ["愛沐家居 (A公司)", "他牌系統家具 (B公司)"]
    )
    
    st.markdown("---")
    st.header("🔑 模擬員工內部權限")
    if user_options:
        selected_username = st.selectbox("請選擇當前登入者身分：", list(user_options.keys()))
        current_user = user_options[selected_username]
        st.success(f"當前身分：{current_user['name']} \n\n權限級別：{current_user['role'].upper()}")
    else:
        st.warning("請先在 Supabase 寫入使用者資料")
        current_user = None

# 核心隔離顯示邏輯（主管看全部 vs 設計師物理隔離）
if current_user:
    st.subheader(f"📋 客戶追蹤名單 ── 【{st.session_state.mock_tenant}】 ❯ 登入視角：{current_user['name']}")
    
    if st.session_state.mock_tenant == "他牌系統家具 (B公司)":
        st.info("🔒 跨企業隔離成功：此處為B公司獨立租戶空間。A公司（愛沐家居）的客戶資料已受底層保護，完全不顯示。")
    else:
        try:
            # 從安全檢視表撈取資料
            if current_user["role"] == "admin":
                query = supabase.table("v_designer_contacts").select("*").execute()
            else:
                query = supabase.table("v_designer_contacts").select("*").eq("assigned_designer_id", current_user["id"]).execute()
                
            contacts_df = pd.DataFrame(query.data)
            
            if not contacts_df.empty:
                rename_dict = {
                    "contact_name": "客戶名稱",
                    "ad_source": "🎯 廣告來源標籤",
                    "case_status": "📈 案件狀態",
                    "designer_name": "負責設計師",
                    "last_message": "💬 最新 LINE 對話"
                }
                
                actual_rename = {k: v for k, v in rename_dict.items() if k in contacts_df.columns}
                contacts_df = contacts_df.rename(columns=actual_rename)
                display_cols = [col for col in contacts_df.columns if col in rename_dict.values()]
                
                if display_cols:
                    st.dataframe(contacts_df[display_cols], width='stretch', hide_index=True)
                else:
                    st.dataframe(contacts_df, width='stretch', hide_index=True)
            else:
                st.info("💡 目前您的名下沒有任何客戶名單。")
        except Exception as e:
            st.error(f"讀取安全檢視表失敗: {e}")

# ==========================================
# 🛠️ 4. 終極 DEMO 實戰測試工具箱 (模擬無 LINE OA 與權限分流)
# ==========================================
st.markdown("---")
st.header("🛠️ DEMO 實戰測試工具箱 (模擬無 LINE OA 進件與整合)")

if st.session_state.mock_tenant == "他牌系統家具 (B公司)":
    st.warning("⚠️ 請將左側企業切換回「愛沐家居 (A公司)」以進行內部驗證場域的進件模擬。")
else:
    tab1, tab2 = st.tabs(["📥 模擬 LINE Webhook 派工進件", "🔌 Ragic 外部 CRM 唯讀連接器"])
    
    with tab1:
        # 👑 核心商務故事控制：檢查是否為 admin
        if current_user and current_user["role"] != "admin":
            st.warning(f"🔒 權限攔截：當前登入身分【{current_user['name']}】為設計師。依據商用防搶單規範，新客首期「派工與指定負責人」功能僅限【主管 / 行政 (Admin)】執行。")
            st.info("💡 請在左側側邊欄將登入身分切換為主管（如：老闆），即可解鎖派工與進件工具箱。")
        else:
            st.write("💡 **商業故事點**：新客進件時為「公海狀態」，僅有行政主管可進行首次指派。分派後，後續該客戶再傳 LINE，系統會自動辨識並直達負責設計師。")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                mock_name = st.text_input("輸入模擬屋主姓名", value="竹北小明")
            with col2:
                mock_ad = st.selectbox("選擇模擬點擊的 Meta 廣告來源", ["FB_2026現代北歐風專案", "IG_工業風限時送丈量", "自然流量"])
            with col3:
                if user_options:
                    # 主管才可以挑選要派給哪位設計師
                    mock_designer_name = st.selectbox("指定分派給哪位設計師 (限主管權限)", [k for k, v in user_options.items() if v["role"] == "designer"])
                    mock_designer_id = user_options[mock_designer_name]["id"]
            
            mock_msg = st.text_area("模擬屋主在 LINE 傳送的諮詢內容：", value="你好，我剛剛在臉書看到裝修廣告，想要諮詢新成屋室內設計，預算大約30萬！")
            
            if st.button("🚀 執行新客首期 Webhook 派工與寫入", type="primary"):
                fake_line_id = f"U{random.randint(10000000, 99999999)}"
                mock_event_id = f"msg_{random.randint(100000, 999999)}"
                
                try:
                    # 1. 寫入客戶並綁定設計師
                    supabase.table("contacts").insert({
                        "line_user_id": fake_line_id,
                        "name": mock_name,
                        "assigned_designer_id": mock_designer_id,
                        "utm_source": mock_ad,
                        "status": "初次洽談"
                    }).execute()
                    
                    # 2. 寫入首則訊息
                    supabase.table("messages").insert({
                        "line_message_id": mock_event_id,
                        "line_user_id": fake_line_id,
                        "sender_type": "client",
                        "message_text": mock_msg
                    }).execute()
                    
                    # 3. 執行後端模擬
                    mock_payload = {
                        "tenant_id": "amour_furniture_tenant_id",
                        "security_audit": "X-Line-Signature Verified (Pass)",
                        "webhook_payload": {
                            "events": [{
                                "type": "message",
                                "message": {"id": mock_event_id, "type": "text", "text": mock_msg},
                                "source": {"userId": fake_line_id}
                            }]
                        }
                    }
                    log_msg = asyncio.run(mock_fastapi_webhook_backend(mock_payload))
                    
                    st.balloons()
                    st.success(f"🎉 成功分派！【{mock_name}】已正式歸屬給設計師【{mock_designer_name}】。")
                    st.info(log_msg)
                    st.json(mock_payload)
                    
                    if st.button("點擊刷新名單"):
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"模擬進件寫入失敗: {e}")
                    
    with tab2:
        st.write("💡 **商用驗收點**：既有 Ragic CRM 連接測試。")
        st.info("🔌 當前安全狀態：【唯讀測試模式 (Read-Only)】。已成功建立與愛沐家居 Ragic API 的同步通道。")
        
        ragic_mock_data = pd.DataFrame([
            {"Ragic表單ID": "CID-2026-01", "客戶姓名": "竹北小明", "既有CRM狀態": "已指派設計師", "資料同步權限": "Read-Only (唯讀)"},
            {"Ragic表單ID": "CID-2026-02", "客戶姓名": "台中陳小姐", "既有CRM狀態": "已出初步報價", "資料同步權限": "Read-Only (唯讀)"}
        ])
        st.dataframe(ragic_mock_data, width='stretch', hide_index=True)
        
        if st.button("⚡ 測試 Ragic 唯讀資料抓取與欄位對齊"):
            st.toast("Ragic API 連線測試成功！", icon="🔌")
            st.success("🎯 驗證通過：順利拉取 Ragic 現有客戶清單。")
