# Brand Guidelines — **CullaGrace**

## 1. Tujuan Dokumen

Dokumen ini adalah panduan merek dan visual untuk aplikasi **CullaGrace**, yaitu aplikasi desktop/web lokal untuk membantu tim multimedia gereja melakukan **photo culling otomatis** berdasarkan **blur detection**, **exposure detection**, **duplicate detection**, dan **face detection**.

Panduan ini harus digunakan oleh agen AI pembuat kode otonom sebagai acuan utama saat membangun antarmuka aplikasi agar hasil front-end konsisten, jelas, ringan, profesional, dan sesuai dengan konteks pelayanan gereja.

---

# 2. Nama Merek (Brand Name)

## 2.1 Nama Utama

Nama merek aplikasi adalah **CullaGrace**.

Makna nama:

- **Culla** berasal dari kata *culling*, yaitu proses menyortir dan memilih foto terbaik.
- **Grace** melambangkan konteks pelayanan gereja, kasih karunia, dan suasana pelayanan yang hangat.
- Nama ini harus terasa **modern**, **ramah**, **profesional**, dan tetap sesuai dengan lingkungan gereja.

## 2.2 Alternatif Nama Jika Diperlukan

Jika agen perlu menggunakan nama alternatif dalam mockup atau placeholder, gunakan salah satu dari berikut:

1. **GraceCuller**
2. **ChurchCull AI**
3. **FotoBerkat AI**
4. **GraceFrame**

Namun, nama default yang harus dipakai di seluruh aplikasi adalah **CullaGrace**.

## 2.3 Tagline

Gunakan tagline utama:

> **Sortir foto pelayanan lebih cepat, rapi, dan bermakna.**

Alternatif tagline:

> **Dari ribuan foto menjadi pilihan terbaik dalam hitungan menit.**

---

# 3. Identitas Visual Utama

## 3.1 Kepribadian Visual

Aplikasi harus memiliki karakter visual berikut:

- **Tenang** — tidak menggunakan warna yang terlalu mencolok.
- **Bersih** — banyak ruang kosong, tata letak rapi, tidak padat.
- **Profesional** — cocok digunakan sebagai alat kerja multimedia.
- **Ramah** — tidak terasa teknis berlebihan walaupun menggunakan AI.
- **Modern** — menggunakan card layout, rounded corner, progress indicator, dan visual hierarchy yang jelas.
- **Pelayanan gereja** — visual harus terasa hangat, sopan, dan tidak agresif.

## 3.2 Prinsip Desain

Agen AI harus mengikuti prinsip berikut:

1. **Utamakan kejelasan daripada dekorasi.**
2. **Gunakan layout yang memandu pengguna langkah demi langkah.**
3. **Jangan membuat UI terlihat seperti software teknis yang rumit.**
4. **Pastikan pengguna pemula dapat memahami aplikasi tanpa membaca dokumentasi panjang.**
5. **Gunakan warna status secara konsisten: hijau untuk lolos, kuning untuk review, merah untuk ditolak.**
6. **Semua aksi utama harus terlihat jelas dan mudah diakses.**

---

# 4. Penggunaan Logo (Logo Usage)

## 4.1 Konsep Logo

Logo **CullaGrace** harus merepresentasikan gabungan antara:

- **Foto / frame kamera**
- **Proses seleksi / checkmark**
- **Nuansa pelayanan / grace / light**

Konsep visual yang disarankan:

- Ikon berbentuk **frame foto** dengan simbol **checkmark** di dalamnya.
- Tambahan aksen kecil berupa **sinar cahaya lembut** atau **spark** untuk melambangkan momen terbaik.
- Hindari simbol keagamaan yang terlalu eksplisit jika tidak diminta, agar aplikasi tetap netral dan profesional.

## 4.2 Bentuk Logo

Logo harus tersedia dalam dua varian:

### 4.2.1 Logo Horizontal

Format:

```text
[Icon] CullaGrace
```

