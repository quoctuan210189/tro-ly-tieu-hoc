import streamlit as st
import pandas as pd
import random
import os
from io import BytesIO

# --- CẤU HÌNH ---
st.set_page_config(page_title="Tool Nhận Xét Theo Mẫu Mới", page_icon="🏫", layout="wide")
st.title("🏫 Tool Nhận Xét Học Sinh (Chuẩn Form Excel)")

FILE_NGAN_HANG = "data_nhan_xet.xlsx"

# --- HÀM 1: ĐỌC VÀ LẤY DANH SÁCH THỜI ĐIỂM ---
def load_bank_info(filepath):
    """
    Hàm này chỉ đọc file để xem có những Tháng/Kỳ nào cho người dùng chọn
    """
    try:
        # Đọc toàn bộ các sheet, nối lại thành 1 bảng to (nếu bạn chia nhiều sheet)
        # Hoặc mặc định đọc sheet đầu tiên nếu bạn để chung
        xl = pd.ExcelFile(filepath)
        df_all = pd.DataFrame()
        
        for sheet in xl.sheet_names:
            df = pd.read_excel(filepath, sheet_name=sheet)
            df_all = pd.concat([df_all, df])
            
        # Chuẩn hóa tên cột (về chữ thường, bỏ khoảng trắng thừa)
        df_all.columns = [str(c).strip().lower() for c in df_all.columns]
        
        # Kiểm tra cột bắt buộc theo ảnh bạn gửi
        required = ['phân loại', 'mã mức độ', 'tháng', 'nội dung nhận xét']
        if not all(col in df_all.columns for col in required):
            missing = [c for c in required if c not in df_all.columns]
            return None, [], f"File thiếu cột: {', '.join(missing)}"
            
        # Lấy danh sách các mốc thời gian (duy nhất) để hiện lên dropdown
        # Ví dụ: 9, 10, Giữa kỳ I, Cuối kỳ I...
        ds_thoi_diem = df_all['tháng'].astype(str).str.strip().unique().tolist()
        ds_thoi_diem.sort() # Sắp xếp lại cho đẹp
        
        return df_all, ds_thoi_diem, None
        
    except Exception as e:
        return None, [], str(e)

# --- HÀM 2: XỬ LÝ NHẬN XÉT ---
def process_data(df_hs, df_bank, selected_period):
    """
    df_hs: Danh sách học sinh
    df_bank: Ngân hàng câu nhận xét (đã load ở trên)
    selected_period: Thời điểm người dùng chọn (VD: Giữa kỳ I)
    """
    df_out = df_hs.copy()
    
    # Bước 1: Lọc Ngân hàng chỉ lấy các dòng đúng "Thời điểm" đang chọn
    # Chuyển về string và chữ thường để so sánh cho chính xác
    target = str(selected_period).strip().lower()
    bank_filtered = df_bank[df_bank['tháng'].astype(str).str.strip().str.lower() == target]
    
    if bank_filtered.empty:
        return df_out, [] # Không có dữ liệu của tháng này

    # Bước 2: Tạo từ điển tra cứu nhanh
    # Cấu trúc: DATA[Môn][Mã] = [Danh sách câu]
    DATA = {}
    for _, row in bank_filtered.iterrows():
        mon = str(row['phân loại']).strip()   # VD: Toán
        ma = str(row['mã mức độ']).strip()    # VD: T
        cau = str(row['nội dung nhận xét'])   # VD: Em học tốt...
        
        if mon not in DATA: DATA[mon] = {}
        if ma not in DATA[mon]: DATA[mon][ma] = []
        DATA[mon][ma].append(cau)

    # Bước 3: Quét qua file Danh sách học sinh để điền
    processed_cols = []
    
    # Duyệt từng cột trong file học sinh
    for col in df_out.columns:
        col_name = str(col).strip() # Tên cột (VD: Toán, Tiếng Việt)
        
        # Nếu Tên cột này CÓ xuất hiện trong cột "Phân loại" của file Excel
        if col_name in DATA:
            processed_cols.append(col_name)
            
            # Hàm con: Lấy câu nhận xét cho 1 học sinh
            def get_comment(student_code):
                student_code = str(student_code).strip() # VD: T, H, C
                
                # Nếu mã của HS có trong ngân hàng đề
                if student_code in DATA[col_name]:
                    return random.choice(DATA[col_name][student_code])
                else:
                    return "" # Không tìm thấy mã hoặc mã lạ
            
            # Tạo cột mới: "Nhận xét [Tên môn]"
            df_out[f"Nhận xét {col_name}"] = df_out[col].apply(get_comment)
            
    return df_out, processed_cols

# --- GIAO DIỆN STREAMLIT ---

# 1. KIỂM TRA FILE NGÂN HÀNG
if not os.path.exists(FILE_NGAN_HANG):
    st.warning(f"⚠️ Chưa thấy file '{FILE_NGAN_HANG}'. Vui lòng upload file Excel mẫu (4 cột: Phân loại | Mã mức độ | Tháng | Nội dung nhận xét)")
    uploaded_bank = st.file_uploader("Upload Ngân hàng (.xlsx)", type=['xlsx'])
    if uploaded_bank:
        # Lưu tạm file để đọc
        with open(FILE_NGAN_HANG, "wb") as f:
            f.write(uploaded_bank.getbuffer())
        st.experimental_rerun()
else:
    # 2. ĐỌC DỮ LIỆU & HIỆN BỘ CHỌN THỜI ĐIỂM
    df_bank_all, list_periods, err = load_bank_info(FILE_NGAN_HANG)
    
    if err:
        st.error(f"Lỗi đọc file Ngân hàng: {err}")
    else:
        st.success(f"✅ Đã kết nối Ngân hàng dữ liệu.")
        
        st.markdown("---")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.header("1. Cấu hình")
            # Dropdown này tự động lấy từ cột 'Tháng' trong file Excel của bạn
            selected_period = st.selectbox("Chọn Thời điểm / Tháng:", list_periods)
            st.info(f"Đang dùng bộ nhận xét: **{selected_period}**")

        with col2:
            st.header("2. Danh sách Học sinh")
            uploaded_hs = st.file_uploader("Tải file điểm/mức đạt (Excel)", type=['xlsx'])

        # 3. XỬ LÝ
        if uploaded_hs:
            st.markdown("---")
            if st.button("🚀 Tạo Nhận Xét Ngay", type="primary"):
                try:
                    df_hs = pd.read_excel(uploaded_hs)
                    
                    with st.spinner("Đang lọc dữ liệu và viết lời phê..."):
                        df_result, cols_done = process_data(df_hs, df_bank_all, selected_period)
                    
                    if cols_done:
                        st.balloons()
                        st.success(f"Đã xong! Đã viết nhận xét cho các môn: {', '.join(cols_done)}")
                        
                        # Hiện kết quả
                        st.dataframe(df_result.head())
                        
                        # Tải về
                        output = BytesIO()
                        writer = pd.ExcelWriter(output, engine='xlsxwriter')
                        df_result.to_excel(writer, index=False)
                        writer.close()
                        
                        file_name_download = f"KetQua_{str(selected_period).replace(' ', '_')}.xlsx"
                        st.download_button(
                            label="📥 Tải file kết quả về máy",
                            data=output.getvalue(),
                            file_name=file_name_download,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.warning("Không tìm thấy môn học nào trùng khớp! Hãy kiểm tra lại tên cột trong file Danh sách có giống cột 'Phân loại' không.")
                        
                except Exception as e:
                    st.error(f"Có lỗi xảy ra: {e}")
