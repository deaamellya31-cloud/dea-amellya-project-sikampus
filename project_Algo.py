# db_sikampus.py
import sqlite3

DATABASE_NAME = 'sikampus_db.sqlite'
PROJECT_COST_PER_CREDIT = 200000  # Biaya Proyek Simulasi per SKS

def init_db():
    """Menginisialisasi tabel database dan mengisi data awal."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # --- 1. Modules (Modul/Mata Pelajaran) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Modules (
            id INTEGER PRIMARY KEY,
            module_code TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            credits INTEGER NOT NULL,
            max_slots INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Open', 'Closed'))
        )
    ''')
    
    # --- 2. Scholars (Akademisi/Mahasiswa) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Scholars (
            id INTEGER PRIMARY KEY,
            scholar_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            contact_email TEXT NOT NULL,
            program TEXT NOT NULL
        )
    ''')

    # --- 3. ProjectRegistrations (Registrasi Proyek) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ProjectRegistrations (
            id INTEGER PRIMARY KEY,
            module_id INTEGER,
            scholar_id_fk INTEGER,
            reg_date TEXT NOT NULL,
            total_fee REAL NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Registered', 'InProgress', 'Completed', 'Canceled')),
            final_score TEXT,
            FOREIGN KEY (module_id) REFERENCES Modules(id),
            FOREIGN KEY (scholar_id_fk) REFERENCES Scholars(id)
        )
    ''')

    conn.commit()
    conn.close()
    
    # Mengisi data awal
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Modules")
    if cursor.fetchone()[0] == 0:
        initial_modules = [
            ('PRJ101', 'Proyek Analisis Data', 4, 20, 'Open'),
            ('PRJ205', 'Riset Kecerdasan Buatan', 6, 15, 'Open'),
            ('PRJ310', 'Desain Infrastruktur Cloud', 3, 25, 'Closed'),
            ('PRJ400', 'Seminar Proposal Studi', 2, 40, 'Open'),
        ]
        cursor.executemany("INSERT INTO Modules (module_code, title, credits, max_slots, status) VALUES (?, ?, ?, ?, ?)", initial_modules)
        conn.commit()
    conn.close()

def execute_query(query, params=(), fetch_all=False):
    """Fungsi pembantu untuk menjalankan kueri."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(query, params)
    if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
        conn.commit()
        if query.strip().upper().startswith('INSERT'):
            return cursor.lastrowid
        return True
    
    result = cursor.fetchall()
    conn.close()
    return result if fetch_all else (result[0] if result else None)
    # main_sikampus.py
import streamlit as st
from db_sikampus import init_db
from public_project_view import show_public_registration
from academic_dashboard import show_academic_dashboard

# ======================================
# Inisialisasi Database
# ======================================
init_db()