Gunakan logo horizontal pada:

- Header aplikasi
- Sidebar atas
- Splash screen
- Halaman awal / onboarding

### 4.2.2 Logo Ikon Saja

Gunakan logo ikon saja pada:

- App icon
- Sidebar collapsed
- Loading screen kecil
- Favicon jika aplikasi berbasis web

## 4.3 Penempatan Logo

Aturan penempatan:

- Logo harus ditempatkan di **kiri atas** pada layout desktop.
- Logo harus memiliki ruang kosong minimal **16px** dari elemen lain.
- Pada header, tinggi logo maksimal **32px**.
- Pada halaman onboarding atau landing internal, logo boleh lebih besar dengan tinggi maksimal **64px**.

## 4.4 Larangan Penggunaan Logo

Jangan lakukan hal berikut:

- Jangan meregangkan logo secara horizontal atau vertikal.
- Jangan memberi efek shadow berlebihan pada logo.
- Jangan meletakkan logo di atas background yang ramai.
- Jangan mengubah warna logo di luar palet warna resmi.
- Jangan menggunakan logo sebagai watermark besar di area kerja utama.

---

# 5. Palet Warna (Colors)

## 5.1 Warna Primer

Gunakan warna primer berikut sebagai warna identitas utama aplikasi:

- **Primary Blue — #2563EB**

Fungsi:

- Tombol aksi utama
- Link aktif
- Indikator proses utama
- Highlight navigasi aktif
- Elemen penting seperti tombol **Start Culling**

Makna:

- Profesional
- Terpercaya
- Teknologis
- Stabil

## 5.2 Warna Sekunder

Gunakan warna sekunder sebagai aksen hangat:

- **Grace Gold — #F59E0B**

Fungsi:

- Aksen kecil
- Ikon highlight
- Status **Review**
- Elemen yang membutuhkan perhatian tanpa terasa berbahaya

Makna:

- Hangat
- Pelayanan
- Momen berharga
- Cahaya

## 5.3 Warna Pendukung

Gunakan warna berikut untuk status hasil culling:

### Selected / Lolos

- **Success Green — #16A34A**

Gunakan untuk:

- Status **Selected**
- Foto yang lolos otomatis
- Badge keberhasilan
- Progress selesai

### Review / Perlu Dicek

- **Warning Amber — #F59E0B**

Gunakan untuk:

- Status **Review**
- Foto yang butuh keputusan manual
- Peringatan ringan

### Rejected / Ditolak

- **Danger Red — #DC2626**

Gunakan untuk:

- Status **Rejected**
- Foto blur parah
- Exposure buruk
- Error serius

### Informasi

- **Info Cyan — #0891B2**

Gunakan untuk:

- Informasi sistem
- Tips penggunaan
- Deteksi AI yang masih berjalan

## 5.4 Warna Netral

Gunakan warna netral berikut untuk struktur UI:

- **Background Light — #F8FAFC**
- **Surface / Card — #FFFFFF**
- **Border Soft — #E2E8F0**
- **Text Primary — #0F172A**
- **Text Secondary — #475569**
- **Text Muted — #94A3B8**
- **Disabled Background — #E5E7EB**

## 5.5 Dark Mode Opsional

Jika aplikasi menyediakan dark mode, gunakan warna berikut:

- **Dark Background — #0F172A**
- **Dark Surface — #1E293B**
- **Dark Border — #334155**
- **Dark Text Primary — #F8FAFC**
- **Dark Text Secondary — #CBD5E1**
- **Dark Text Muted — #64748B**

Dark mode bersifat opsional untuk versi 1. Jangan prioritaskan dark mode jika fitur inti belum selesai.

## 5.6 Aturan Penggunaan Warna

Agen AI harus mengikuti aturan ini:

