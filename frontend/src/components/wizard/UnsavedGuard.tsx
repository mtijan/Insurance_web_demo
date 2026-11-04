import { useEffect } from 'react'
import { useBlocker } from 'react-router-dom'
import { ConfirmDialog } from '../shared/ConfirmDialog'

export function UnsavedGuard({ dirty, busy }: { dirty: boolean; busy: boolean }) {
  const blocker = useBlocker(({ currentLocation, nextLocation }) => (dirty || busy) && currentLocation.pathname !== nextLocation.pathname)
  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => { if (dirty || busy) { event.preventDefault(); event.returnValue = '' } }
    window.addEventListener('beforeunload', warn)
    return () => window.removeEventListener('beforeunload', warn)
  }, [dirty, busy])
  if (blocker.state !== 'blocked') return null
  return <ConfirmDialog title="Tinggalkan perubahan?" close={() => blocker.reset()} busy={busy}><p>{busy ? 'Tunggu hasil permintaan server sebelum meninggalkan halaman.' : 'Isian yang belum disimpan akan hilang. Draft yang sudah disimpan tetap ada di server.'}</p><button disabled={busy} onClick={() => blocker.proceed()}>Tinggalkan halaman</button></ConfirmDialog>
}
