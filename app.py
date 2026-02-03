import streamlit as st
import pandas as pd
import random
import os
from io import BytesIO

# --- CẤU HÌNH ---
st.set_page_config(page_title="Tool Nhận Xét Form Excel", page_icon="🏫", layout="wide")
st.title("🏫 Tool Nhận Xét Học Sinh (Chuẩn Form Excel)")

FILE_NGAN_HANG = "data_nhan_xet.xlsx"

# --- HÀM 1: ĐỌC FILE THÔNG MINH (TỰ TÌM TIÊU ĐỀ) ---
def clean_column_name(name):
    """Hàm làm sạch tên cột: Xóa xuống dòng, xóa khoảng trắng thừa"""
    return str(name).strip().lower().replace('\n', ' ').replace('  ', ' ')

def load_bank_info(filepath):
    try:
        xl = pd.ExcelFile(filepath)
        df_all = pd.DataFrame()
        
        for sheet in xl.sheet_names:
            # 1. Đọc thử không có tiêu đề để tìm xem dòng tiêu đề nằm ở đâu
            df_temp = pd.read_excel(filepath, sheet_name=sheet, header=None, nrows=10)
            
            header_row_index = 0
            found_header = False
            
            # Quét từng dòng để tìm chữ "phân loại"
            for i, row in df_temp.iterrows():
                # Chuyển cả dòng thành chuỗi thường để tìm
                row_str = " ".join([str(val).lower() for val in row.values])
                if "phân loại" in row_str and "mã mức" in row_str:
                    header_row_index = i
                    found_header = True
                    break
            
            # 2. Đọc lại dữ liệu thật với dòng tiêu đề vừa tìm được
            if found_header:
                df = pd.read_excel(filepath, sheet_name=sheet, header=header_row_index)
            else:
                # Nếu không tìm thấy, cứ đọc dòng 0 (mặc định)
                df = pd.read_excel(filepath, sheet_name=sheet, header=0)

            # 3. Chuẩn hóa tên cột (Quan trọng: Xử lý vụ Alt+Enter)
            df.columns = [clean_column_name(c) for c in df.columns]
            
            # Gộp vào bảng chung
            df_all = pd.concat([df_all, df])
            
        # Kiểm tra cột bắt buộc
        # Lưu ý: Tên cột ở đây phải khớp với tên bạn đã clean ở trên (viết thường, không dấu xuống dòng)
        required = ['phân loại', 'mã mức độ', 'tháng', 'nội dung nhận xét']
        
        # Check kỹ từng cột xem thiếu cái nào
        missing = [c for c in required if c not in df_all.columns]
        if missing:
            return None, [], f"Tìm thấy tiêu đề ở dòng {header_row_index + 1} nhưng vẫn thiếu cột: {', '.join(missing)}. (Hãy kiểm tra chính tả)"
            
        # Lấy danh sách thời điểm
        if 'tháng' in df_all.columns:
            ds_thoi_diem = df_all['tháng'].dropna().astype(str).apply(lambda x: x.strip()).unique().tolist()
            # Sắp xếp logic (đưa số lên trước, chữ ra sau)
            try:
                ds_thoi_diem.sort(key=lambda x: (not x.isnumeric(), x))
            except:
                ds_thoi_diem.sort()
        else:
            ds_thoi_diem = []
        
        return df_all, ds_thoi_diem, None
        
    except Exception as e:
        return None, [], str(e)