1. Gunakan **#2563EB** hanya untuk aksi utama dan elemen aktif.
2. Gunakan **#F59E0B** untuk status review atau aksen hangat.
3. Gunakan **#16A34A**, **#F59E0B**, dan **#DC2626** secara konsisten untuk status culling.
4. Jangan menggunakan terlalu banyak warna baru di luar palet ini.
5. Background utama harus tetap terang dan bersih menggunakan **#F8FAFC**.
6. Card utama harus menggunakan **#FFFFFF** dengan border halus **#E2E8F0**.

---

# 6. Tipografi (Typography)

## 6.1 Font Utama

Gunakan font utama:

- **Inter**

Alasan:

- Modern
- Mudah dibaca
- Cocok untuk aplikasi produktivitas
- Mendukung UI dashboard dan tabel dengan baik

Fallback font:

```css
font-family: "Inter", "Segoe UI", Roboto, Arial, sans-serif;
```

## 6.2 Font Alternatif

Jika **Inter** tidak tersedia, gunakan:

- **Segoe UI** untuk Windows desktop app
- **Roboto** untuk web app
- **Arial** sebagai fallback terakhir

## 6.3 Ukuran Font

Gunakan skala berikut:

| Elemen | Ukuran | Berat |
|---|---:|---:|
| Page Title | **28px** | **700** |
| Section Title | **20px** | **600** |
| Card Title | **16px** | **600** |
| Body Text | **14px** | **400** |
| Small Text | **12px** | **400** |
| Button Text | **14px** | **600** |
| Badge Text | **12px** | **600** |

## 6.4 Aturan Tipografi

1. Judul halaman harus jelas dan tidak terlalu panjang.
2. Gunakan **font weight 600 atau 700** untuk heading.
3. Gunakan **font weight 400** untuk teks penjelasan.
4. Hindari penggunaan huruf kapital penuh kecuali untuk badge kecil.
5. Teks tombol harus singkat dan berbentuk aksi, misalnya **Start Culling**, **Pilih Folder**, **Export Hasil**.

---

# 7. Elemen UI (UI Elements)

## 7.1 Gaya Umum

Gunakan gaya visual:

- **Clean dashboard style**
- **Rounded card layout**
- **Soft shadow**
- **Minimal border**
- **High readability**
- **Step-by-step workflow**

Aplikasi harus terasa seperti alat kerja modern, bukan seperti eksperimen teknis AI.

---

## 7.2 Tombol (Buttons)

### 7.2.1 Primary Button

Gunakan untuk aksi utama seperti **Start Culling**, **Pilih Folder Foto**, atau **Export Selected**.

Style:

```css
background: #2563EB;
color: #FFFFFF;
border-radius: 10px;
padding: 10px 16px;
font-weight: 600;
border: none;
```

Hover:

```css
background: #1D4ED8;
```

Disabled:

```css
background: #E5E7EB;
color: #94A3B8;
cursor: not-allowed;
```

### 7.2.2 Secondary Button

Gunakan untuk aksi tambahan seperti **Lihat Detail**, **Buka Folder**, atau **Reset Filter**.

Style:

```css
background: #FFFFFF;
color: #2563EB;
border: 1px solid #E2E8F0;
border-radius: 10px;
padding: 10px 16px;
font-weight: 600;
```

Hover:

```css
background: #EFF6FF;
```

### 7.2.3 Danger Button

Gunakan untuk aksi destruktif seperti **Hapus Hasil Analisis** atau **Kosongkan Folder Output**.

Style:

```css
background: #DC2626;
color: #FFFFFF;
border-radius: 10px;
padding: 10px 16px;
font-weight: 600;
```

---

## 7.3 Kartu Antarmuka (Cards)

Gunakan card untuk menampilkan ringkasan dan konten utama.

Style default:

```css
background: #FFFFFF;
border: 1px solid #E2E8F0;
border-radius: 16px;
box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
padding: 20px;
```

Aturan:

- Card tidak boleh terlalu padat.
- Setiap card harus memiliki judul yang jelas.
- Gunakan ikon kecil untuk membantu identifikasi jenis data.
- Card statistik harus menampilkan angka besar dan label kecil.

