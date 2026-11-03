import { z } from 'zod'

export const loginSchema = z.object({
  username: z.string().trim().min(1, 'Isi username atau email.'),
  password: z.string().min(1, 'Isi password.'),
})
export const passwordSchema = z.object({
  current_password: z.string().min(1, 'Isi password saat ini.'),
  new_password: z.string().min(8, 'Password baru minimal 8 karakter.'),
}).refine(value => value.current_password !== value.new_password, {
  message: 'Gunakan password yang berbeda.', path: ['new_password'],
})
