import { ShieldCheck, Users, FileText, CheckCircle2 } from 'lucide-react'

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 text-white p-2 rounded-lg shadow-sm">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-slate-900">Kevin Assurance</h1>
            <p className="text-xs text-slate-500 font-medium">Internal Management Platform</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5" /> Frontend Active (Vite + Tailwind v4)
          </span>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-slate-800">Sistem Penjaminan Asuransi Kendaraan</h2>
          <p className="text-sm text-slate-600 mt-1">
            Pengelolaan formulir jaminan, verifikasi berkas bersyarat, dan underwriting terintegrasi.
          </p>
        </div>

        {/* 4 Roles Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-blue-600 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider">Peran 1</span>
              <Users className="w-4 h-4" />
            </div>
            <h3 className="font-semibold text-slate-900">Super Admin</h3>
            <p className="text-xs text-slate-500 mt-1">Manajemen akun, konfigurasi admin fee, & ekspor Excel.</p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-indigo-600 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider">Peran 2</span>
              <FileText className="w-4 h-4" />
            </div>
            <h3 className="font-semibold text-slate-900">Admin (Underwriting)</h3>
            <p className="text-xs text-slate-500 mt-1">Verifikasi berkas KTP, STNK, fisik motor & persetujuan polis.</p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-emerald-600 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider">Peran 3</span>
              <Users className="w-4 h-4" />
            </div>
            <h3 className="font-semibold text-slate-900">Agent</h3>
            <p className="text-xs text-slate-500 mt-1">Pendaftaran jaminan & pemantauan dealer binaan.</p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-amber-600 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider">Peran 4</span>
              <FileText className="w-4 h-4" />
            </div>
            <h3 className="font-semibold text-slate-900">Dealer</h3>
            <p className="text-xs text-slate-500 mt-1">Input data motor baru/lama dari cabang dealer resmi.</p>
          </div>
        </div>
      </main>
    </div>
  )
}