Contoh card statistik:

```text
Total Foto
2.438
```

```text
Selected
326
```

```text
Review
184
```

```text
Rejected
1.928
```

---

## 7.4 Badge Status

Gunakan badge untuk status foto.

### Selected

```css
background: #DCFCE7;
color: #166534;
```

Label: **Selected**

### Review

```css
background: #FEF3C7;
color: #92400E;
```

Label: **Review**

### Rejected

```css
background: #FEE2E2;
color: #991B1B;
```

Label: **Rejected**

### Duplicate

```css
background: #E0F2FE;
color: #075985;
```

Label: **Duplicate Group**

---

## 7.5 Input dan Form

Gunakan input yang bersih dan mudah dibaca.

Style:

```css
background: #FFFFFF;
border: 1px solid #CBD5E1;
border-radius: 10px;
padding: 10px 12px;
font-size: 14px;
```

Focus:

```css
border-color: #2563EB;
box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
```

Form utama yang harus ada:

- **Folder Input**
- **Folder Output**
- **Blur Threshold**
- **Exposure Minimum**
- **Exposure Maximum**
- **Duplicate Sensitivity**
- **Face Detection Toggle**

---

## 7.6 Progress Bar

Progress bar harus digunakan saat proses analisis foto berjalan.

Style:

```css
background-track: #E2E8F0;
background-fill: #2563EB;
border-radius: 999px;
height: 8px;
```

Tampilkan informasi:

```text
Memproses 348 dari 2.438 foto...
```

Jangan hanya menampilkan spinner tanpa informasi jumlah proses.

---

## 7.7 Tabel

Tabel digunakan untuk menampilkan daftar hasil analisis foto.

Kolom minimal:

1. **Thumbnail**
2. **Nama File**
3. **Blur Score**
4. **Brightness**
5. **Face Count**
6. **Duplicate Group**
7. **Final Score**
8. **Status**
9. **Action**

Style:

- Header tabel menggunakan background **#F1F5F9**.
- Border antar row menggunakan **#E2E8F0**.
- Row hover menggunakan **#F8FAFC**.
- Status harus menggunakan badge, bukan teks polos.

---

## 7.8 Thumbnail Grid

Untuk galeri foto, gunakan grid thumbnail.

Aturan:

- Thumbnail berbentuk card kecil dengan radius **12px**.
- Rasio thumbnail disarankan **4:3** atau **1:1**.
- Tampilkan badge status di pojok kanan atas.
- Tampilkan skor kecil di bawah nama file.
- Foto yang dipilih manual harus memiliki outline **#2563EB**.

---

## 7.9 Empty State

Jika belum ada folder dipilih atau belum ada hasil analisis, tampilkan empty state yang ramah.

Contoh teks:

> **Belum ada foto yang dianalisis**  
> Pilih folder dokumentasi terlebih dahulu untuk mulai melakukan culling otomatis.

Gunakan ikon sederhana seperti folder, image, atau spark.

---

## 7.10 Error State

Pesan error harus jelas, tidak teknis berlebihan.

Contoh:

> **Folder tidak ditemukan**  
> Pastikan folder foto masih tersedia dan coba pilih ulang folder tersebut.

Jangan tampilkan stack trace kepada pengguna biasa. Stack trace hanya boleh muncul di log developer.

---

# 8. Layout dan Navigasi Visual

## 8.1 Struktur Layout Utama

Gunakan layout desktop dengan struktur berikut:

```text
+------------------------------------------------------+
| Header: Logo, Nama Aplikasi, Status                  |
+----------------------+-------------------------------+
| Sidebar Navigation   | Main Content                  |
|                      |                               |
| Dashboard            | Halaman aktif                 |
| Import & Culling     |                               |
| Results              |                               |
| Settings             |                               |
+----------------------+-------------------------------+
```

