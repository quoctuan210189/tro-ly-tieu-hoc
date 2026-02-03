import streamlit as st
import pandas as pd
import time
import random
from io import BytesIO

# --- CẤU HÌNH TRANG WEB ---
st.set_page_config(page_title="Tool Nhận Xét Học Sinh v3.0 (Pro)", page_icon="🏫", layout="wide")

# --- NGÂN HÀNG NHẬN XÉT (GIỮ NGUYÊN HOẶC BỔ SUNG THÊM) ---
NGAN_HANG_NHAN_XET = {
    "Toán": {
        "Tot": ["Tư duy toán học tốt, tính toán nhanh.", "Làm bài chính xác, trình bày sạch đẹp.", "Thông minh, tiếp thu bài rất nhanh."],
        "Dat": ["Nắm được kiến thức cơ bản.", "Cần cẩn thận hơn khi tính toán.", "Làm bài đầy đủ nhưng còn chậm."],
        "CanCoGang": ["Cần rèn luyện thêm bảng cộng trừ.", "Chưa tập trung, hay tính sai.", "Cần gia đình kèm thêm ở nhà."]
    },
    "Tiếng Việt": {
        "Tot": ["Đọc to, rõ ràng, chữ viết đẹp.", "Viết câu gãy gọn, giàu cảm xúc.", "Đọc diễn cảm, hiểu nội dung bài."],
        "Dat": ["Đọc bài trôi chảy nhưng chữ viết chưa đều.", "Cần chú ý lỗi chính tả.", "Viết câu còn đơn giản."],
        "CanCoGang": ["Đọc còn đánh vần, chữ viết ẩu.", "Sai nhiều lỗi chính tả cơ bản.", "Cần luyện đọc nhiều hơn."]
    }
}

# --- CÁC HÀM XỬ LÝ ---
def lay_nhan_xet(diem, mon_hoc):
    """Hàm lấy nhận xét ngẫu nhiên dựa trên điểm"""
    # Xử lý trường hợp điểm bị để trống hoặc không phải số
    try:
        diem = float(diem)
    except:
        return "" # Trả về rỗng nếu không có điểm

    muc_do = "CanCoGang"
    if diem >= 9: muc_do = "Tot"
    elif diem >= 5: muc_do = "Dat"
    
    # Mặc định lấy môn Toán nếu không tìm thấy môn kia
    if mon_hoc not in NGAN_HANG_NHAN_XET: mon_hoc = "Toán"
    
    return random.choice(NGAN_HANG_NHAN_XET[mon_hoc][muc_do])

def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='KetQua')
    writer.close()
    return output.getvalue()

# --- GIAO DIỆN CHÍNH ---
st.title("🏫 Tool Nhận Xét - Phiên bản 'Cân' mọi bảng điểm")

uploaded_file = st.file_uploader("1️⃣ Tải lên file Excel (.xlsx) đã Save As", type=['xlsx'])

if uploaded_file:
    try:
        # 1. Đọc file Excel để lấy danh sách Sheet (Môn học)
        xl = pd.ExcelFile(uploaded_file)
        sheet_names = xl.sheet_names
        
        st.success("Đã đọc được file! Hãy chọn thông tin bên dưới:")
        
        # CHIA CỘT ĐỂ GIAO DIỆN GỌN HƠN
        col1, col2 = st.columns(2)
        
        with col1:
            # Chọn Sheet (Môn học) - Xử lý vấn đề nhiều sheet trong hình của bạn
            selected_sheet = st.selectbox("Chọn Sheet (Môn học):", sheet_names, index=0)
            
            # Chọn dòng tiêu đề - Mặc định là dòng 7 (index 6) như trong hình bạn gửi
            header_row = st.number_input("Dòng chứa tiêu đề (STT, Họ tên...) là dòng số mấy?", 
                                       min_value=1, value=7) - 1

        # Đọc dữ liệu thật sự dựa trên Sheet và Dòng tiêu đề đã chọn
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet, header=header_row)
        
        st.markdown("---")
        st.write("▼ **Kiểm tra xem máy tính đọc đúng cột chưa:**")
        st.dataframe(df.head(3)) # Hiện 3 dòng đầu để check
        
        # 2. KHỚP CỘT DỮ LIỆU (QUAN TRỌNG NHẤT)
        st.subheader("2️⃣ Khớp thông tin cột")
        st.info("Vì file của bạn cột Họ và Tên bị tách rời, và chưa rõ cột Điểm ở đâu, hãy chỉ cho máy tính biết:")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            # Tìm cột có chữ "Họ" hoặc chọn cột C (thường là cột thứ 2, 3)
            col_ho = st.selectbox("Cột 'Họ đệm' là cột nào?", df.columns, index=1) 
        with c2:
            # Tìm cột có chữ "Tên"
            col_ten = st.selectbox("Cột 'Tên' là cột nào?", df.columns, index=2)
        with c3:
            # Cho người dùng chọn cột điểm.
            # Lưu ý: Trong hình bạn gửi tôi không thấy cột điểm, bạn hãy chọn đúng cột chứa điểm số nhé.
            col_diem = st.selectbox("Cột 'Điểm số' để xét là cột nào?", df.columns)

        # 3. NÚT XỬ LÝ
        if st.button("🚀 Tạo nhận xét ngay"):
            # Ghép họ và tên lại cho đẹp
            df['Họ và tên đầy đủ'] = df[col_ho].astype(str) + " " + df[col_ten].astype(str)
            
            # Tạo nhận xét
            # Tự động đoán môn học dựa trên tên Sheet, nếu không thì mặc định là Toán
            mon_hien_tai = "Toán"
            if "tieng_viet" in selected_sheet.lower(): mon_hien_tai = "Tiếng Việt"
            
            df['Nhận xét tự động'] = df[col_diem].apply(lambda x: lay_nhan_xet(x, mon_hien_tai))
            
            # Hiển thị kết quả
            st.success("Xong! Kéo xuống để xem kết quả.")
            st.dataframe(df[[col_ho, col_ten, col_diem, 'Nhận xét tự động']])
            
            # Tải về
            excel_data = to_excel(df)
            st.download_button(label="📥 Tải file kết quả về máy",
                               data=excel_data,
                               file_name=f'Nhan_xet_{selected_sheet}.xlsx')
            
    except Exception as e:
        st.error(f"Vẫn có lỗi nhỏ: {e}")
        st.warning("Gợi ý: Hãy chắc chắn bạn đã Save As file cũ sang đuôi .xlsx (Excel Workbook) nhé!")
