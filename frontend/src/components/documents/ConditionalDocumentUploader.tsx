import type { AssuranceDetail } from '../../types/assurance'
import { DocumentSlots } from './DocumentSlots'

export function ConditionalDocumentUploader({ detail, reload, activity }: { detail: AssuranceDetail; reload: () => Promise<unknown>; activity: (busy: boolean) => void }) {
  return <section><h2>Dokumen {detail.vehicle_category === 'MOTOR_BARU' ? 'Motor Baru' : 'Motor Lama'}</h2>
    <p>{detail.vehicle_category === 'MOTOR_BARU' ? 'Empat dokumen wajib: KTP, Surat Jalan, Rangka, Mesin.' : 'Enam dokumen dasar wajib: KTP, STNK, Depan, Belakang, Kanan, Kiri; ditambah Rangka ATAU Mesin. Keduanya boleh.'}</p>
    <p>JPEG/PNG/WebP, maksimal 5 MiB per berkas. Pratinjau menampilkan file asli yang dipilih selama sesi pengisian. Berkas tersimpan dapat dibuka melalui tautannya.</p>
    <DocumentSlots detail={detail} reload={reload} activity={activity} />
    <p role="status">{detail.is_documents_complete ? 'Seluruh dokumen wajib tersedia menurut server.' : `Belum lengkap: ${detail.missing_documents.join(', ')}`}</p>
  </section>
}
