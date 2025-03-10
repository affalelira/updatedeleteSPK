import streamlit as st
import requests
import pandas as pd
from datetime import datetime, time, timedelta, date
import locale
import threading
import time as tm 

# URL dari Google Apps Script Web App
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbywSRCwDhF6BoV7-za6sRy3zq_WI5vNYJqo4t4wGyxgkEW8_B5vHDnQ3Nw3tVhjteYm/exec"

# Atur locale ke bahasa Indonesia
try:
    locale.setlocale(locale.LC_TIME, 'id_ID.UTF-8')
except locale.Error:
    print("Locale 'id_ID.UTF-8' tidak tersedia, menggunakan locale default.")

# Function to get all data from Google Sheets
def get_all_data():
    try:
        response = requests.get(APPS_SCRIPT_URL, params={"action": "get_data"}, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Terjadi kesalahan saat mengambil data: {e}")
        return []

# Function to get options
def get_options():
    try:
        response = requests.get(APPS_SCRIPT_URL, params={"action": "get_options"}, timeout=10)
        response.raise_for_status()
        options = response.json()
        for key in options:
            options[key].insert(0, "")  # Add empty option as default
        return options
    except requests.exceptions.RequestException as e:
        st.error(f"Terjadi kesalahan saat mengambil opsi: {e}")
        return {}

# Function to add data to Google Sheets
def add_data(form_data):
    try:
        form_data["action"] = "add_data"
        response = requests.post(APPS_SCRIPT_URL, json=form_data, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": str(e)}

# Function to update data
def update_data(updated_row):
    try:
        updated_row["Tanggal"] = updated_row["Tanggal"].strftime("%Y-%m-%d")
        updated_row["Jam Start"] = updated_row["Jam Start"].strftime("%H:%M")
        updated_row["Jam Stop"] = updated_row["Jam Stop"].strftime("%H:%M")

        payload = {
            "action": "update_data",
            "updated_row": updated_row,
        }
        response = requests.post(APPS_SCRIPT_URL, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Terjadi kesalahan: {e}")
        return {"status": "error", "error": str(e)}

# Function to delete data
def delete_data(unique_key):
    try:
        response = requests.post(APPS_SCRIPT_URL, json={"action": "delete_data", "unique_key": unique_key}, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": str(e)}

def parse_time(time_str):
    """Convert a time string into a datetime.time object."""
    if isinstance(time_str, str):
        try:
            return datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            return time(0, 0)
    elif isinstance(time_str, time):
        return time_str
    else:
        return time(0, 0)

# Fungsi Ping Otomatis (Keep Alive)
def keep_alive():
    while True:
        try:
            response = requests.get(APPS_SCRIPT_URL, timeout=10)
            print(f"Keep Alive Status: {response.status_code}")
        except Exception as e:
            print(f"Keep Alive Error: {e}")
        tm.sleep(600)  # Ping setiap 10 menit

# Menjalankan fungsi keep_alive di thread terpisah agar tidak mengganggu UI
thread = threading.Thread(target=keep_alive, daemon=True)
thread.start()

# Get options for select box
options = get_options()

# Get data from Google Sheets
all_data = get_all_data()

st.title("📄 Surat Perintah Kerja")

if isinstance(all_data, list) and all_data:
    df = pd.DataFrame(all_data, columns=[
       "Nomor SPK", "Tanggal", "Jenis Produk", "Line", "Jam Start", "Jam Stop", "Total hour",
       "Speed (kg/jam)", "Rencana Total Output (kg)", "Rencana Total Output (Batch)", "Inner (roll)"])

    st.subheader("📊 Data Keseluruhan")

    # Display each row with expander
    for index, row in df.iterrows():
        unique_key = row["Nomor SPK"]
        with st.expander(f"📄 {unique_key}"):
            st.write(f"📅 **Tanggal:** {row['Tanggal']}")
            st.write(f"🏷️ **Jenis Produk:** {row['Jenis Produk']}")
            st.write(f"🏭 **Line:** {row['Line']}")
            st.write(f"⏰ **Jam Start:** {row['Jam Start']}")
            st.write(f"⏳ **Jam Stop :** {row['Jam Stop']}")
            st.write(f"⏱️ **Total hour:** {row['Total hour']}")
            st.write(f"🚀 **Speed (kg/jam):** {row['Speed (kg/jam)']}")
            st.write(f"📦 **Rencana Total Output (kg):** {row['Rencana Total Output (kg)']}")
            st.write(f"📦 **Rencana Total Output (Batch):** {row['Rencana Total Output (Batch)']}")
            st.write(f"📦 **Inner (roll):** {row['Inner (roll)']}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"🗑️ Hapus {unique_key}", key=f"delete_{unique_key}"):
                    st.session_state.confirm_delete = unique_key  # Set unique_key for confirmation

            with col2:
                if st.button(f"✏️ Edit {unique_key}", key=f"edit_{unique_key}"):
                    st.session_state["edit_data"] = row
                    st.session_state["editing"] = True

# Konfirmasi penghapusan
if "confirm_delete" in st.session_state and st.session_state.confirm_delete:
    unique_key = st.session_state.confirm_delete
    st.error("Apakah Anda yakin ingin menghapus data ini?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Ya, Hapus"):
            delete_data(unique_key)
            st.success(f"Data {unique_key} berhasil dihapus.")
            st.session_state.confirm_delete = None  # Reset konfirmasi
            tm.sleep(2)
            st.rerun()  # Refresh UI setelah penghapusan
    with col2:
        if st.button("Batal"):
            st.session_state.confirm_delete = None  # Reset konfirmasi
            st.toast("Penghapusan dibatalkan.",icon="↩️")
            tm.sleep(2)
            st.rerun()

# If the user clicks "Edit", display the form for updating
if st.session_state.get("editing", False):
    st.subheader("✏️ Edit Data")
    row = st.session_state["edit_data"]

    # Convert "Tanggal" to a datetime.date object
    if isinstance(row["Tanggal"], str):
        try:
            tanggal_date = datetime.strptime(row["Tanggal"], "%A, %d %B %Y").date()
        except ValueError:
            tanggal_date = datetime.now().date()  # Fallback to today's date
    else:
        tanggal_date = row["Tanggal"]

    # Ensure initial values match available options
    list_produk = [item[0] if isinstance(item, list) and item else item for item in options.get("List Produk", [""])]
    list_line = [item[0] if isinstance(item, list) and item else item for item in options.get("List Line", [""])]
    default_speed = row["Speed (kg/jam)"] if row["Speed (kg/jam)"] else "280,67"

    # Input fields organized in columns
    col1, col2 = st.columns(2)
    with col1:
        updated_row = {
            "Nomor SPK": st.text_input("🔢 Nomor SPK", value=row["Nomor SPK"]),
            "Tanggal": st.date_input("📅 Tanggal", value=tanggal_date),  # Use the converted date
            "Jenis Produk": st.selectbox("🏷️ Jenis Produk", list_produk),
        }
        # Validation for "Jenis Produk"
        if not updated_row["Jenis Produk"]:
            st.error("⚠ Jenis Produk belum dipilih.")

    with col2:
        updated_row["Line"] = st.selectbox("🏭 Line", list_line)
        # Validation for "Line"
        if not updated_row["Line"]:
            st.error("⚠ Line belum dipilih.")

        start_time = st.time_input("⏰ Waktu Mulai", value=parse_time(row["Jam Start"]))
        stop_time = st.time_input("⏳ Waktu Selesai", value=parse_time(row["Jam Stop"]))

    # Calculate total hours
    start_datetime = datetime.combine(date.today(), start_time)
    stop_datetime = datetime.combine(date.today(), stop_time)

    if stop_datetime < start_datetime:
        stop_datetime += timedelta(days=1)
    total_hour = stop_datetime - start_datetime
    total_hour_time = (datetime(1900, 1, 1) + total_hour).time()
    st.write(f"⏱️ **Total Hour:** {total_hour_time.strftime('%H:%M')} jam")

    # Speed selection
    list_speed = [280.67, 780.00]
    speed_index = list_speed.index(st.session_state.form_speed) if "form_speed" in st.session_state and st.session_state.form_speed in list_speed else 0
    updated_row["Speed (kg/jam)"] = st.selectbox("🚀 Speed (kg/jam)", list_speed, index=speed_index, key="form_speed")

    # Batch selection
    list_batch = [1000.00, 130.00]
    batch_index = list_batch.index(st.session_state.form_batch) if "form_batch" in st.session_state and st.session_state.form_batch in list_batch else 0
    updated_row["Batch"] = st.selectbox("📦 Pilih Banyak Kg/Batch", list_batch, index=batch_index, key="form_batch")

    # Roll selection
    list_roll = [75.9, 75.0]
    roll_index = list_roll.index(st.session_state.form_roll) if "form_roll" in st.session_state and st.session_state.form_roll in list_roll else 0
    updated_row["Roll"] = st.selectbox("📦 Pilih Banyak Kg/Roll", list_roll, index=roll_index, key="form_roll")

    # Calculate outputs
    total_hour_float = total_hour.total_seconds() / 3600  # Convert total_hour to float (hours)
    OutputKG = total_hour_float * updated_row["Speed (kg/jam)"]
    OutputBatch = round(OutputKG / updated_row["Batch"], 1)
    InnerRoll = round(OutputKG / updated_row["Roll"], 0)

    # Display results in a single line using columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📦 Rencana Total Output (kg)", f"{OutputKG:.2f} kg")
    with col2:
        st.metric("📦 Rencana Total Output (Batch)", f"{OutputBatch:.1f} batch")
    with col3:
        st.metric("📦 Inner (roll)", f"{InnerRoll:.0f}")

    # Add the time inputs and calculations to the updated_row dictionary
    updated_row.update({
        "Jam Start": start_time,
        "Jam Stop": stop_time,
        "Total hour": total_hour_time.strftime("%H:%M"),
        "Rencana Total Output (kg)": OutputKG,
        "Rencana Total Output (Batch)": OutputBatch,
        "Inner (roll)": InnerRoll
    })

    # Checkbox untuk konfirmasi update
    confirm_update = st.checkbox("Saya yakin ingin memperbarui data.")

    # Tombol update hanya aktif jika checkbox dicentang
    if st.button("💾 Simpan Perubahan", disabled=not confirm_update):
        result = update_data(updated_row)
        if result.get("status") == "success":
            st.toast("Data berhasil diperbarui!", icon="✅")
            tm.sleep(2)
            st.session_state["editing"] = False
            st.rerun()
        else:
            st.error("Gagal memperbarui data. Silakan coba lagi.")

