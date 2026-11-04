# Kevin Assurance frontend

Status 2026-11-04 WIB: **20/23 sub-checklist Local Verified; 3 Partial**.
Aplikasi React kini mempunyai sidebar responsif, daftar/detail/ringkasan scoped,
wizard lima tahap/draft eksplisit, kalkulasi server, dokumen kedua kategori,
kompresi terukur, antrean/viewer/putusan/revisi, serta master/biaya/Excel/audit.

Dari frontend: `npm.cmd ci`, lalu `npm.cmd run dev`. Build: `npm.cmd run build`;
lint: `npm.cmd run lint`. Dependency aktual tetap package.json/lock existing;
tidak ada dependency baru pada fase ini. Dev proxy /api menuju127.0.0.1:8000;
KEVIN_TEST_BACKEND_URL dapat mengganti target hanya untuk verifikasi lokal.
Production same-origin/reverse proxy dan SPA fallback belum diverifikasi.

Backend memakai requirements.txt dan requirements-dev.txt untuk seluruh suite.
Default core.settings memakai SQLite; PostgreSQL lokal dipilih eksplisit.
users.0003_first_login_password masih memerlukan upgrade persisten terencana:
backup DB/media, verifikasi target/owner, migration plan dan maintenance window.
Fase ini tidak menjalankan migrate/seed/reset pada database kerja. Tidak ada
migrasi schema baru untuk frontend/filter. Jangan menguji terhadap database kerja.

Login cookie HttpOnly+CSRF terpusat; force-change restricted sampai ganti password
dan login ulang. Profil/izin diperbarui saat fokus; server otoritas scope/status.
Draft disimpan eksplisit sesudah field create API terpenuhi. Tidak ada autosave,
PII/token/file dalam localStorage/sessionStorage, atau query URL berisi identitas.
Premi/admin/total/tanggal akhir dari server; draft lama mempertahankan snapshot.

Menu: /dashboard, /, /assurances/new, /review, /dealers; Super Admin juga
/admin/users, /admin/assignments, /admin/reports, /admin/settings/admin-fee, /audit.
Detail /assurances/:id; lanjut /assurances/:id/edit; review /review/:id.
ACTIVE selalu readonly. REJECT berarti REVISION, bukan penolakan permanen.
Filter dealer/status dan tanggal pembuatan WIB diterapkan server; total Ringkasan
hanya data yang dimuat. PDF tetap ringkasan ACTIVE scoped dengan gap font Unicode.

Kompresi menerima JPEG/PNG/WebP<=5MiB sebelum resize, long edge<=1080px.
Ukuran/dimensi aktual ditampilkan; gambar kecil dapat dipertahankan tanpa reduksi.
P0-FE-03/Sub-1 Partial untuk target80%/tanpa blur universal. P0-FE-05/Sub-3
Partial karena aturan SLA belum disahkan. Tidak mengarang SLA atau kebijakan bisnis.

Verifikasi frontend terbaru: **46/46 task checks**, termasuk tujuh tes Origin
baru; tujuh tes tersebut juga lulus di Chrome berjendela otomatis. Lima tes
privasi lulus. Backend225/225 PostgreSQL dan220PASS+5PGskip SQLite adalah bukti
fase diagnosis sebelumnya; tidak dijalankan ulang pada penambahan testini.
Build/lint dan gate struktur lulus; screenshot375/1440 serta boundary320/768/1024
tersedia. Login manusia tetap gagal ORIGIN_REJECTED danOPEN; AT/UAT belum.

Di root, verifikasi disposable (nama phase wajib unik):
```powershell
& backend/venv/Scripts/python.exe tools/run_frontend_verification.py --phase local-check-YYYYMMDD-HHMMSS
node tools/check_frontend_structure.cjs
```

Bukti lengkap lokal: [laporan](../docs/evidence/frontend-implementation-20261103-231847/final-report.md),
[matriks](../docs/evidence/frontend-implementation-20261103-231847/checklist-matrix.md),
[protokol manusia/AT/UAT](../docs/evidence/frontend-implementation-20261103-231847/manual-test.md).
Direktori docs/ tetap diabaikan Git; tidak ada commit/push/deploy fase ini.

