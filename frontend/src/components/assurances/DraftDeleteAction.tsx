import { useState } from 'react'
import { Trash2 } from 'lucide-react'
import { IconAction } from '../shared/IconAction'
import { DeleteConfirmation } from '../shared/DeleteConfirmation'

export function DraftDeleteAction({ id, name, done }: { id: string; name: string; done: () => Promise<unknown> }) {
  const [open, setOpen] = useState(false)
  return <>
    <IconAction label={`Hapus draft ${name}`} icon={Trash2} danger onClick={() => setOpen(true)} />
    {open && <DeleteConfirmation path={`assurances/${id}/`} label={`draft ${name}`} close={() => setOpen(false)} done={done} />}
  </>
}
