# Kevin Assurance frontend

Status 2026-11-02: shell presentasi React di src/App.tsx dengan ringkasan empat role. Belum ada auth/login API client, route guard, formulir wizard, compressor, upload progress, review viewer, business dashboards, user management atau export UI. Backend 164/164 bukan bukti frontend berfungsi; checklist fitur tetap 0/23.

## Menjalankan shell

Gunakan package-lock.json dan environment Node yang sesuai engine paket Vite yang terpasang. Dari folder frontend jalankan `npm ci`, `npm run dev`; `npm run build` menjalankan TypeScript dan Vite; `npm run lint` memakai Oxlint; `npm run preview` hanya preview hasil build. Audit dokumentasi ini memeriksa nama script/dependency dari package.json, tidak menjalankan ulang build atau membuktikan UI bisnis.

Dependensi declared: React/ReactDOM ^19.3.1, TypeScript ~7.0.2, Vite ^8.3.5, Tailwind ^4.3.3, Axios, router, Zod dan Lucide. Axios/router/Zod terpasang belum berarti flow bisnis terintegrasi. Zustand/TanStack React Query belum terpasang. Lihat [package.json](package.json), [kode shell](src/App.tsx).

## Kontrak implementasi berikut

Baca [status dan keputusan](../docs/19_Documentation_Status.md), [SRS](../docs/04_SRS.md), [API](../docs/08_API.md), [checklist](../docs/11_Checklist.md), serta [UI target](../docs/02_PRD.md). Login cookie memerlukan GET csrf, X-CSRFToken, credentials dan token CSRF yang dirotasi setelah login; jangan mengharapkan access_token JSON pada cookie login. Bearer endpoint bersifat eksplisit. NIK/identity dan password tidak disimpan ke browser secara otomatis oleh shell ini.

Target UI/performa, force-first-password-change, autosave dan storage PII tetap keputusan/backlog yang belum selesai. Jangan menganggap label Frontend Active pada shell berarti aplikasi operasional sudah siap. index.html adalah entry aplikasi, bukan dokumentasi HTML generated.
