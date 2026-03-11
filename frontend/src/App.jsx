import { useState, useEffect, useRef } from 'react'
import axios from 'axios'

const API_URL = 'http://localhost:8000'

// ─── MARKDOWN RENDERER (prosty) ───────────────────────────────────────────────
function SimpleMarkdown({ text }) {
  if (!text) return null
  const lines = text.split('\n')
  return (
    <div style={{ fontSize: '0.875rem', lineHeight: '1.6' }}>
      {lines.map((line, i) => {
        if (line.startsWith('### ')) return <h3 key={i} style={{ color: '#f97316', fontWeight: 'bold', margin: '0.75rem 0 0.25rem' }}>{line.slice(4)}</h3>
        if (line.startsWith('## '))  return <h2 key={i} style={{ color: '#60a5fa', fontWeight: 'bold', margin: '1rem 0 0.25rem' }}>{line.slice(3)}</h2>
        if (line.startsWith('# '))   return <h1 key={i} style={{ color: 'white', fontWeight: 'bold', margin: '1rem 0 0.5rem', fontSize: '1.1rem' }}>{line.slice(2)}</h1>
        if (line.startsWith('- ') || line.startsWith('* ')) return (
          <div key={i} style={{ marginLeft: '1rem', marginBottom: '0.2rem' }}>
            <span style={{ color: '#60a5fa' }}>•</span> {line.slice(2)}
          </div>
        )
        if (/^\d+\.\s/.test(line)) return <div key={i} style={{ marginLeft: '1rem', marginBottom: '0.2rem' }}>{line}</div>
        if (line.startsWith('```')) return <div key={i} style={{ height: '0.5rem' }} />
        if (!line.trim()) return <div key={i} style={{ height: '0.5rem' }} />
        // Bold
        const parts = line.split(/(\*\*[^*]+\*\*)/g)
        return (
          <p key={i} style={{ marginBottom: '0.3rem' }}>
            {parts.map((p, j) =>
              p.startsWith('**') && p.endsWith('**')
                ? <strong key={j} style={{ color: '#fbbf24' }}>{p.slice(2, -2)}</strong>
                : p
            )}
          </p>
        )
      })}
    </div>
  )
}