# --- HÀM 2: XỬ LÝ NHẬN XÉT ---
def process_data(df_hs, df_bank, selected_period):
    df_out = df_hs.copy()
    
    # Chuẩn hóa thời điểm chọn
    target = str(selected_period).strip().lower()
    
    # Lọc ngân hàng theo thời điểm
    # Lưu ý: Cột 'tháng' trong df_bank đã được clean tên, nhưng dữ liệu bên trong cần ép kiểu
    mask = df_bank['tháng'].astype(str).str.strip().str.lower() == target
    bank_filtered = df_bank[mask]
    
    if bank_filtered.empty:
        return df_out, [] 

    # Tạo từ điển tra cứu
    DATA = {}
    for _, row in bank_filtered.iterrows():
        # Lấy tên cột chính xác từ file Excel
        mon = str(row['phân loại']).strip()   
        ma = str(row['mã mức độ']).strip()
        cau = str(row['nội dung nhận xét'])
        
        if mon not in DATA: DATA[mon] = {}
        if ma not in DATA[mon]: DATA[mon][ma] = []
        DATA[mon][ma].append(cau)

    processed_cols = []
    
    for col in df_out.columns:
        col_name = str(col).strip() 
        
        # Kiểm tra xem tên cột trong file HS có trùng với 'Phân loại' không
        if col_name in DATA:
            processed_cols.append(col_name)
            
            def get_comment(student_code):
                student_code = str(student_code).strip()
                if student_code in DATA[col_name]:
                    return random.choice(DATA[col_name][student_code])
                return ""
            
            df_out[f"Nhận xét {col_name}"] = df_out[col].apply(get_comment)
            
    return df_out, processed_cols

# --- GIAO DIỆN ---
if not os.path.exists(FILE_NGAN_HANG):
    st.warning(f"⚠️ Chưa thấy file '{FILE_NGAN_HANG}' cạnh file code.")
    uploaded_bank = st.file_uploader("Upload Ngân hàng (.xlsx)", type=['xlsx'])
    if uploaded_bank:
        with open(FILE_NGAN_HANG, "wb") as f:
            f.write(uploaded_bank.getbuffer())
        st.experimental_rerun()
else:
    # Load Data với hàm mới
    df_bank_all, list_periods, err = load_bank_info(FILE_NGAN_HANG)
    
    if err:
        st.error(f"❌ Lỗi đọc file Ngân hàng: {err}")
        st.info("💡 Gợi ý: Hãy mở file Excel, kiểm tra xem tên cột có đúng chính tả: 'Phân loại', 'Mã mức độ', 'Tháng', 'Nội dung nhận xét' không.")
    else:
        st.success(f"✅ Đã kết nối thành công! Tìm thấy {len(list_periods)} mốc thời gian.")
        
        st.markdown("---")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.header("1. Cấu hình")
            if list_periods:
                selected_period = st.selectbox("Chọn Thời điểm / Tháng:", list_periods)
                st.info(f"Đang dùng bộ câu mẫu: **{selected_period}**")
            else:
                st.warning("Không tìm thấy dữ liệu trong cột 'Tháng'.")
                selected_period = None

        with col2:
            st.header("2. Danh sách Học sinh")
            uploaded_hs = st.file_uploader("Tải file danh sách lớp", type=['xlsx'])

        if uploaded_hs and selected_period:
            st.markdown("---")
            if st.button("🚀 Viết Nhận Xét", type="primary"):
                try:
                    df_hs = pd.read_excel(uploaded_hs)
                    
                    with st.spinner("Đang xử lý..."):
                        df_result, cols_done = process_data(df_hs, df_bank_all, selected_period)
                    
                    if cols_done:
                        st.balloons()
                        st.success(f"Đã xong! Các môn được nhận xét: {', '.join(cols_done)}")
                        
                        output = BytesIO()
                        writer = pd.ExcelWriter(output, engine='xlsxwriter')
                        df_result.to_excel(writer, index=False)
                        writer.close()
                        
                        file_name_dl = f"KetQua_{str(selected_period).replace(' ', '_')}.xlsx"
                        st.download_button("📥 Tải kết quả về máy", data=output.getvalue(), file_name=file_name_dl, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    else:
                        st.warning(f"⚠️ Không tìm thấy môn nào khớp! Hãy kiểm tra file Danh sách học sinh xem tiêu đề cột (ví dụ 'Toán') có giống hệt cột 'Phân loại' trong file Ngân hàng không.")
                        
                except Exception as e:
                    st.error(f"Lỗi: {e}")
