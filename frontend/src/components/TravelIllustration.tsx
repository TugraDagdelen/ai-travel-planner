import type { Copy } from '../i18n/copy'

export function TravelIllustration({ t }: { t: Copy }) {
  return <section className="postcard" aria-label={t.illustrationLabel}>
    <div className="postcard-copy"><span>{t.postcardLabel}</span><h2>{t.postcardTitle}</h2></div>
    <svg className="coast-illustration" viewBox="0 0 480 430" role="img" aria-label={t.illustrationLabel}>
      <defs>
        <linearGradient id="sea" x2="0.3" y2="1"><stop stopColor="#79b5af"/><stop offset="1" stopColor="#346b66"/></linearGradient>
        <pattern id="grain" width="7" height="7" patternUnits="userSpaceOnUse"><circle cx="1" cy="3" r="0.55" fill="#fff" opacity=".17"/></pattern>
      </defs>
      <circle cx="345" cy="76" r="48" fill="#edc77c"/>
      <path d="M0 164 74 110 133 133 216 79 293 151 373 135 480 169V430H0Z" fill="#b6c2af"/>
      <path d="M0 202C97 162 155 218 245 173S391 156 480 187V430H0Z" fill="url(#sea)"/>
      <path d="M0 244c91-24 132 26 219 2s181-22 261-2M0 275c91-24 132 26 219 2s181-22 261-2M0 311c91-24 132 26 219 2s181-22 261-2" fill="none" stroke="#b6d6c7" opacity=".35" strokeWidth="2"/>
      <path d="M0 240c48-36 114-21 165 14s61 98 160 114 123 34 155 62H0Z" fill="#e4ccab"/>
      <path d="M0 340c99-72 103-5 169 19s152 36 181 71H0Z" fill="#d7b28a"/>
      <path d="M21 403c72-53 78-105 120-108s50 76 116 75" fill="none" stroke="#f8ead3" strokeWidth="17"/>
      <g stroke="#754f3b" strokeWidth="2" strokeLinejoin="round">
        <path d="M27 233v-97h62v97Z" fill="#edddba"/><path d="m19 137 39-33 39 33Z" fill="#ba7155"/>
        <path d="M83 257V167h70v90Z" fill="#d98d6b"/><path d="m76 167 40-27 44 27Z" fill="#aa6348"/>
        <path d="M140 291v-83h61v83Z" fill="#f1d6ac"/><path d="m135 208 34-23 38 23Z" fill="#c07851"/>
      </g>
      <g fill="#41665b"><path d="M49 233v-31a10 10 0 0 1 20 0v31Z"/><path d="M106 257v-31a10 10 0 0 1 20 0v31Z"/><path d="M163 291v-29a9 9 0 0 1 18 0v29Z"/><rect x="43" y="154" width="12" height="18" rx="2"/><rect x="65" y="154" width="12" height="18" rx="2"/><rect x="98" y="184" width="12" height="19" rx="2"/><rect x="125" y="184" width="12" height="19" rx="2"/><rect x="151" y="223" width="11" height="16" rx="2"/><rect x="179" y="223" width="11" height="16" rx="2"/></g>
      <path d="m360 265 24 0-5 7h-14Z" fill="#f4e9ce"/><path d="M372 265v-28l17 23h-17" fill="#f5e7c8" stroke="#8c7353" strokeWidth="1.5"/>
      <g fill="#385c4b"><path d="M21 356c-34-36-15-85-4-112 29 44 39 80 4 112Z"/><path d="M231 352c-28-38-12-82 3-106 25 41 27 79-3 106Z"/><path d="M425 430c-43-56-17-109 4-142 30 56 40 95-4 142Z"/></g>
      <g stroke="#77573d" strokeWidth="4"><path d="M20 320v65M233 316v57M427 378v52"/></g>
      <path d="m242 101 9-5 8 4m-32 19 7-4 7 3" fill="none" stroke="#626d59" strokeWidth="2" strokeLinecap="round"/>
      <path d="M0 0h480v430H0Z" fill="url(#grain)"/>
    </svg>
    <div className="postcard-note"><span>↗</span>{t.postcardNote}<span className="postcard-stamp">ROTA<br/>EXPLORER</span></div>
  </section>
}