// ─── ANSWER CARD ──────────────────────────────────────────────────────────────
function AnswerCard({ title, answer, sources, mode, convId, onRate, color }) {
  const [rated, setRated] = useState(null)

  const handleRate = async (rating) => {
    if (rated) return
    setRated(rating)
    await onRate(convId, mode, rating)
  }

  return (
    <div style={{
      flex: 1, background: '#111827', border: `1px solid ${color}33`,
      borderRadius: '0.75rem', padding: '1.25rem', display: 'flex', flexDirection: 'column'
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div>
          <span style={{
            background: color + '22', color, border: `1px solid ${color}44`,
            padding: '0.25rem 0.75rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 'bold'
          }}>
            {title}
          </span>
        </div>
        {convId && (
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button onClick={() => handleRate(1)}
              style={{
                background: rated === 1 ? '#16a34a' : '#1f2937',
                border: '1px solid #374151', borderRadius: '0.5rem',
                padding: '0.25rem 0.75rem', cursor: rated ? 'default' : 'pointer',
                fontSize: '1rem', opacity: rated && rated !== 1 ? 0.4 : 1
              }}>👍</button>
            <button onClick={() => handleRate(-1)}
              style={{
                background: rated === -1 ? '#dc2626' : '#1f2937',
                border: '1px solid #374151', borderRadius: '0.5rem',
                padding: '0.25rem 0.75rem', cursor: rated ? 'default' : 'pointer',
                fontSize: '1rem', opacity: rated && rated !== -1 ? 0.4 : 1
              }}>👎</button>
          </div>
        )}
      </div>

      {/* Answer */}
      <div style={{ flex: 1, color: '#e5e7eb', overflowY: 'auto', maxHeight: '400px' }}>
        {answer
          ? <SimpleMarkdown text={answer} />
          : <p style={{ color: '#6b7280', fontStyle: 'italic' }}>Brak odpowiedzi</p>
        }
      </div>

      {/* Sources (RAG only) */}
      {sources && sources.length > 0 && (
        <div style={{ marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid #1f2937' }}>
          <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>📎 Źródła: </span>
          {sources.map((s, i) => (
            <span key={i} style={{
              fontSize: '0.7rem', background: '#1e3a5f', color: '#93c5fd',
              padding: '0.1rem 0.5rem', borderRadius: '9999px', margin: '0 0.2rem'
            }}>{s}</span>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── STATS BAR ────────────────────────────────────────────────────────────────
function StatsBar({ stats }) {
  if (!stats || stats.total_conversations === 0) return null
  const ragScore = stats.rag.thumbs_up - stats.rag.thumbs_down
  const ftScore  = stats.finetuned.thumbs_up - stats.finetuned.thumbs_down
  return (
    <div style={{ display: 'flex', gap: '1rem', padding: '0.75rem 1rem', background: '#0f172a', borderRadius: '0.5rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
      <span style={{ color: '#6b7280', fontSize: '0.8rem' }}>📊 {stats.total_conversations} rozmów</span>
      <span style={{ color: '#3b82f6', fontSize: '0.8rem' }}>RAG: 👍{stats.rag.thumbs_up} 👎{stats.rag.thumbs_down} (wynik: {ragScore > 0 ? '+' : ''}{ragScore})</span>
      <span style={{ color: '#a855f7', fontSize: '0.8rem' }}>Fine-tune: 👍{stats.finetuned.thumbs_up} 👎{stats.finetuned.thumbs_down} (wynik: {ftScore > 0 ? '+' : ''}{ftScore})</span>
      <span style={{ color: ragScore >= ftScore ? '#22c55e' : '#a855f7', fontSize: '0.8rem', fontWeight: 'bold' }}>
        🏆 Lepszy model: {ragScore >= ftScore ? 'RAG' : 'Fine-tune'}
      </span>
    </div>
  )
}

// ─── HISTORY VIEW ─────────────────────────────────────────────────────────────
function HistoryView({ onSelectQuestion }) {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get(`${API_URL}/history`)
      .then(r => setHistory(r.data))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p style={{ color: '#6b7280', textAlign: 'center', padding: '2rem' }}>Ładowanie historii...</p>
  if (!history.length) return <p style={{ color: '#6b7280', textAlign: 'center', padding: '2rem' }}>Brak historii rozmów.</p>

  return (
    <div>
      {history.map(item => (
        <div key={item.id} style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '0.75rem', padding: '1rem', marginBottom: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <button onClick={() => onSelectQuestion(item.question)}
              style={{ color: '#60a5fa', fontWeight: 'bold', background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', fontSize: '0.9rem' }}>
              ❓ {item.question}
            </button>
            <span style={{ color: '#4b5563', fontSize: '0.75rem', whiteSpace: 'nowrap', marginLeft: '1rem' }}>{item.timestamp}</span>
          </div>
          <div style={{ display: 'flex', gap: '2rem', fontSize: '0.8rem' }}>
            <span style={{ color: '#3b82f6' }}>RAG: {item.rag_rating === 1 ? '👍' : item.rag_rating === -1 ? '👎' : '—'}</span>
            <span style={{ color: '#a855f7' }}>Fine-tune: {item.ft_rating === 1 ? '👍' : item.ft_rating === -1 ? '👎' : '—'}</span>
            {item.sources?.length > 0 && <span style={{ color: '#6b7280' }}>📎 {item.sources.join(', ')}</span>}
          </div>
        </div>
      ))}
    </div>
  )
}

// ─── UPLOAD PDF ───────────────────────────────────────────────────────────────
function UploadPDF({ onUploaded }) {
  const [uploading, setUploading] = useState(false)
  const [message, setMessage]     = useState(null)
  const inputRef = useRef()

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    setMessage(null)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await axios.post(`${API_URL}/upload-pdf`, form)
      setMessage({ type: 'ok', text: `✅ ${res.data.message}` })
      onUploaded()
    } catch (err) {
      setMessage({ type: 'err', text: `❌ ${err.response?.data?.detail || 'Błąd uploadu'}` })
    } finally {
      setUploading(false)
    }
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
      <input ref={inputRef} type="file" accept=".pdf" onChange={handleUpload} style={{ display: 'none' }} />
      <button onClick={() => inputRef.current.click()} disabled={uploading}
        style={{
          background: uploading ? '#1f2937' : '#1e3a5f', color: uploading ? '#6b7280' : '#93c5fd',
          border: '1px solid #2563eb33', borderRadius: '0.5rem', padding: '0.5rem 1rem',
          cursor: uploading ? 'not-allowed' : 'pointer', fontSize: '0.85rem'
        }}>
        {uploading ? '⏳ Dodawanie...' : '📄 Dodaj PDF do RAG'}
      </button>
      {message && (
        <span style={{ fontSize: '0.8rem', color: message.type === 'ok' ? '#22c55e' : '#ef4444' }}>
          {message.text}
        </span>
      )}
    </div>
  )
}

// ─── MAIN APP ─────────────────────────────────────────────────────────────────
export default function App() {
  const [question, setQuestion]     = useState('')
  const [loading, setLoading]       = useState(false)
  const [result, setResult]         = useState(null)
  const [error, setError]           = useState(null)
  const [activeTab, setActiveTab]   = useState('chat')
  const [stats, setStats]           = useState(null)
  const [historyKey, setHistoryKey] = useState(0)

  const loadStats = () => {
    axios.get(`${API_URL}/stats`).then(r => setStats(r.data)).catch(() => {})
  }

  useEffect(() => { loadStats() }, [historyKey])

  const handleAsk = async () => {
    if (!question.trim() || loading) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await axios.post(`${API_URL}/ask`, { question })
      setResult(res.data)
      setActiveTab('chat')
    } catch (err) {
      setError(err.response?.data?.detail || 'Błąd połączenia z API')
    } finally {
      setLoading(false)
    }
  }

  const handleRate = async (convId, mode, rating) => {
    await axios.post(`${API_URL}/rate`, { conv_id: convId, mode, rating })
    loadStats()
    setHistoryKey(k => k + 1)
  }

  const tabs = [
    { id: 'chat',    label: '💬 Chat' },
    { id: 'history', label: '📁 Historia' },
  ]

  return (
    <div style={{ minHeight: '100vh', width: '100%', background: '#030712', color: 'white', fontFamily: 'system-ui, sans-serif' }}>
      <div style={{ width: '100%', padding: '2rem' }}>

        {/* HEADER */}
        <div style={{ marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>
            🧠 PAN-OS AI Assistant
          </h1>
          <p style={{ color: '#6b7280', fontSize: '0.9rem' }}>
            Porównanie RAG vs Fine-tuned model na dokumentacji Palo Alto Networks
          </p>
        </div>

        {/* STATS */}
        <StatsBar stats={stats} />

        {/* UPLOAD + TABS */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {tabs.map(tab => (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                style={{
                  padding: '0.5rem 1rem', borderRadius: '0.5rem', fontWeight: 'medium',
                  background: activeTab === tab.id ? '#1d4ed8' : '#1f2937',
                  color: activeTab === tab.id ? 'white' : '#9ca3af',
                  border: 'none', cursor: 'pointer'
                }}>
                {tab.label}
              </button>
            ))}
          </div>
          <UploadPDF onUploaded={() => setHistoryKey(k => k + 1)} />
        </div>

        {/* CHAT TAB */}
        {activeTab === 'chat' && (
          <div>
            {/* INPUT */}
            <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '2rem' }}>
              <input
                type="text"
                value={question}
                onChange={e => setQuestion(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleAsk()}
                placeholder="Zapytaj o PAN-OS... np. 'Jak skonfigurować Security Policy?'"
                style={{
                  flex: 1, background: '#111827', color: 'white',
                  border: '1px solid #374151', borderRadius: '0.75rem',
                  padding: '0.875rem 1.25rem', fontSize: '0.95rem',
                  outline: 'none'
                }}
              />
              <button onClick={handleAsk} disabled={loading || !question.trim()}
                style={{
                  background: loading || !question.trim() ? '#1f2937' : '#1d4ed8',
                  color: loading || !question.trim() ? '#6b7280' : 'white',
                  border: 'none', borderRadius: '0.75rem',
                  padding: '0.875rem 1.5rem', cursor: loading ? 'not-allowed' : 'pointer',
                  fontWeight: 'bold', fontSize: '0.9rem', whiteSpace: 'nowrap'
                }}>
                {loading ? '⏳ Pytam...' : '🔍 Zapytaj'}
              </button>
            </div>

            {/* SUGGESTED QUESTIONS */}
            {!result && !loading && (
              <div style={{ marginBottom: '2rem' }}>
                <p style={{ color: '#4b5563', fontSize: '0.8rem', marginBottom: '0.75rem' }}>💡 Przykładowe pytania:</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {[
                    'Jak skonfigurować Security Policy w PAN-OS?',
                    'Co to jest App-ID i jak działa?',
                    'Jak działa WildFire?',
                    'Jak skonfigurować NAT na Palo Alto?',
                    'Jaka jest różnica między Zone i Interface?',
                    'Jak włączyć SSL Inspection?'
                  ].map((q, i) => (
                    <button key={i} onClick={() => { setQuestion(q); }}
                      style={{
                        background: '#111827', color: '#60a5fa',
                        border: '1px solid #1e3a5f', borderRadius: '9999px',
                        padding: '0.4rem 0.9rem', cursor: 'pointer', fontSize: '0.8rem'
                      }}>
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* ERROR */}
            {error && (
              <div style={{ background: '#1f0a0a', border: '1px solid #7f1d1d', color: '#fca5a5', padding: '1rem', borderRadius: '0.75rem', marginBottom: '1.5rem' }}>
                ⚠️ {error}
              </div>
            )}

            {/* LOADING */}
            {loading && (
              <div style={{ textAlign: 'center', padding: '4rem', color: '#6b7280' }}>
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🤔</div>
                <p>Pytam oba modele jednocześnie...</p>
                <p style={{ fontSize: '0.8rem', marginTop: '0.5rem' }}>RAG przeszukuje dokumenty, Fine-tune odpowiada z pamięci</p>
              </div>
            )}

            {/* RESULTS — dwa modele obok siebie */}
            {result && !loading && (
              <div>
                <div style={{ marginBottom: '1rem', padding: '0.75rem 1rem', background: '#0f172a', borderRadius: '0.5rem' }}>
                  <span style={{ color: '#9ca3af', fontSize: '0.85rem' }}>❓ </span>
                  <span style={{ color: 'white', fontWeight: 'bold' }}>{result.question}</span>
                  <span style={{ color: '#4b5563', fontSize: '0.75rem', marginLeft: '1rem' }}>{result.timestamp}</span>
                </div>

                <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
                  <AnswerCard
                    title="🔍 RAG — wyszukiwanie w dokumentach"
                    answer={result.rag.answer}
                    sources={result.rag.sources}
                    mode="rag"
                    convId={result.id}
                    onRate={handleRate}
                    color="#3b82f6"
                  />
                  <AnswerCard
                    title="🧠 Fine-tuned Model"
                    answer={result.finetuned.answer}
                    sources={null}
                    mode="ft"
                    convId={result.id}
                    onRate={handleRate}
                    color="#a855f7"
                  />
                </div>

                <div style={{ marginTop: '1rem', padding: '0.75rem 1rem', background: '#0f172a', borderRadius: '0.5rem', fontSize: '0.8rem', color: '#6b7280' }}>
                  💡 <strong style={{ color: '#9ca3af' }}>Czym się różnią?</strong> RAG przeszukuje Twoje dokumenty i cytuje źródła.
                  Fine-tuned model odpowiada z wiedzy wbudowanej podczas treningu — szybciej, ale bez aktualizacji w czasie rzeczywistym.
                </div>
              </div>
            )}
          </div>
        )}

        {/* HISTORY TAB */}
        {activeTab === 'history' && (
          <HistoryView key={historyKey} onSelectQuestion={q => { setQuestion(q); setActiveTab('chat') }} />
        )}
      </div>
    </div>
  )
}