# ======================================
# Konfigurasi Halaman
# ======================================
st.set_page_config(
    page_title="SIKAMPUS - Sistem Informasi Kapsul Mahasiswa",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================================
# CSS TEMA PUTIH & UNGU
# ======================================
st.markdown("""
<style>
/* ===============================
   TEMA PUTIH & UNGU (PURPLE)
   =============================== */

/* Background utama */
.stApp {
    background-color: #f7f5fb;
}

/* Sidebar */
.css-1d391kg, .e1fqkh3o7 {
    background: linear-gradient(180deg, #6a0dad, #4b0082);
    color: white;
}

/* Teks sidebar */
.css-1d391kg .stRadio label,
.css-1d391kg .stMarkdown,
.css-1d391kg span {
    color: white !important;
}

/* Judul */
h1, h2, h3, h4 {
    color: #6a0dad;
    font-weight: 700;
}

/* Card / Container */
.stCard,
div[data-testid="stContainer"] {
    background-color: white;
    border-radius: 14px;
    padding: 24px;
    box-shadow: 0 8px 20px rgba(106, 13, 173, 0.12);
    border: 1px solid #eee;
}

/* Button */
.stButton > button {
    background: linear-gradient(135deg, #6a0dad, #9b5de5);
    color: white !important;
    border-radius: 10px;
    border: none;
    padding: 10px 22px;
    font-weight: 600;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #5a0cae, #7b2cbf);
    transform: translateY(-2px);
    box-shadow: 0 6px 15px rgba(106, 13, 173, 0.3);
}

/* Input */
input, textarea, select {
    border-radius: 8px !important;
    border: 1px solid #d1c4e9 !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    background-color: white;
    border-radius: 12px;
    box-shadow: 0 6px 15px rgba(106, 13, 173, 0.1);
}

/* Metric */
[data-testid="stMetric"] {
    background: white;
    padding: 18px;
    border-radius: 12px;
    box-shadow: 0 6px 15px rgba(106, 13, 173, 0.15);
}
</style>
""", unsafe_allow_html=True)

# ======================================
# Navigasi Sidebar
# ======================================
st.sidebar.title("🎓 SIKAMPUS")
st.sidebar.markdown("### Sistem Informasi Proyek Mahasiswa")
st.sidebar.markdown("---")

# Simulasi Otentikasi Role
if 'user_role' not in st.session_state:
    st.session_state.user_role = 'Public'

role_choice = st.sidebar.radio(
    "Pilih Antarmuka:",
    [
        'Public (Registrasi Proyek)',
        'Academic Staff (Dasbor)'
    ],
    index=0 if st.session_state.user_role == 'Public' else 1
)

# ======================================
# Routing Halaman
# ======================================
if role_choice == 'Public (Registrasi Proyek)':
    st.session_state.user_role = 'Public'
    show_public_registration()

elif role_choice == 'Academic Staff (Dasbor)':
    st.session_state.user_role = 'Staff'
    show_academic_dashboard()
    # public_project_view.py
import streamlit as st
from db_sikampus import execute_query, DATABASE_NAME, PROJECT_COST_PER_CREDIT
import sqlite3
from datetime import datetime

def show_public_registration():
    """Menampilkan daftar modul proyek yang terbuka dan formulir registrasi."""
    st.title("📚 Registrasi Proyek Studi SIKAMPUS")
    st.markdown("Pilih modul proyek yang terbuka untuk studi lanjutan.")
    st.markdown("---")

    # Ambil data modul yang "Open" dan hitung slot terisi
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    query = """
    SELECT 
        M.id, M.module_code, M.title, M.credits, M.max_slots, M.status,
        COUNT(P.id) AS registered_count
    FROM Modules M
    LEFT JOIN ProjectRegistrations P ON M.id = P.module_id AND P.status = 'Registered'
    WHERE M.status = 'Open'
    GROUP BY M.id
    HAVING M.max_slots > COUNT(P.id)
    ORDER BY M.title
    """
    available_modules_data = cursor.execute(query).fetchall()
    conn.close()

    if not available_modules_data:
        st.info("Saat ini tidak ada Modul Proyek yang terbuka atau memiliki slot tersedia.")
        return

    # --- Tampilan Daftar Modul ---
    st.subheader("Modul Proyek Tersedia")
    
    # Menggunakan container untuk tampilan kartu yang lebih rapi
    cols = st.columns(3)
    
    if 'show_reg_form' not in st.session_state:
        st.session_state['show_reg_form'] = False

    for i, data in enumerate(available_modules_data):
        module_id, code, title, credits, max_slots, status, registered_count = data
        slots_available = max_slots - registered_count
        
        with cols[i % 3]:
            with st.container(border=True): # Menggunakan border container sebagai Card
                st.markdown(f"**{title} ({code})**", help=title)
                st.caption(f"Credits: {credits} SKS")
                st.markdown(f"Biaya Simulasi: **Rp {credits * PROJECT_COST_PER_CREDIT:,.0f}**")
                st.markdown(f"Slot Tersisa: **{slots_available}** dari {max_slots}")

                if st.button("Daftar Proyek", key=f"reg_{module_id}", use_container_width=True):
                    st.session_state['reg_module_id'] = module_id
                    st.session_state['reg_module_credits'] = credits
                    st.session_state['show_reg_form'] = True
                    st.experimental_rerun() 

    # --- Formulir Registrasi ---
    if st.session_state.get('show_reg_form', False) and st.session_state.get('reg_module_id'):
        module_id_to_reg = st.session_state['reg_module_id']
        module_credits_to_reg = st.session_state['reg_module_credits']
        
        # Ambil nama modul yang dipilih
        module_name = execute_query("SELECT title FROM Modules WHERE id = ?", (module_id_to_reg,))[0]

        st.markdown("---")
        st.subheader(f"📝 Formulir Registrasi: {module_name}")
        
        with st.form("project_registration_form"):
            st.markdown("**Data Akademisi**")
            scholar_id = st.text_input("ID Akademisi/NIM", max_chars=10, help="Gunakan ID unik")
            name = st.text_input("Nama Lengkap")
            email = st.text_input("Email Kontak")
            program = st.text_input("Program Studi")
            
            total_fee = module_credits_to_reg * PROJECT_COST_PER_CREDIT
            st.info(f"Total Biaya Proyek (Simulasi): **Rp {total_fee:,.0f}**")
            
            submitted = st.form_submit_button("Submit Registrasi Proyek")

            if submitted:
                if scholar_id and name and email and program:
                    
                    try:
                        # 1. Cek atau tambahkan Akademisi (Scholars)
                        scholar_data = execute_query("SELECT id FROM Scholars WHERE scholar_id = ?", (scholar_id,))
                        scholar_fk = None
                        if scholar_data:
                            scholar_fk = scholar_data[0]
                        else:
                            scholar_fk = execute_query("INSERT INTO Scholars (scholar_id, name, contact_email, program) VALUES (?, ?, ?, ?)", (scholar_id, name, email, program))

                        # 2. Cek apakah Akademisi sudah terdaftar di proyek ini
                        existing_reg = execute_query("SELECT id FROM ProjectRegistrations WHERE module_id = ? AND scholar_id_fk = ? AND status != 'Canceled'", (module_id_to_reg, scholar_fk))
                        if existing_reg:
                            st.warning("Anda sudah terdaftar di proyek ini.")
                            return
                            
                        # 3. Lakukan Registrasi Proyek
                        reg_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        execute_query(
                            "INSERT INTO ProjectRegistrations (module_id, scholar_id_fk, reg_date, total_fee, status, final_score) VALUES (?, ?, ?, ?, ?, ?)",
                            (module_id_to_reg, scholar_fk, reg_date, total_fee, 'Registered', None)
                        )
                        
                        st.success(f"✅ Registrasi Proyek berhasil! Status: **Registered**.")
                        
                        st.session_state['show_reg_form'] = False
                        st.experimental_rerun()
                        
                    except Exception as e:
                        st.error(f"Terjadi kesalahan saat menyimpan data: {e}")
                else:
                    st.warning("Semua kolom wajib diisi.")
                    # academic_dashboard.py
import streamlit as st
from db_sikampus import execute_query, DATABASE_NAME, PROJECT_COST_PER_CREDIT
import pandas as pd
import sqlite3
from datetime import datetime

def show_academic_dashboard():
    """Menampilkan navigasi dan konten dasbor Akademisi/Staf."""
    st.sidebar.markdown("---")
    dashboard_page = st.sidebar.radio(
        "Menu Akademik:", 
        ['Ringkasan Proyek', 'Kelola Modul Proyek', 'Daftar Registrasi']
    )

    if dashboard_page == 'Ringkasan Proyek':
        show_metrics_summary()
    elif dashboard_page == 'Kelola Modul Proyek':
        manage_modules()
    elif dashboard_page == 'Daftar Registrasi':
        manage_registrations()

# --- Fungsionalitas Metrik ---
def show_metrics_summary():
    st.title("📊 Ringkasan Proyek SIKAMPUS")
    
    # 1. Total Akademisi Terdaftar (Registered)
    total_registered = execute_query("SELECT COUNT(*) FROM ProjectRegistrations WHERE status = 'Registered'")
    total_registered_count = total_registered[0] if total_registered else 0

    # 2. Total Slot Proyek Tersedia
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    total_capacity_open_data = cursor.execute("SELECT SUM(max_slots) FROM Modules WHERE status = 'Open'").fetchone()
    total_capacity_open = total_capacity_open_data[0] if total_capacity_open_data and total_capacity_open_data[0] else 0
    
    total_occupied_data = cursor.execute("""
        SELECT COUNT(P.id) 
        FROM ProjectRegistrations P 
        JOIN Modules M ON P.module_id = M.id 
        WHERE P.status = 'Registered' AND M.status = 'Open'
    """).fetchone()
    total_occupied = total_occupied_data[0] if total_occupied_data and total_occupied_data[0] else 0
    conn.close()
    
    total_slots_available = total_capacity_open - total_occupied

    # 3. Proyeksi Fee Bulan Ini
    first_day_of_month = datetime.now().strftime('%Y-%m-01 00:00:00')
    monthly_fee_data = execute_query("SELECT SUM(total_fee) FROM ProjectRegistrations WHERE status = 'Registered' AND reg_date >= ?", (first_day_of_month,))
    monthly_fee_projection = monthly_fee_data[0] if monthly_fee_data and monthly_fee_data[0] else 0
    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Total Akademisi Registrasi Proyek", 
            value=f"{total_registered_count}",
        )
    with col2:
        st.metric(
            label="Total Slot Proyek Tersedia", 
            value=f"{total_slots_available}",
            delta=f"Kapasitas Modul Terbuka: {total_capacity_open}"
        )
    with col3:
        st.metric(
            label="Proyeksi Fee Bulan Ini (Simulasi)", 
            value=f"Rp {monthly_fee_projection:,.0f}",
        )
    
    st.markdown("---")


