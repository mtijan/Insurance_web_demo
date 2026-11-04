export const money = (value: string | number) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 2 }).format(Number(value))
export const dateLabel = (value: string) => new Intl.DateTimeFormat('id-ID', { dateStyle: 'long', timeZone: 'Asia/Jakarta' }).format(new Date(value.length === 10 ? value + 'T00:00:00+07:00' : value))
