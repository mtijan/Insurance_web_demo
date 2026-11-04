import type { ReactNode } from 'react'
interface Column<T> { label: string; render: (row: T) => ReactNode }
export function DataTable<T extends { id: string }>({ rows, columns, label }: { rows: T[]; columns: Column<T>[]; label: string }) {
  return <table className="data-table"><caption className="sr-only">{label}</caption><thead><tr>{columns.map(column => <th scope="col" key={column.label}>{column.label}</th>)}</tr></thead><tbody>{rows.map(row => <tr key={row.id}>{columns.map(column => <td key={column.label}><span className="cell-label" aria-hidden="true">{column.label}</span><div className="cell-value">{column.render(row)}</div></td>)}</tr>)}</tbody></table>
}