# --- Fungsionalitas Kelola Modul (CRUD) ---
def manage_modules():
    st.title("🧩 Kelola Modul Proyek")

    # --- CRUD: CREATE / UPDATE Form ---
    st.subheader("Tambah/Ubah Modul")
    
    module_id_to_edit = st.session_state.get('edit_module_id', None)
    initial_data = {}
    if module_id_to_edit:
        data = execute_query("SELECT module_code, title, credits, max_slots, status FROM Modules WHERE id = ?", (module_id_to_edit,))
        if data:
            initial_data = {'module_code': data[0], 'title': data[1], 'credits': data[2], 'max_slots': data[3], 'status': data[4]}
    
    with st.form("module_form", clear_on_submit=True):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            code = st.text_input("Kode Modul", value=initial_data.get('module_code', ''), max_chars=10)
            title = st.text_input("Judul Modul/Proyek", value=initial_data.get('title', ''))
        with col_c2:
            credits = st.number_input("Credits (SKS)", min_value=1, max_value=10, value=initial_data.get('credits', 3))
            max_slots = st.number_input("Slot Maksimal", min_value=5, max_value=100, value=initial_data.get('max_slots', 20))
            status = st.selectbox("Status", ['Open', 'Closed'], index=0 if initial_data.get('status', 'Open') == 'Open' else 1)
        
        submit_label = "Update Modul" if module_id_to_edit else "Tambah Modul Baru"
        submitted = st.form_submit_button(submit_label)
        
        if submitted:
            if code and title:
                try:
                    if module_id_to_edit:
                        # UPDATE
                        execute_query(
                            "UPDATE Modules SET module_code=?, title=?, credits=?, max_slots=?, status=? WHERE id=?",
                            (code, title, credits, max_slots, status, module_id_to_edit)
                        )
                        st.success(f"✅ Modul ID {module_id_to_edit} berhasil diupdate!")
                        del st.session_state['edit_module_id']
                    else:
                        # CREATE
                        execute_query(
                            "INSERT INTO Modules (module_code, title, credits, max_slots, status) VALUES (?, ?, ?, ?, ?)",
                            (code, title, credits, max_slots, status)
                        )
                        st.success(f"✅ Modul '{title}' berhasil ditambahkan!")
                    st.experimental_rerun()
                except sqlite3.IntegrityError:
                    st.error("Kode Modul sudah ada. Gunakan kode unik.")
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")
            else:
                st.warning("Kode dan Judul Modul wajib diisi.")

    st.markdown("---")

    # --- CRUD: READ (Tabel Data) ---
    st.subheader("Daftar Semua Modul Proyek")
    
    modules_data = execute_query("SELECT id, module_code, title, credits, max_slots, status FROM Modules", fetch_all=True)
    if modules_data:
        df_modules = pd.DataFrame(modules_data, columns=['ID', 'Kode', 'Judul', 'Credits', 'Slot Max', 'Status'])
        st.dataframe(df_modules, use_container_width=True)
        
        # --- CRUD: DELETE / EDIT (Aksi) ---
        col_actions = st.columns([1, 1, 3])
        module_id_to_act = col_actions[0].number_input("ID Modul untuk Aksi:", min_value=1, value=1)
        
        if col_actions[1].button("Edit Data", key="edit_mod_btn"):
            st.session_state['edit_module_id'] = int(module_id_to_act)
            st.experimental_rerun()
            
        if col_actions[2].button("Hapus Permanen", key="del_mod_btn", help="Hapus Modul dan semua registrasi terkait"):
            try:
                execute_query("DELETE FROM ProjectRegistrations WHERE module_id = ?", (module_id_to_act,))
                execute_query("DELETE FROM Modules WHERE id = ?", (module_id_to_act,))
                st.success(f"🗑️ Modul ID {module_id_to_act} dan registrasi terkait berhasil dihapus.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Gagal menghapus: {e}")
    else:
        st.info("Tidak ada data Modul Proyek.")

