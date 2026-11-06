import { useCallback, useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { DocumentPreviewContext } from '../../hooks/documentPreviewState'
import type { OriginalPreview } from '../../hooks/documentPreviewState'

export function DocumentPreviewProvider({ children }: { children: ReactNode }) {
  const [previews, setPreviews] = useState<Record<string, OriginalPreview>>({})
  const urls = useRef(new Set<string>())
  useEffect(() => () => { urls.current.forEach(url => URL.revokeObjectURL(url)); urls.current.clear() }, [])
  const create = useCallback((file: File) => {
    const preview = { url: URL.createObjectURL(file), name: file.name }
    urls.current.add(preview.url); return preview
  }, [])
  const release = useCallback((preview: OriginalPreview) => { URL.revokeObjectURL(preview.url); urls.current.delete(preview.url) }, [])
  const keep = useCallback((id: string, preview: OriginalPreview) => setPreviews(current => ({ ...current, [id]: preview })), [])
  const remove = useCallback((id: string) => {
    if (previews[id]) release(previews[id])
    setPreviews(current => { const next = { ...current }; delete next[id]; return next })
  }, [previews, release])
  return <DocumentPreviewContext.Provider value={{ previews, create, release, keep, remove }}>{children}</DocumentPreviewContext.Provider>
}
