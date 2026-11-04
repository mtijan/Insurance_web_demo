export function Feedback({ loading, error, retry }: { loading: boolean; error: string; retry: () => unknown }) {
  if (loading) return <p role="status" className="feedback">Memuat data…</p>
  if (error) return <div role="alert" className="error"><p>{error}</p><button className="secondary" onClick={() => void retry()}>Coba lagi</button></div>
  return null
}
