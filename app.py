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
    Hàm quét 15 dòng đầu để tìm tiêu đề
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
    df_all, header_idx = smart_read_excel(filepath, ['phân loại', 'mã mức độ'])
    
    # Kiểm tra xem có lỗi khi đọc không
    if df_all is None: 
        return None, [], str(header_idx) # header_idx lúc này chứa thông báo lỗi
    
    # Kiểm tra cột bắt buộc
    required = ['phân loại', 'mã mức độ', 'tháng', 'nội dung nhận xét']
    missing = [c for c in required if c not in df_all.columns]
    if missing:
        return None, [], f"Thiếu cột: {', '.join(missing)}"
        
    # Lấy danh sách thời điểm (Tháng/Kỳ)
    if 'tháng' in df_all.columns:
        periods = df_all['tháng'].astype(str).str.strip().unique().tolist()
        try:
            # Sắp xếp để số hiện trước, chữ hiện sau
            periods.sort(key=lambda x: (not x[0].isdigit(), x)) 
        except:
            periods.sort()
    else:
        periods = []
        
    return df_all, periods, None

# --- GIAO DIỆN CHÍNH ---

# 1. SIDEBAR: CẤU HÌNH NGÂN HÀNG
with st.sidebar:
    st.header("⚙️ Cấu Hình")
    
    # Kiểm tra file ngân hàng
    if not os.path.exists(FILE_NGAN_HANG):
        st.warning(f"Chưa có file '{FILE_NGAN_HANG}'")
        up_bank = st.file_uploader("Upload Ngân Hàng (.xlsx)", type=['xlsx'])
        if up_bank:
            with open(FILE_NGAN_HANG, "wb") as f:
                f.write(up_bank.getbuffer())
            st.rerun() # Load lại trang sau khi upload
    
    # Load dữ liệu Ngân hàng
    df_bank = None
    if os.path.exists(FILE_NGAN_HANG):
        df_bank, periods, err = load_bank(FILE_NGAN_HANG)
        
        if err:
            st.error(f"Lỗi Ngân hàng: {err}")
            df_bank = None # Đảm bảo reset về None nếu lỗi
        elif df_bank is not None:
            st.success("✅ Đã kết nối Ngân hàng")
            # Chọn thời điểm
            selected_period = st.selectbox("📅 Chọn Thời điểm/Tháng:", periods)
            
            # Lấy danh sách môn có trong ngân hàng để dùng cho việc map cột
            available_subjects = df_bank['phân loại'].unique().tolist()

# 2. KHU VỰC CHÍNH: XỬ LÝ DANH SÁCH HỌC SINH
st.subheader("📁 Xử lý Bảng Điểm")
uploaded_hs = st.file_uploader("Tải file Bảng điểm chi tiết (.xlsx)", type=['xlsx'])

# --- ĐÂY LÀ CHỖ BẠN BỊ LỖI TRƯỚC ĐÓ, TÔI ĐÃ SỬA LẠI CẨN THẬN ---
if uploaded_hs and df_bank is not None:
    # Bắt đầu khối lệnh xử lý
    
    # Đọc file học sinh: Tìm dòng chứa "họ và tên" hoặc "stt"
    df_hs, h_idx = smart_read_excel(uploaded_hs, ['họ và tên', 'stt', 'nhận xét'])
    
    if df_hs is None: # Nếu hàm trả về None tức là lỗi
        st.error(f"Lỗi đọc file HS: {h_idx}")
    else:
        st.info(f"💡 Đã tìm thấy dòng tiêu đề ở dòng số **{h_idx + 1}**")
        st.dataframe(df_hs.head(3))
        
        st.markdown("### 🔗 Ghép cột dữ liệu")
        st.markdown("Hãy chọn xem cột trong file của bạn tương ứng với môn nào trong Ngân hàng:")
        
        # Lấy các cột trong file HS (trừ cột STT, Họ tên...) để người dùng map
        cols_hs = [c for c in df_hs.columns if 'unnamed' not in c and 'stt' not in c and 'họ' not in c and 'tên' not in c]
        
        # Tạo Form ghép cột
        mapping = {}
        cols_ui = st.columns(3)
        
        for i, col_name in enumerate(cols_hs):
            # Hiển thị trên 3 cột cho gọn
            with cols_ui[i % 3]:
                # Tự động đoán tên môn (Ví dụ: cột "toán" -> chọn môn "Toán")
                default_idx = 0
                for idx, subj in enumerate(available_subjects):
                    # Logic đoán: Nếu tên cột chứa tên môn
                    if clean_header(subj) in str(col_name).lower():
                        default_idx = idx + 1 # +1 vì index 0 là "(Bỏ qua)"
                        break
                
                # Dropdown chọn môn
                # Thêm option (Bỏ qua) ở đầu danh sách
                options = ["(Bỏ qua)"] + available_subjects
                
                # Đảm bảo index nằm trong vùng an toàn
                safe_index = default_idx if default_idx < len(options) else 0
                
                selected_subj = st.selectbox(
                    f"Cột '{col_name}' là môn:", 
                    options,
                    index=safe_index,
                    key=f"map_{col_name}"
                )
                
                if selected_subj != "(Bỏ qua)":
                    mapping[col_name] = selected_subj

        st.markdown("---")
        # NÚT XỬ LÝ
        if st.button("🚀 Tạo Lời Nhận Xét", type="primary"):
            try:
                # Lọc ngân hàng theo tháng đã chọn
                bank_filtered = df_bank[df_bank['tháng'].astype(str).str.strip() == str(selected_period).strip()]
                
                if bank_filtered.empty:
                    st.warning(f"Không có dữ liệu nhận xét nào cho tháng/kỳ: {selected_period}")
                else:
                    # Tạo Dictionary tra cứu
                    DATA = {}
                    for _, row in bank_filtered.iterrows():
                        m = str(row['phân loại']).strip()
                        c = str(row['mã mức độ']).strip()
                        t = str(row['nội dung nhận xét'])
                        if m not in DATA: DATA[m] = {}
                        if c not in DATA[m]: DATA[m][c] = []
                        DATA[m][c].append(t)
                    
                    # Xử lý từng dòng học sinh
                    df_result = df_hs.copy()
                    
                    # Duyệt qua các cột đã map
                    cols_created = []
                    for col_hs, subject_bank in mapping.items():
                        # Hàm lấy lời phê
                        def get_comment(code):
                            code = str(code).strip()
                            if subject_bank in DATA and code in DATA[subject_bank]:
                                return random.choice(DATA[subject_bank][code])
                            return "" # Không tìm thấy mã
                        
                        # Tạo cột kết quả mới
                        new_col_name = f"Nội dung {col_hs}"
                        df_result[new_col_name] = df_result[col_hs].apply(get_comment)
                        cols_created.append(new_col_name)
                    
                    st.success(f"✅ Đã xử lý xong! Các cột mới: {', '.join(cols_created)}")
                    st.dataframe(df_result.head())
                    
                    # Xuất Excel
                    output = BytesIO()
                    writer = pd.ExcelWriter(output, engine='xlsxwriter')
                    df_result.to_excel(writer, index=False)
                    writer.close()
                    
                    st.download_button(
                        label="📥 Tải Kết Quả Về Máy", 
                        data=output.getvalue(), 
                        file_name=f"KetQua_{selected_period}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
            except Exception as e:
                st.error(f"Có lỗi khi xử lý: {e}")

elif uploaded_hs is None and df_bank is not None:
    st.info("👈 Hãy tải file Bảng điểm lên để bắt đầu.")
