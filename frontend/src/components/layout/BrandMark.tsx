export function BrandMark({ alt = '' }: { alt?: string }) {
  return <img className="brand-mark" src={`${import.meta.env.BASE_URL}favicon.svg`} width={40} height={40} alt={alt} />
}
