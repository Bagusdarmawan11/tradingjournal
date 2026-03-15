import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ==========================================
# 0. SETUP DASHBOARD STREAMLIT
# ==========================================
st.set_page_config(page_title="Sparbot Omni-Dashboard", layout="wide", page_icon="📈")

COLOR_PROFIT = '#1F77B4' 
COLOR_LOSS = '#FF7F0E'   
COLOR_NEUTRAL = '#7F7F7F'
sns.set_theme(style="whitegrid")

st.title("📈 Dashboard Analitik Sparbot V11.4.2 (Ultimate AI)")
st.markdown("Upload dataset jurnal terbarumu. Sistem akan otomatis menganalisis dan memberikan **Deep Insight & Rekomendasi Makro**.")

# ==========================================
# 1. FILE UPLOADER & DATA CLEANING
# ==========================================
uploaded_file = st.file_uploader("📂 Upload Jurnal Trading CSV", type=['csv'])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df = df.dropna(subset=['Waktu Buka', 'Koin']).copy()

    def clean_money(x):
        if isinstance(x, str): return float(x.replace('$', '').replace(',', '').strip())
        return x
    def clean_pct(x):
        if isinstance(x, str): return float(x.replace('%', '').strip())
        return x

    df['Net PnL'] = df['Net PnL'].apply(clean_money)
    df['ROI (%)'] = df['ROI (%)'].apply(clean_pct)
    df['Skor SMC'] = df['Skor SMC'].apply(clean_pct)

    df['Waktu Buka'] = pd.to_datetime(df['Waktu Buka'])
    df['Waktu Tutup'] = pd.to_datetime(df['Waktu Tutup'])
    df['Durasi (Menit)'] = (df['Waktu Tutup'] - df['Waktu Buka']).dt.total_seconds() / 60.0
    df['Jam Buka'] = df['Waktu Buka'].dt.hour
    df = df.sort_values('Waktu Buka').reset_index(drop=True)

    df['Is Loss'] = df['Status Exit'].str.contains('STOP LOSS', na=False)
    df['Is Profit'] = df['Status Exit'].str.contains('SMART LOCK|TAKE PROFIT', na=False)
    df['Status Sederhana'] = np.where(df['Is Profit'], 'Profit', np.where(df['Is Loss'], 'Loss', 'Lainnya'))

    df['Cumulative PnL'] = df['Net PnL'].cumsum()
    df['Peak'] = df['Cumulative PnL'].cummax()
    df['Drawdown'] = df['Cumulative PnL'] - df['Peak']
    max_drawdown = df['Drawdown'].min()

    st.success("✅ Dataset berhasil dianalisis! Gulir ke bawah untuk membaca Insight Mendalam.")
    st.markdown("---")

    # ==========================================
    # 2. METRIK UTAMA 
    # ==========================================
    avg_dur_win = df[df['Is Profit']]['Durasi (Menit)'].mean()
    avg_dur_loss = df[df['Is Loss']]['Durasi (Menit)'].mean()
    avg_roi_win = df[df['Is Profit']]['ROI (%)'].mean()
    avg_roi_loss = df[df['Is Loss']]['ROI (%)'].mean()
    
    st.subheader("📊 Laporan Kesehatan Bot")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🚨 Max Drawdown", f"${max_drawdown:.2f}")
    col2.metric("⏱️ Avg Durasi Profit", f"{avg_dur_win:.1f} Menit")
    col3.metric("⏱️ Avg Durasi Loss", f"{avg_dur_loss:.1f} Menit")
    col4.metric("💰 Avg ROI Win", f"+{avg_roi_win:.2f}%")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("🩸 Avg ROI Loss", f"{avg_roi_loss:.2f}%")
    col6.metric("🧠 Rata-rata Skor SMC", f"{df['Skor SMC'].mean():.1f}%")
    most_traded = df['Koin'].value_counts().head(1) if not df.empty else (["N/A"], [0])
    col7.metric("🎯 Koin Tering", f"{most_traded.index[0]}")
    col8.metric("🔄 Total Transaksi", f"{len(df)} Trade")
    st.markdown("---")

    # ==========================================
    # 3. VISUALISASI & DEEP INSIGHT AUTO-READ
    # ==========================================
    
    # --- VISUAL 1: Kurva Profit & Insight Riwayat ---
    st.subheader("1. Kurva Profit vs Drawdown")
    fig1, ax1 = plt.subplots(figsize=(12, 4))
    ax1.plot(df['Waktu Buka'], df['Cumulative PnL'], marker='o', color=COLOR_PROFIT, linewidth=2, label='Profit Nyata')
    ax1.plot(df['Waktu Buka'], df['Peak'], linestyle='--', color='black', alpha=0.5, label='Puncak Saldo')
    ax1.fill_between(df['Waktu Buka'], df['Cumulative PnL'], df['Peak'], color=COLOR_LOSS, alpha=0.3, label='Area Drawdown')
    ax1.set_ylabel('Net PnL ($)')
    ax1.legend()
    st.pyplot(fig1)

    # Insight Kurva (Mendeteksi Tanggal Terburuk & Terbaik)
    idx_min_dd = df['Drawdown'].idxmin()
    date_min_dd = df.loc[idx_min_dd, 'Waktu Buka'].strftime('%d %b %H:%M')
    
    df_before_dd = df.loc[:idx_min_dd]
    if not df_before_dd.empty:
        idx_peak_before = df_before_dd['Cumulative PnL'].idxmax()
        date_peak_before = df.loc[idx_peak_before, 'Waktu Buka'].strftime('%d %b %H:%M')
    else:
        date_peak_before = "Awal Trading"
        
    idx_max_profit = df['Net PnL'].idxmax()
    date_max_profit = df.loc[idx_max_profit, 'Waktu Buka'].strftime('%d %b %H:%M')
    koin_max_profit = df.loc[idx_max_profit, 'Koin']

    st.info(f"📆 **Detail Perjalanan Historis:** Badai penurunan paling parah (Max Drawdown) terjadi dalam rentang waktu **{date_peak_before} hingga {date_min_dd}**. Sebaliknya, lonjakan profit terbesar dalam satu transaksi dicetak pada **{date_max_profit}** melalui koin **{koin_max_profit}**. Jika kurva saat ini sedang turun, pertahankan *mindset* objektif, karena bot terbukti mampu melakukan *recovery* dari fase {date_min_dd}.")

    # --- VISUAL 2 & 3: Distribusi Jam & Tren Makro Arah ---
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.subheader("2. Peta Zona Waktu (WIB)")
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        sns.countplot(data=df, x='Jam Buka', hue='Status Sederhana', palette={'Profit':COLOR_PROFIT, 'Loss':COLOR_LOSS, 'Lainnya':COLOR_NEUTRAL}, ax=ax2)
        ax2.set_xlabel('Jam (WIB)')
        ax2.set_ylabel('Jumlah Transaksi')
        st.pyplot(fig2)
        
        # Analisis Cerdas Jam Terbaik & Terburuk
        jam_stats = df.groupby('Jam Buka').agg(Total=('Jam Buka', 'count'), Win=('Is Profit', 'sum'), Loss=('Is Loss', 'sum'))
        jam_stats['WinRate'] = jam_stats['Win'] / jam_stats['Total']
        
        jam_terburuk = jam_stats['Loss'].idxmax() if not jam_stats.empty else "N/A"
        jam_terbaik = jam_stats[jam_stats['Total'] >= 2]['WinRate'].idxmax() if len(jam_stats[jam_stats['Total'] >= 2]) > 0 else "N/A"

        st.error(f"🛑 **SOP Jadwal Bot:** Jam paling berdarah dengan *Stop Loss* terbanyak adalah pukul **{jam_terburuk}:00 WIB**. Pastikan bot berstatus **OFF** pada jam tersebut. Anda disarankan untuk melakukan **BOT ON** kembali pada pukul **{jam_terbaik}:00 WIB**, karena secara historis ini adalah zona waktu paling stabil dengan Win Rate tertinggi.")

    with col_v2:
        st.subheader("3. Performa Arah & Kondisi Makro")
        arah_stats = df.groupby('Arah').agg(Total=('Arah', 'count'), Profit=('Is Profit', 'sum'))
        arah_stats['Win_Rate'] = (arah_stats['Profit'] / arah_stats['Total']) * 100
        fig3, ax3 = plt.subplots(figsize=(8, 4))
        sns.barplot(x=arah_stats.index, y='Win_Rate', data=arah_stats, palette=[COLOR_PROFIT, COLOR_LOSS], ax=ax3)
        ax3.axhline(50, color='black', linestyle='--')
        ax3.set_ylabel('Win Rate (%)')
        st.pyplot(fig3)
        
        # Analisis Makro Bearish/Bullish
        if len(arah_stats) == 2:
            wr_long = arah_stats.loc['LONG', 'Win_Rate'] if 'LONG' in arah_stats.index else 0
            wr_short = arah_stats.loc['SHORT', 'Win_Rate'] if 'SHORT' in arah_stats.index else 0
            
            if wr_short > wr_long + 10:
                tren = "DOWNTREND / BEARISH"
                alasan = "Peluang posisi SHORT lebih sering mencapai target (hit). Disarankan mengurangi margin pada sinyal LONG karena rawan tertelan tren."
            elif wr_long > wr_short + 10:
                tren = "UPTREND / BULLISH"
                alasan = "Peluang posisi LONG sangat dominan. Pasar merespon positif kenaikan harga. Tetap berhati-hati mengambil sinyal SHORT."
            else:
                tren = "SIDEWAYS / KONSOLIDASI"
                alasan = "Performa LONG dan SHORT cukup seimbang. Bot dapat menangkap peluang dari dua arah dengan aman karena pasar berayun di rentang harga tertentu."
                
            st.success(f"🧭 **Insight Makro Pasar:** Berdasarkan disparitas Win Rate, market saat ini cenderung berada di fase **{tren}**. {alasan}")

    # --- VISUAL 4: Koin Pahlawan vs Beban ---
    st.subheader("4. Top Koin Pahlawan vs Koin Beban (Manajemen Blacklist)")
    coin_pnl = df.groupby('Koin')['Net PnL'].sum().sort_values(ascending=False)
    fig4, axes = plt.subplots(1, 2, figsize=(14, 4))
    sns.barplot(x=coin_pnl.head(5).values, y=coin_pnl.head(5).index, ax=axes[0], color=COLOR_PROFIT)
    axes[0].set_title('Top 5 Paling Cuan')
    sns.barplot(x=coin_pnl.tail(5).values, y=coin_pnl.tail(5).index, ax=axes[1], color=COLOR_LOSS)
    axes[1].set_title('Top 5 Koin Beban (Blacklist)')
    st.pyplot(fig4)
    
    koin_beban = list(coin_pnl.tail(3).index)
    st.warning(f"⚠️ **SOP Blacklist:** Segera masukkan **{', '.join(koin_beban)}** ke VPS Anda. **PENTING:** Koin di dunia kripto memiliki siklus rotasi likuiditas. Blacklist koin-koin ini selama **7 hingga 14 hari ke depan saja**. Setelah 2 minggu berlalu, lepaskan mereka dari blacklist secara bertahap untuk menguji apakah algoritma *market maker* (bandar) pada koin tersebut sudah normal kembali.")

    # --- VISUAL 5: Jebakan SMC ---
    st.subheader("5. Deteksi Jebakan Sinyal SMC")
    fig5, ax5 = plt.subplots(figsize=(12, 4))
    sns.scatterplot(data=df, x='Jam Buka', y='Skor SMC', hue='Status Sederhana', style='Status Sederhana', palette={'Profit':COLOR_PROFIT, 'Loss':COLOR_LOSS, 'Lainnya':COLOR_NEUTRAL}, s=100, alpha=0.8, ax=ax5)
    ax5.axhline(85, color='black', linestyle='--', alpha=0.5, label='Batas SMC (85%)')
    ax5.set_xticks(range(0, 24))
    ax5.set_xlabel('Jam Buka Posisi (WIB)')
    ax5.set_ylabel('Skor SMC (%)')
    ax5.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    st.pyplot(fig5)
    
    st.info("🔎 **Analisis Fakeout:** Fokus pada titik-titik oranye yang berada di atas garis putus-putus. Jika bot memunculkan sinyal dengan SMC 95% namun berada di zona jam terburuk (seperti analisis nomor 2), itu adalah *Fake Breakout* (Sinyal Palsu) akibat volatilitas. Abaikan sinyal tersebut.")

    # --- VISUAL 6: Pola AI Terbaik ---
    st.subheader("6. Pola AI Terbaik (Setup Taktis)")
    pola_stats = df.groupby('Pola & AI').agg(Total_Entry=('Koin', 'count'), Win_Rate=('Is Profit', lambda x: (x.sum() / len(x)) * 100)).sort_values(by='Win_Rate', ascending=True)
    pola_stats_valid = pola_stats[pola_stats['Total_Entry'] >= 2]

    if not pola_stats_valid.empty:
        fig6, ax6 = plt.subplots(figsize=(12, 4))
        sns.barplot(x='Win_Rate', y=pola_stats_valid.index, data=pola_stats_valid, color=COLOR_PROFIT, ax=ax6)
        ax6.axvline(50, color='black', linestyle='--')
        ax6.set_xlabel('Win Rate (%)')
        st.pyplot(fig6)
        
        pola_terbaik = pola_stats_valid.index[-1]
        st.success(f"💎 **Blueprint Kemenangan:** Pola **'{pola_terbaik}'** adalah setup algoritma terkuat Anda saat ini. Selama kondisi makro pasar tidak berubah drastis, pertahankan prioritas eksekusi pada pola ini.")
    else:
        st.info("💡 Sistem membutuhkan minimal 2 kali percobaan per pola AI untuk memunculkan peringkat akurat.")

else:
    st.info("💡 Menunggu dataset... Silakan upload file 'Trading Journal Sparbot - Trading Journaling.csv' di atas untuk memulai Analisis Makro Otomatis.")
