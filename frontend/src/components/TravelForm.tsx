import { useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { ArrowRight, CalendarDays, Check, Coffee, Landmark, MapPin, Palette, Trees } from 'lucide-react'
import type { Copy } from '../i18n/copy'
import type { Interest, TripRequest, ValidatedTripRequest } from '../types/trip'
import { isConnectionError, validatePreferences } from '../services/api'
import { validateDraft } from '../services/validation'
import type { ValidationErrors } from '../services/validation'

const interestOptions = [
  { value: 'culture', icon: Landmark }, { value: 'nature', icon: Trees },
  { value: 'food', icon: Coffee }, { value: 'art', icon: Palette },
] as const

interface Props {
  t: Copy
  draft: TripRequest
  onChange: (draft: TripRequest) => void
  onValidated: (result: ValidatedTripRequest) => void
}

export function TravelForm({ t, draft, onChange, onValidated }: Props) {
  const [errors, setErrors] = useState<ValidationErrors>({})
  const [failure, setFailure] = useState<'networkError' | 'requestError' | null>(null)
  const [pending, setPending] = useState(false)
  const submitting = useRef(false)
  const errorSummary = useRef<HTMLDivElement>(null)

  function update<K extends keyof TripRequest>(field: K, value: TripRequest[K]) {
    onChange({ ...draft, [field]: value })
    setFailure(null)
  }

  function toggleInterest(interest: Interest) {
    update('interests', draft.interests.includes(interest)
      ? draft.interests.filter(item => item !== interest) : [...draft.interests, interest])
  }

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (submitting.current) return
    const nextErrors = validateDraft(draft)
    setErrors(nextErrors)
    setFailure(null)
    if (Object.keys(nextErrors).length) {
      requestAnimationFrame(() => errorSummary.current?.focus())
      return
    }
    submitting.current = true
    setPending(true)
    try {
      onValidated(await validatePreferences(draft))
    } catch (error) {
      setFailure(isConnectionError(error) ? 'networkError' : 'requestError')
      requestAnimationFrame(() => errorSummary.current?.focus())
    } finally {
      submitting.current = false
      setPending(false)
    }
  }

  return <form className="travel-form" onSubmit={submit} noValidate aria-busy={pending}>
    <div className="form-heading"><span className="tiny-eyebrow">{t.phase}</span><h2>{t.formTitle}</h2><p>{t.formSubtitle}</p></div>
    {(Object.keys(errors).length > 0 || failure) && <div className="error-summary" role="alert" tabIndex={-1} ref={errorSummary}>{failure ? t[failure] : t.invalid}</div>}
    <fieldset className="form-fields" disabled={pending}>
      <div className="field">
        <label htmlFor="destination">{t.destination}</label>
        <div className="input-icon"><MapPin size={19} aria-hidden="true"/><input id="destination" name="destination" value={draft.destination} onChange={e => update('destination', e.target.value)} placeholder={t.destinationPlaceholder} maxLength={120} autoComplete="address-level2" required aria-invalid={Boolean(errors.destination)} aria-describedby={errors.destination ? 'destination-error' : undefined}/></div>
        {errors.destination && <p id="destination-error" className="field-error">{t[errors.destination]}</p>}
      </div>
      <div className="date-grid">
        <div className="field"><label htmlFor="start-date">{t.start}</label><div className="input-icon"><CalendarDays size={18} aria-hidden="true"/><input id="start-date" type="date" value={draft.start_date} onChange={e => update('start_date', e.target.value)} required aria-invalid={Boolean(errors.dates)} aria-describedby={errors.dates ? 'dates-error' : undefined}/></div></div>
        <div className="field"><label htmlFor="end-date">{t.end}</label><div className="input-icon"><CalendarDays size={18} aria-hidden="true"/><input id="end-date" type="date" value={draft.end_date} min={draft.start_date || undefined} onChange={e => update('end_date', e.target.value)} required aria-invalid={Boolean(errors.dates)} aria-describedby={errors.dates ? 'dates-error' : undefined}/></div></div>
      </div>
      {errors.dates && <p id="dates-error" className="field-error">{t[errors.dates]}</p>}
      <fieldset className="interest-field"><legend>{t.interests}</legend><p className="field-hint">{t.interestHint}</p><div className="interest-options">
        {interestOptions.map(({ value, icon: Icon }) => <button type="button" key={value} onClick={() => toggleInterest(value)} aria-pressed={draft.interests.includes(value)} aria-describedby={errors.interests ? 'interests-error' : undefined} className={`interest-option ${draft.interests.includes(value) ? 'selected' : ''}`}><Icon size={17} aria-hidden="true"/>{t[value]}{draft.interests.includes(value) && <Check size={14} aria-hidden="true"/>}</button>)}
      </div>{errors.interests && <p id="interests-error" className="field-error">{t[errors.interests]}</p>}</fieldset>
      <div className="date-grid">
        <div className="field"><label htmlFor="budget">{t.budget}</label><select id="budget" value={draft.budget} onChange={e => update('budget', e.target.value as TripRequest['budget'])}>{(['economy', 'balanced', 'flexible'] as const).map(value => <option value={value} key={value}>{t[value]}</option>)}</select></div>
        <div className="field"><label htmlFor="pace">{t.pace}</label><select id="pace" value={draft.pace} onChange={e => update('pace', e.target.value as TripRequest['pace'])}>{(['relaxed', 'balanced', 'active'] as const).map(value => <option value={value} key={value}>{t[value]}</option>)}</select></div>
      </div>
      <div className="field"><label htmlFor="notes">{t.notes} <span className="optional">({t.optional})</span></label><textarea id="notes" rows={3} value={draft.notes} onChange={e => update('notes', e.target.value)} placeholder={t.notesPlaceholder} maxLength={1000} aria-invalid={Boolean(errors.notes)}/><span className="character-count">{draft.notes.length}/1000</span>{errors.notes && <p className="field-error">{t[errors.notes]}</p>}</div>
      <button type="submit" className="primary-button">{pending ? t.checking : t.review}<ArrowRight size={18} aria-hidden="true"/></button>
    </fieldset>
    <p className="form-footnote">{t.formFootnote}</p>
  </form>
}
