# Kevin Assurance frontend

Status 2026-11-03: **6/23 sub-checklist Local Verified**. Login cookie/CSRF, forced password change, AuthProvider/role guard, layout, scoped assurance list, thumbnail/upload/progress/delete dan audit summary khusus Super Admin tersedia. Wizard/compressor/split review viewer/config/export/user-management UI belum selesai. PDF ringkasan ACTIVE dapat diunduh; dukungan karakter di luar font default masih terbatas.

Dari folder frontend jalankan `npm ci`, lalu `npm run dev`. `npm run build` memeriksa TypeScript dan membuat build Vite; `npm run lint` menjalankan Oxlint. Dev proxy `/api` menuju backend lokal `127.0.0.1:8000`; `KEVIN_TEST_BACKEND_URL` dapat mengganti target proxy untuk pengujian. Production memerlukan same-origin atau reverse proxy yang sesuai dan belum diverifikasi.

Backend memerlukan dependency pada `backend/requirements.txt`; untuk menjalankan seluruh test aplikasi gunakan `backend/requirements-dev.txt`. Pilih settings backend secara eksplisit: default `core.settings` memakai SQLite, sedangkan PostgreSQL lokal memakai `core.local_postgres_settings` dan konfigurasi lokal yang tidak disertakan Git. Migrasi `users.0003_first_login_password` diperlukan sebelum kode baru dipakai pada database persisten. Ambil dan verifikasi backup database/media, periksa target serta migration plan, lalu lakukan upgrade pada maintenance window. Pekerjaan ini belum menerapkan migrasi tersebut ke database kerja; jangan seed/reset akun existing sebagai bagian upgrade. Downgrade diblokir selama ada akun yang masih wajib mengganti password.

API client memakai Axios credentials + CSRF; JWT tidak disalin ke localStorage/sessionStorage. Login merotasi CSRF. Sesi required-password dibatasi server dan UI; perubahan password sukses mencabut semua sesi dan meminta login ulang. Tidak ada autosave PII browser. Error503/network, loading dan retry ditampilkan; password manager/paste memakai input native.

Verifikasi lokal terakhir: PostgreSQL **211/211 PASS**, SQLite **206 PASS + 5 pengujian khusus PostgreSQL dilewati**, serta enam alur browser live pada empat role. Screenshot 375/1440, keyboard, dan semantik diuji. Screen reader manual, staging, produksi, dan UAT belum diverifikasi. Runtime state memakai React hooks.

Dokumentasi dan log rinci tetap tersedia pada workspace lokal di `docs/evidence/open-findings-2026-11-03/`. Direktori `docs/` diabaikan oleh aturan Git yang berlaku; tools pengujian tambahan juga tidak termasuk dalam pengiriman ini. Instruksi build/lint di atas tidak membutuhkan tools tambahan tersebut.