## 8.2 Header

Header harus berisi:

- Logo **CullaGrace** di kiri.
- Nama aplikasi.
- Status proses di kanan, misalnya **Idle**, **Processing**, atau **Completed**.
- Tombol kecil **Open Output Folder** jika hasil sudah tersedia.

Style header:

```css
height: 64px;
background: #FFFFFF;
border-bottom: 1px solid #E2E8F0;
padding: 0 24px;
```

## 8.3 Sidebar

Sidebar harus berisi navigasi utama:

1. **Dashboard**
2. **Import & Culling**
3. **Results**
4. **Settings**
5. **About**

Style sidebar:

```css
width: 240px;
background: #FFFFFF;
border-right: 1px solid #E2E8F0;
padding: 16px;
```

Item aktif:

```css
background: #EFF6FF;
color: #2563EB;
font-weight: 600;
border-radius: 10px;
```

---

# 9. Tone of Voice and Context

## 9.1 Nada Bahasa Utama

Gunakan gaya bahasa:

- **Ramah**
- **Tenang**
- **Profesional**
- **Membantu**
- **Tidak menghakimi**
- **Tidak terlalu teknis**

Aplikasi digunakan oleh tim multimedia gereja, sehingga teks harus terasa mendukung pelayanan, bukan seperti sistem enterprise yang kaku.

## 9.2 Bahasa Utama Aplikasi

Bahasa utama aplikasi adalah **Bahasa Indonesia**.

Gunakan istilah bahasa Inggris hanya jika sudah umum dalam konteks teknis, misalnya:

- **Selected**
- **Review**
- **Rejected**
- **Blur Score**
- **Final Score**
- **Duplicate**

Jika memungkinkan, sertakan padanan Indonesia pada penjelasan.

Contoh:

```text
Selected — Foto yang direkomendasikan untuk dipakai.
Review — Foto yang perlu dicek ulang secara manual.
Rejected — Foto yang tidak disarankan untuk dipakai.
```

## 9.3 Contoh Microcopy

### Tombol

Gunakan teks tombol berikut:

- **Pilih Folder Foto**
- **Mulai Culling**
- **Lihat Hasil**
- **Buka Folder Output**
- **Export CSV**
- **Reset Pengaturan**
- **Simpan Pengaturan**

### Pesan Proses

Gunakan pesan seperti:

```text
Sedang menganalisis ketajaman foto...
```

```text
Sedang mencari foto yang mirip...
```

```text
Sedang mendeteksi wajah...
```

```text
Hampir selesai. Menyusun hasil akhir...
```

### Pesan Berhasil

```text
Culling selesai. Foto telah dikelompokkan ke dalam folder Selected, Review, dan Rejected.
```

### Pesan Review

```text
Beberapa foto membutuhkan pengecekan manual karena hasil analisis belum cukup yakin.
```

### Pesan Error

```text
Terjadi kendala saat membaca beberapa foto. Foto tersebut dilewati dan dicatat dalam laporan.
```

## 9.4 Hal yang Harus Dihindari dalam Bahasa

Jangan gunakan kalimat seperti:

- “Foto Anda buruk.”
- “Gagal total.”
- “AI tidak bisa memproses.”
- “File rusak parah.”

Gunakan alternatif yang lebih ramah:

- “Foto ini kurang direkomendasikan karena terdeteksi blur.”
- “Beberapa file tidak dapat dibaca.”
- “Silakan cek ulang folder sumber.”

---

# 10. Ikonografi

## 10.1 Gaya Ikon

Gunakan ikon dengan gaya:

- **Outline**
- **Rounded**
- **Minimal**
- **Konsisten secara visual**

Library ikon yang disarankan:

- **Lucide Icons**
- **Heroicons**
- **Feather Icons**

Jika menggunakan React, prioritaskan **lucide-react**.

## 10.2 Ikon yang Disarankan

Gunakan ikon berikut untuk elemen UI:

