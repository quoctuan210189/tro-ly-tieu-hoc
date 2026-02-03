import streamlit as st
import pandas as pd
import random
import os
from io import BytesIO

# --- CẤU HÌNH ---
st.set_page_config(page_title="Tool Nhận Xét Tiểu Học Pro", page_icon="🏫", layout="wide")
st.title("🏫 Trợ Lý Viết Nhận Xét (Tự Động Dò Dòng Tiêu Đề)")

FILE_NGAN_HANG = "data_nhan_xet.xlsx"

# --- HÀM 1: ĐỌC EXCEL THÔNG MINH (TỰ TÌM DÒNG TIÊU ĐỀ) ---
def clean_header(name):
    """Làm sạch tên cột (xóa xuống dòng, khoảng trắng)"""
    return str(name).strip().lower().replace('\n', ' ').replace('  ', ' ')

def smart_read_excel(file_upload, keywords_to_find):
    """
    Hàm này sẽ quét 15 dòng đầu tiên.
    Nếu dòng nào chứa từ khóa (ví dụ: 'họ và tên', 'phân loại') thì lấy dòng đó làm tiêu đề.
    """
    try:
        # Đọc thử không tiêu đề
        df_temp = pd.read_excel(file_upload, header=None, nrows=15)
        
        header_index = 0
        found = False
        
        for i, row in df_temp.iterrows():
            row_str = " ".join([str(val).lower() for val in row.values])
            # Kiểm tra xem dòng này có chứa từ khóa không
            if any(k in row_str for k in keywords_to_find):
                header_index = i
                found = True
                break
        
        # Đọc lại với dòng tiêu đề tìm được
        if found:
            df = pd.read_excel(file_upload, header=header_index)
        else:
            df = pd.read_excel(file_upload, header=0) # Mặc định dòng 1
            
        # Làm sạch tên cột
        df.columns = [clean_header(c) for c in df.columns]
        return df, header_index
    except Exception as e:
        return None, str(e)

# --- HÀM 2: LOAD NGÂN HÀNG DỮ LIỆU ---
def load_bank(filepath):
    # Tìm dòng chứa chữ "phân loại" hoặc "mã mức độ"
    df_all, _ = smart_read_excel(filepath, ['phân loại', 'mã mức độ'])
    
    if isinstance(df_all, str): return None, [], df_all # Trả về lỗi
    
    # Kiểm tra cột bắt buộc
    required = ['phân loại', 'mã mức độ', 'tháng', 'nội dung nhận xét']
    missing = [c for c in required if c not in df_all.columns]
    if missing:
        return None, [], f"Thiếu cột: {', '.join(missing)}"
        
    # Lấy danh sách thời điểm (Tháng/Kỳ)
    if 'tháng' in df_all.columns:
        periods = df_all['tháng'].astype(str).str.strip().unique().tolist()
        try:
            periods.sort(key=lambda x: (not x[0].isdigit(), x)) # Sắp xếp số trước chữ
        except:
            periods.sort()
    else:
        periods = []
        
    return df_all, periods, None

# --- GIAO DIỆN ---

# 1. SIDEBAR: CẤU HÌNH NGÂN HÀNG
with st.sidebar:
    st.header("⚙️ Cấu Hình")
    if not os.path.exists(FILE_NGAN_HANG):
        st.warning(f"Chưa có file '{FILE_NGAN_HANG}'")
        up_bank = st.file_uploader("Upload Ngân Hàng (.xlsx)", type=['xlsx'])
        if up_bank:
            with open(FILE_NGAN_HANG, "wb") as f:
                f.write(up_bank.getbuffer())
            st.experimental_rerun()
    
    # Load Ngân hàng
    df_bank, periods, err = load_bank(FILE_NGAN_HANG)
    
    if err:
        st.error(f"Lỗi Ngân hàng: {err}")
    elif df_bank is not None:
        st.success("✅ Đã kết nối Ngân hàng")
        # Chọn thời điểm
        selected_period = st.selectbox("📅 Chọn Thời điểm/Tháng:", periods)
        
        # Lấy danh sách môn trong ngân hàng để dùng sau này
        available_subjects = df_bank['phân loại'].unique().tolist()

# 2. KHU VỰC CHÍNH: XỬ LÝ DANH SÁCH HỌC SINH
st.subheader("📁 Xử lý Bảng Điểm (Header dòng bất kỳ)")
uploaded_hs = st.file_uploader("Tải file Bảng điểm chi tiết (.xlsx)", type=['xlsx'])

if uploaded_hs and df_bank is not None:
    #