Untuk cek manual, dari root jalankan `backend/venv/Scripts/python.exe tools/run_frontend_manual.py`.
Masukkan password uji, lalu buka URL Aplikasi yang tercetak. Akun ui_dealer,
ui_agent, ui_admin dan ui_super_admin memakai password tersebut; Dealer perlu
menggantinya saat login pertama. Gunakan data sintetis. Ctrl+C membersihkan
server/database/media disposable; hasil manusia dicatat terpisah dari smoke.

Tindak lanjut CSRF2026-11-04: klien mengambil token baru sebelum mutasi dan
tidak mengulang POST otomatis. Runner membedakan cookie CSRF per port agar tidak
berbenturan dengan aplikasi lokal lain. Hentikan runner lama dengan Ctrl+C lalu
jalankan perintah manual di atas kembali. Buka URL baru yang dicetak; jika masih
gagal, gunakan jendela Private/Incognito dan pastikan cookie untuk alamat itu
diizinkan. Jangan kirim password/token/cookie atau ekspor HAR mentah.
Tes CSRF terarah: `backend/venv/Scripts/python.exe tools/run_frontend_verification.py --phase csrf-YYYYMMDD-HHMMSS --suite csrf`.
[Bukti perbaikan](../docs/evidence/frontend-csrf-20261104-101957-368687/report.md).

Diagnosis lanjutan2026-11-04: kodeCSRF_ORIGIN_REJECTED terkonfirmasi pada Chrome biasa dan Incognito pengguna; P0-FE-01/Sub-3 kembaliPartial, semua server/runner telah dihentikan atas permintaan pengguna. Diagnostik aman sudah tersedia, tetapi penyebab nilaiOrigin belum diselesaikan. Tidak perlu menyalakan ulang sebelum pemeriksaan berikutnya. Regresi terbaru39browserchecks,225PG/220SQLite+5skip. [Laporan](../docs/evidence/frontend-csrf-diagnosis-20261104-104435-028882/report.md).

Tes browser Origin tambahan (FR-AUTH-01): suite `origin` memeriksa empatrole,
localhost, Origin null dan port salah, perbandingan browser-proxy-Django serta
retry eksplisit. Default suitefull kini mencakup46kasus; hasil aktual ada di
[laporan browser](../docs/evidence/frontend-browser-origin-20261104-110559-371863/report.md). Opsi `--headed` menjalankan Chrome
berjendela dengan profil otomatis baru; ini bukan pengujian manusia/profilpribadi.

Dari root, gunakan nama fase unik:
```powershell
& .\backend\venv\Scripts\python.exe .\tools\run_frontend_verification.py --suite origin --headed --phase "origin-$(Get-Date -Format yyyyMMdd-HHmmss-fff)"
```

Driver Playwright memakai lokasi lokal existing atau `PLAYWRIGHT_DRIVER_DIR`;
Chrome memakai lokasi existing atau `CHROME_PATH`. Tidak ada dependency baru.
Metadata Origin hanya direkam pada settings disposable verifikasi; normal/produksi
tidak berubah. Log berisi originloopback/trustlist, host, status dan boolean
keberadaan CSRF, tanpa body/token/cookie/password. Server testdibersihkan setelah
run. Masalah login manusia CSRF-USER-01 tetapOPEN; jumlahfrontend20/23.

Debug terpisah memakai port tetap dan database disposable. Terminal pertama dari
root: `backend/venv/Scripts/python.exe tools/run_debug_backend.py`; tentukan password
uji, lalu Django berjalan langsung di127.0.0.1:8000 tanpa autoreloader. Terminal
kedua dari frontend: set KEVIN_TEST_BACKEND_URL=http://127.0.0.1:8000 dan
UI_BASE_URL=http://127.0.0.1:5173, lalu `node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort`.
Buka http://127.0.0.1:5173/login. Ctrl+C pada masing-masing terminal; backend
menutup koneksi dan membersihkan database/media sementara. Mode `--check`
hanya memverifikasi bootstrap/cleanup, bukan login manusia. Error Origin yang
hilang port tetap memerlukan pemeriksaan header aktual; tidak ditutup oleh mode ini.


Alur peninjauan2026-11-04: Agent memberi catatan/revisi pada dealer binaan; Dealer melihat flag data/berkas dan histori; Admin/Super Admin memutuskan setujui/revisi/tolak final. [Hasil otomatis dan migrasi lokal](../docs/evidence/workflow-review-2026-11-04/report.md).