| Fungsi | Ikon yang Disarankan |
|---|---|
| Dashboard | LayoutDashboard |
| Import Folder | FolderOpen |
| Culling / AI | Sparkles atau ScanSearch |
| Selected | CheckCircle |
| Review | AlertCircle |
| Rejected | XCircle |
| Duplicate | Copy |
| Face Detection | Smile atau UserRound |
| Settings | Settings |
| Export | Download |
| Open Folder | Folder |

---

# 11. Gaya Data Visualization

## 11.1 Chart Ringkasan

Jika menampilkan chart, gunakan chart sederhana:

- Donut chart untuk distribusi **Selected**, **Review**, **Rejected**.
- Bar chart untuk jumlah masalah foto, misalnya **Blur**, **Underexposed**, **Overexposed**, **Duplicate**.

## 11.2 Warna Chart

Gunakan warna status:

- **Selected: #16A34A**
- **Review: #F59E0B**
- **Rejected: #DC2626**
- **Duplicate: #0891B2**

## 11.3 Aturan Chart

1. Jangan membuat chart terlalu ramai.
2. Selalu tampilkan angka dan label.
3. Chart hanya digunakan untuk membantu keputusan, bukan dekorasi.
4. Hindari animasi berlebihan.

---

# 12. Spacing dan Radius

## 12.1 Spacing Scale

Gunakan skala spacing berikut:

- **4px** untuk jarak sangat kecil
- **8px** untuk jarak antar elemen kecil
- **12px** untuk jarak internal komponen
- **16px** untuk jarak standar
- **24px** untuk jarak antar section
- **32px** untuk jarak antar blok besar

## 12.2 Border Radius

Gunakan radius berikut:

- **8px** untuk input kecil
- **10px** untuk tombol
- **12px** untuk thumbnail
- **16px** untuk card
- **20px** untuk modal besar

## 12.3 Shadow

Gunakan shadow halus:

```css
box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
```

Untuk modal:

```css
box-shadow: 0 20px 40px rgba(15, 23, 42, 0.18);
```

Jangan gunakan shadow berat pada semua elemen.

---

# 13. Halaman dan Identitas Visual per Halaman

## 13.1 Dashboard

Tujuan halaman:

Memberi ringkasan cepat tentang proses culling terakhir.

Komponen visual utama:

- Card **Total Foto**
- Card **Selected**
- Card **Review**
- Card **Rejected**
- Chart distribusi hasil
- Tombol **Mulai Culling Baru**
- Ringkasan folder terakhir

Nuansa halaman:

- Ringkas
- Optimis
- Memberi rasa kontrol

## 13.2 Import & Culling

Tujuan halaman:

Tempat pengguna memilih folder dan menjalankan analisis.

Komponen visual utama:

- Card **Pilih Folder Foto**
- Card **Folder Output**
- Panel **Pengaturan Analisis Cepat**
- Tombol besar **Mulai Culling**
- Progress bar
- Log proses ringkas

Nuansa halaman:

- Step-by-step
- Jelas
- Tidak menakutkan

## 13.3 Results

Tujuan halaman:

Menampilkan hasil culling dan membantu pengguna review foto.

Komponen visual utama:

- Filter status: **All**, **Selected**, **Review**, **Rejected**
- Search file name
- Toggle view: **Grid** dan **Table**
- Thumbnail grid
- Detail panel foto
- Tombol **Buka Folder Output**
- Tombol **Export CSV**

Nuansa halaman:

- Visual
- Cepat dipindai
- Mudah memilah

## 13.4 Settings

Tujuan halaman:

Mengatur threshold dan preferensi sistem.

Komponen visual utama:

- Slider **Blur Threshold**
- Slider **Exposure Minimum**
- Slider **Exposure Maximum**
- Slider **Duplicate Sensitivity**
- Toggle **Face Detection**
- Toggle **Copy Files to Output Folder**
- Tombol **Simpan Pengaturan**
- Tombol **Reset Default**

