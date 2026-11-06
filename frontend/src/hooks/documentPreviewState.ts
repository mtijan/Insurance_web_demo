import { createContext, useContext } from 'react'

export interface OriginalPreview { url: string; name: string }
export interface DocumentPreviewCache {
  previews: Record<string, OriginalPreview>
  create: (file: File) => OriginalPreview
  release: (preview: OriginalPreview) => void
  keep: (id: string, preview: OriginalPreview) => void
  remove: (id: string) => void
}
export const DocumentPreviewContext = createContext<DocumentPreviewCache | null>(null)
export function useDocumentPreviews() {
  const context = useContext(DocumentPreviewContext)
  if (!context) throw new Error('Document previews require a workspace provider.')
  return context
}
