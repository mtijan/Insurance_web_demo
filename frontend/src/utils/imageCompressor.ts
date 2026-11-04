export interface CompressionMetrics { beforeBytes: number; afterBytes: number; beforeWidth: number; beforeHeight: number; afterWidth: number; afterHeight: number }
export interface CompressedImage { file: File; metrics: CompressionMetrics }

export async function compressImage(file: File): Promise<CompressedImage> {
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || /\.(exe|sh|bat|php|js)$/i.test(file.name) || file.size > 5 * 1024 * 1024 || !file.size) throw new Error('Pilih JPEG, PNG, atau WebP maksimal 5 MiB yang valid.')
  let bitmap: ImageBitmap
  try { bitmap = await createImageBitmap(file) } catch { throw new Error('Gambar rusak atau tidak dapat dibaca. Pilih berkas lain.') }
  try { return await encode(file, bitmap) } finally { bitmap.close() }
}
async function encode(file: File, bitmap: ImageBitmap): Promise<CompressedImage> {
  const scale = Math.min(1, 1080 / Math.max(bitmap.width, bitmap.height))
  const canvas = document.createElement('canvas')
  canvas.width = Math.max(1, Math.round(bitmap.width * scale)); canvas.height = Math.max(1, Math.round(bitmap.height * scale))
  const context = canvas.getContext('2d')
  if (!context) throw new Error('Browser tidak mendukung kompresi gambar. Gunakan browser yang didukung.')
  context.fillStyle = '#fff'; context.fillRect(0, 0, canvas.width, canvas.height)
  context.drawImage(bitmap, 0, 0, canvas.width, canvas.height)
  const blob = await new Promise<Blob>((resolve, reject) => canvas.toBlob(result => result ? resolve(result) : reject(new Error('Kompresi gagal. Pilih ulang gambar.')), 'image/jpeg', 0.8))
  const keepOriginal = scale === 1 && blob.size >= file.size
  const result = keepOriginal ? file : new File([blob], 'document.jpg', { type: blob.type })
  return { file: result, metrics: { beforeBytes: file.size, afterBytes: result.size, beforeWidth: bitmap.width, beforeHeight: bitmap.height, afterWidth: canvas.width, afterHeight: canvas.height } }
}