Nuansa halaman:

- Terkontrol
- Sederhana
- Tidak terlalu teknis

## 13.5 About

Tujuan halaman:

Menjelaskan aplikasi secara singkat.

Komponen visual utama:

- Logo **CullaGrace**
- Tagline
- Versi aplikasi
- Penjelasan singkat
- Catatan bahwa hasil AI tetap perlu dicek manusia

Contoh teks:

> **CullaGrace membantu tim multimedia gereja menyortir dokumentasi foto lebih cepat dengan analisis otomatis berbasis ketajaman, pencahayaan, kemiripan, dan deteksi wajah.**

---

# 14. Accessibility

Agen AI harus memperhatikan aksesibilitas dasar:

1. Kontras teks harus cukup jelas.
2. Jangan mengandalkan warna saja untuk membedakan status; gunakan juga label teks.
3. Semua tombol harus memiliki label yang jelas.
4. Ukuran klik minimal **40px** tinggi.
5. Teks kecil jangan kurang dari **12px**.
6. Status proses harus terlihat dalam teks, bukan hanya animasi.

---

# 15. Motion dan Animasi

Animasi harus minimal dan fungsional.

Gunakan animasi untuk:

- Loading progress
- Card muncul secara halus
- Hover tombol
- Perubahan status proses

Durasi animasi:

- **150ms–250ms** untuk hover dan transisi kecil
- **300ms** maksimal untuk transisi panel

Jangan gunakan animasi berlebihan seperti bounce, rotation terus-menerus, atau efek visual yang mengganggu.

---

# 16. Do and Don't

## 16.1 Do

Lakukan hal berikut:

- Gunakan **Inter** sebagai font utama.
- Gunakan **#2563EB** sebagai warna primer.
- Gunakan card putih dengan border halus.
- Gunakan status color secara konsisten.
- Gunakan Bahasa Indonesia yang ramah.
- Gunakan layout yang memandu pengguna dari kiri ke kanan atau atas ke bawah.
- Tampilkan progress yang jelas saat proses culling berlangsung.

## 16.2 Don't

Jangan lakukan hal berikut:

- Jangan membuat UI terlalu gelap untuk versi awal.
- Jangan menggunakan warna neon.
- Jangan menggunakan terlalu banyak gradient.
- Jangan menampilkan istilah teknis tanpa penjelasan.
- Jangan menyembunyikan hasil analisis penting.
- Jangan membuat tombol utama sulit ditemukan.
- Jangan membuat pengguna harus membuka banyak modal untuk menjalankan proses utama.

---

# 17. Prioritas Implementasi Visual Versi 1

Untuk versi pertama, agen AI harus memprioritaskan:

1. **Layout utama yang bersih**
2. **Halaman Import & Culling yang mudah dipakai**
3. **Progress bar yang informatif**
4. **Hasil culling dalam grid dan tabel**
5. **Badge status Selected, Review, Rejected**
6. **Card statistik di Dashboard**
7. **Pengaturan threshold sederhana**

Elemen seperti dark mode, animasi lanjutan, dan logo final dapat dibuat setelah fitur inti selesai.

---

# 18. Ringkasan Identitas Merek

Gunakan ringkasan berikut sebagai sumber kebenaran utama:

```text
Brand Name: CullaGrace
Tagline: Sortir foto pelayanan lebih cepat, rapi, dan bermakna.
Primary Color: #2563EB
Secondary Color: #F59E0B
Success Color: #16A34A
Warning Color: #F59E0B
Danger Color: #DC2626
Main Font: Inter
Visual Style: Clean, calm, modern, friendly, professional
Tone of Voice: Ramah, tenang, membantu, tidak terlalu teknis
Primary Users: Tim multimedia gereja yang bekerja cepat dengan banyak foto dokumentasi
Core UI Pattern: Dashboard + Sidebar + Card + Status Badge + Thumbnail Grid
```
