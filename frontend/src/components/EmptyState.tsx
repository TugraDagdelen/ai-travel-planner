import { ArrowRight, Luggage } from 'lucide-react'
import { Link } from 'react-router-dom'

export function EmptyState({ title, description, action }: { title: string; description: string; action: string }) {
  return <section className="empty-state"><div className="empty-illustration"><Luggage size={60} strokeWidth={1.2}/><span aria-hidden="true">✦</span></div><h1>{title}</h1><p>{description}</p><Link to="/" className="primary-button">{action}<ArrowRight size={18}/></Link></section>
}
