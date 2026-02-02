import streamlit as st
import pandas as pd
import time
import random # <--- Thư viện mới để chọn ngẫu nhiên
from io import BytesIO

# --- CẤU HÌNH TRANG WEB ---
st.set_page_config(
    page_title="Tool Nhận Xét Học Sinh Tiểu Học v2.0",
    page_icon="🏫",
    layout="wide"
)

# --- PHẦN 1: NGÂN HÀNG NHẬN XÉT (ĐÂY LÀ TÀI SẢN QUÝ GIÁ NHẤT CỦA BẠN) ---
# Bạn hãy thêm các câu hay ho vào trong dấu ngoặc [] nhé.
# Cấu trúc: "Môn": { "Mức độ": [Danh sách các câu] }

NGAN_HANG_NHAN_XET = {
    "Toán": {
        "Tot": [
            "Em có tư duy toán học rất tốt, tính toán nhanh và chính xác.",
            "Hoàn thành xuất sắc các bài tập, giải toán thông minh, sáng tạo.",
            "Nắm vững kiến thức, trình bày bài sạch đẹp, khoa học.",
            "Rất thông minh, tiếp thu bài nhanh, vận dụng tốt vào bài tập nâng cao.",
            "Có năng khiếu về môn Toán, tính toán cẩn thận và chính xác."
        ],
        "Dat": [
            "Em nắm được kiến thức cơ bản, làm bài đầy đủ.",
            "Cần cẩn thận hơn trong việc đặt tính và tính toán.",
            "Tiếp thu bài tốt nhưng đôi khi còn làm ẩu, cần soát lại bài kỹ hơn.",
            "Hiểu bài, làm bài đúng nhưng tốc độ còn hơi chậm.",
            "Có cố gắng trong giờ học, hoàn thành được các bài tập cơ bản."
        ],
        "CanCoGang": [
            "Cần rèn luyện thêm kỹ năng tính toán, em còn hay tính sai.",
            "Chưa thuộc hết bảng cửu chương/công thức, cần ôn tập thêm ở nhà.",
            "Cần tập trung nghe giảng hơn để hiểu bài, làm bài còn chậm.",
            "Gia đình cần phối hợp kèm thêm cho em các phép tính cơ bản."
        ]
    },
    "Tiếng Việt": {
        "Tot": [
            "Chữ viết đẹp, nắn nót. Đọc to, rõ ràng, diễn cảm.",
            "Vốn từ phong phú, viết câu gãy gọn, giàu hình ảnh.",
            "Đọc hiểu tốt, trả lời câu hỏi chính xác và tự tin.",
            "Chữ viết rất đẹp, trình bày sạch sẽ. Kỹ năng viết văn tốt.",
            "Hoàn thành xuất sắc bài học, rất chăm chỉ phát biểu."
        ],
        "Dat": [
            "Chữ viết rõ ràng nhưng chưa đều nét. Đọc bài trôi chảy.",
            "Cần chú ý lỗi chính tả khi viết, em viết còn sai dấu thanh.",
            "Đọc bài to nhưng cần ngắt nghỉ đúng dấu câu.",
            "Hoàn thành bài viết, tuy nhiên câu văn còn lủng củng.",
            "Có tiến bộ trong việc rèn chữ, cần cố gắng duy trì."
        ],
        "CanCoGang": [
            "Chữ viết còn ẩu, sai nhiều lỗi chính tả.",
            "Đọc bài còn nhỏ, đánh vần chậm, cần luyện đọc thêm ở nhà.",
            "Cần rèn luyện thêm kỹ năng viết câu cho trọn vẹn ý nghĩa.",
            "Gia đình cần đôn đốc em luyện viết và đọc bài mỗi tối."
        ]
    }
}

# --- PHẦN 2: CÁC HÀM XỬ LÝ LOGIC ---

def lay_nhan_xet_ngau_nhien(diem_so, mon_hoc):
    """
    Hàm này sẽ chọn ngẫu nhiên một câu trong ngân hàng dựa trên điểm số.
    """
    # 1. Xác định mức độ dựa trên điểm số (Logic của TT27)
    muc_do = ""
    if diem_so >= 9:
        muc_do = "Tot"
    elif diem_so >= 5:
        muc_do = "Dat"
    else:
        muc_do = "CanCoGang"
    
    # 2. Lấy danh sách câu tương ứng
    # Nếu môn học chưa có trong ngân hàng thì dùng mặc định
    if mon_hoc not in NGAN_HANG_NHAN_XET:
        return f"Đã hoàn thành môn {mon_hoc} với điểm số {diem_so}."
    
    danh_sach_cau = NGAN_HANG_NHAN_XET[mon_hoc][muc_do]
    
    # 3. Chọn ngẫu nhiên (Random)
    cau_chon = random.choice(danh_sach_cau)
    
    return cau_chon

def convert_df_to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='KetQua')
    writer.close()
    processed_data = output.getvalue()
    return processed_data

# --- PHẦN 3: GIAO DIỆN NGƯỜI DÙNG (UI) ---

st.title("🏫 Trợ Lý Nhận Xét Học Sinh v2.0")
st.markdown("### ✨ Tính năng mới: Tự động trộn câu nhận xét ngẫu nhiên")

# Sidebar
with st.sidebar:
    st.header("⚙️ Cấu hình")
    # Tự động lấy danh sách môn từ Ngân hàng dữ liệu
    ds_mon = list(NGAN_HANG_NHAN_XET.keys())
    mon_hoc_chon = st.selectbox("Chọn môn học:", ds_mon)
    
    st.markdown("---")
    st.info("💡 **Mẹo:** Mỗi lần bấm nút 'Tạo', kết quả sẽ khác nhau một chút nhờ thuật toán ngẫu nhiên.")

# Main area
uploaded_file = st.file_uploader("📂 Tải lên file Excel (Cần cột 'Họ và tên' & 'Điểm số')", type=['xlsx', 'xls'])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        
        if 'Điểm số' in df.columns:
            st.success(f"Đã tải xong danh sách {len(df)} học sinh.")
            
            # Hiển thị trước 3 dòng để check
            with st.expander("Xem dữ liệu đầu vào"):
                st.dataframe(df.head(3))

            if st.button("✨ Tạo nhận xét ngẫu nhiên ngay"):
                with st.spinner('Đang suy nghĩ lời phê cho từng em...'):
                    time.sleep(1) # Tạo cảm giác đang xử lý
                    
                    # Áp dụng hàm ngẫu nhiên
                    df['Nhận xét giáo viên'] = df['Điểm số'].apply(lambda x: lay_nhan_xet_ngau_nhien(x, mon_hoc_chon))
                
                st.balloons() # Hiệu ứng bóng bay chúc mừng
                
                st.subheader("✅ Kết quả (Đã trộn nội dung):")
                st.dataframe(df)
                
                # Nút tải về
                excel_data = convert_df_to_excel(df)
                st.download_button(
                    label="📥 Tải file kết quả về máy",
                    data=excel_data,
                    file_name=f'Nhan_xet_{mon_hoc_chon}.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                )
        else:
            st.error("⚠️ Lỗi: File Excel thiếu cột 'Điểm số'.")
            
    except Exception as e:
        st.error(f"Có lỗi: {e}")