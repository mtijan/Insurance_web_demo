export function AuthBackdrop() {
  return <div className="auth-backdrop" aria-hidden="true">
    <svg className="auth-motif auth-motif-left" viewBox="0 0 360 420" fill="none">
      <g className="auth-spin">
        <circle cx="132" cy="184" r="108" stroke="currentColor" strokeOpacity="0.14" strokeWidth="1" strokeDasharray="4 7" />
        <circle cx="132" cy="184" r="74" stroke="currentColor" strokeOpacity="0.1" strokeWidth="0.9" />
      </g>
      <rect x="78" y="130" width="108" height="108" rx="14" transform="rotate(24 132 184)" stroke="currentColor" strokeOpacity="0.13" strokeWidth="1" />
      <g className="auth-sway">
        <path d="M54 398C66 322 104 252 152 178" stroke="currentColor" strokeOpacity="0.22" strokeWidth="1.25" />
        <path d="M98 268C70 250 56 226 62 204C86 210 102 234 98 268Z" fill="currentColor" fillOpacity="0.035" stroke="currentColor" strokeOpacity="0.2" strokeWidth="1.1" />
        <path d="M126 220C156 216 178 198 182 176C158 176 138 192 126 220Z" fill="currentColor" fillOpacity="0.035" stroke="currentColor" strokeOpacity="0.18" strokeWidth="1.1" />
        <path d="M78 318C48 308 32 288 34 268C58 270 76 290 78 318Z" stroke="currentColor" strokeOpacity="0.17" strokeWidth="1.1" />
      </g>
      <circle cx="204" cy="116" r="3" fill="currentColor" fillOpacity="0.18" />
    </svg>
    <svg className="auth-motif auth-motif-right" viewBox="0 0 380 420" fill="none">
      <g className="auth-spin-rev">
        <polygon points="242,88 302,122 302,190 242,224 182,190 182,122" stroke="currentColor" strokeOpacity="0.12" strokeWidth="1" />
        <circle cx="242" cy="156" r="88" stroke="currentColor" strokeOpacity="0.14" strokeWidth="1" strokeDasharray="3 8" />
      </g>
      <g className="auth-drift">
        <path d="M332 404C308 334 274 266 220 202" stroke="currentColor" strokeOpacity="0.22" strokeWidth="1.25" />
        <path d="M278 290C308 274 326 250 324 226C298 232 280 256 278 290Z" fill="currentColor" fillOpacity="0.035" stroke="currentColor" strokeOpacity="0.2" strokeWidth="1.1" />
        <path d="M250 246C222 248 198 234 190 212C214 208 238 222 250 246Z" fill="currentColor" fillOpacity="0.035" stroke="currentColor" strokeOpacity="0.18" strokeWidth="1.1" />
        <path d="M304 342C276 346 254 334 246 314C270 310 292 320 304 342Z" stroke="currentColor" strokeOpacity="0.16" strokeWidth="1.1" />
      </g>
      <line x1="146" y1="304" x2="226" y2="304" stroke="currentColor" strokeOpacity="0.14" strokeWidth="1" strokeDasharray="4 6" />
      <circle cx="146" cy="304" r="2.5" fill="currentColor" fillOpacity="0.2" />
    </svg>
  </div>
}