# --- Fungsionalitas Daftar Registrasi ---
def manage_registrations():
    st.title("📋 Daftar Registrasi Proyek")

    # --- READ (Tabel Registrasi Lengkap) ---
    query = """
    SELECT 
        P.id, S.scholar_id, S.name AS scholar_name, M.module_code, M.title AS module_title, 
        P.reg_date, P.total_fee, P.status, P.final_score, P.module_id
    FROM ProjectRegistrations P
    JOIN Scholars S ON P.scholar_id_fk = S.id
    JOIN Modules M ON P.module_id = M.id
    ORDER BY P.reg_date DESC
    """
    registrations_data = execute_query(query, fetch_all=True)
    
    if registrations_data:
        df_registrations = pd.DataFrame(registrations_data, columns=[
            'ID Reg', 'ID Akademisi', 'Nama Akademisi', 'Kode Modul', 'Judul Modul', 
            'Tgl Registrasi', 'Total Fee', 'Status', 'Nilai Akhir', 'Module ID (Internal)'
        ])
        
        st.dataframe(df_registrations.drop(columns=['Module ID (Internal)']), use_container_width=True)
        
        st.markdown("---")
        st.subheader("Ubah Status & Berikan Nilai/Score")
        
        # --- UPDATE (Ubah Status dan Nilai) ---
        with st.form("update_registration_form"):
            col_u1, col_u2, col_u3 = st.columns(3)
            
            reg_id = col_u1.number_input("ID Registrasi yang akan diubah:", min_value=1, value=1)
            new_status = col_u2.selectbox("Status Baru:", ['Registered', 'InProgress', 'Completed', 'Canceled'])
            final_score = col_u3.selectbox("Nilai Akhir (Isi jika status Completed):", ['A', 'B', 'C', 'D', 'E', 'N/A'])
            
            updated_score = final_score if final_score != 'N/A' and new_status == 'Completed' else None
            
            submitted = st.form_submit_button("Update Registrasi")
            
            if submitted:
                if new_status == 'Completed' and updated_score is None:
                    st.warning("Status 'Completed' memerlukan Nilai Akhir.")
                else:
                    try:
                        execute_query(
                            "UPDATE ProjectRegistrations SET status = ?, final_score = ? WHERE id = ?",
                            (new_status, updated_score, reg_id)
                        )
                        st.success(f"✅ Registrasi ID {reg_id} berhasil diupdate ke Status: **{new_status}** dan Nilai: **{updated_score if updated_score else '-'}**.")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Gagal mengupdate registrasi: {e}")
    else:
        st.info("Tidak ada data Registrasi Proyek.")