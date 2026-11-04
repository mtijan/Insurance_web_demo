import type { AssuranceDetail } from '../../types/assurance'
import { DocumentUploadSlot } from './DocumentUploadSlot'

export function DocumentSlots({ detail, reload, activity }: { detail: AssuranceDetail; reload: () => Promise<unknown>; activity?: (busy: boolean) => void }) {
  const types = [...new Set([...detail.required_documents.flatMap(type => type.split(' OR ')), ...detail.documents.map(doc => doc.document_type)])]
  return <div className="document-grid">{types.map(type => <DocumentUploadSlot key={type} assuranceId={detail.id} type={type} documents={detail.documents.filter(doc => doc.document_type === type)} editable={detail.can_edit} reload={async () => { await reload() }} activity={activity} />)}</div>
}
