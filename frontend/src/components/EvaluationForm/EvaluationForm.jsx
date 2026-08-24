import { useEffect, useState } from 'react'
import { getAttemptEvaluation, getEvaluationDimensions, submitAttemptEvaluation } from '../../api/evaluations'
import Button from '../Button/Button'
import styles from './EvaluationForm.module.css'

// 4.04/4.04.1: every participant is offered this, passed or failed, whether
// they complete it or not - see current-feature.md, "Solicitation". Rendered
// on Result for any completed attempt, independent of the certificate flow.
function RatingScale({ dimension, value, onChange }) {
  return (
    <fieldset className={styles.dimension}>
      <legend className={styles.question}>{dimension.question}</legend>
      <div className={styles.scale}>
        <span className={styles.scaleLabel}>Not at all</span>
        {[1, 2, 3, 4, 5].map((rating) => (
          <label key={rating} className={styles.scaleOption}>
            <input
              type="radio"
              name={dimension.key}
              value={rating}
              checked={value === rating}
              onChange={() => onChange(rating)}
            />
            {rating}
          </label>
        ))}
        <span className={styles.scaleLabel}>Completely</span>
      </div>
    </fieldset>
  )
}

function SubmittedEvaluation({ dimensions, evaluation }) {
  return (
    <section className={styles.form}>
      <h2 className={styles.heading}>Your evaluation</h2>
      <p className={styles.message}>Thanks for evaluating this program.</p>
      <ul className={styles.summaryList}>
        {dimensions.map((dimension) => (
          <li key={dimension.key}>
            {dimension.question} {evaluation[dimension.key] ?? '—'}
          </li>
        ))}
      </ul>
      {evaluation.comments && <p className={styles.comments}>&ldquo;{evaluation.comments}&rdquo;</p>}
    </section>
  )
}

function EvaluationForm({ attemptId }) {
  const [state, setState] = useState({ status: 'loading', dimensions: [], evaluation: null })
  const [ratings, setRatings] = useState({})
  const [comments, setComments] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    setState({ status: 'loading', dimensions: [], evaluation: null })
    Promise.all([getEvaluationDimensions(), getAttemptEvaluation(attemptId)])
      .then(([{ dimensions }, evaluation]) => setState({ status: 'loaded', dimensions, evaluation }))
      .catch(() => setState({ status: 'error', dimensions: [], evaluation: null }))
  }, [attemptId])

  if (state.status === 'loading') return null
  if (state.status === 'error') return null

  if (state.evaluation) {
    return <SubmittedEvaluation dimensions={state.dimensions} evaluation={state.evaluation} />
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const evaluation = await submitAttemptEvaluation(attemptId, { ...ratings, comments: comments.trim() || null })
      setState((current) => ({ ...current, evaluation }))
    } catch {
      setError('Could not submit your evaluation. Please try again.')
      setSubmitting(false)
    }
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <h2 className={styles.heading}>Evaluate this program</h2>
      {state.dimensions.map((dimension) => (
        <RatingScale
          key={dimension.key}
          dimension={dimension}
          value={ratings[dimension.key]}
          onChange={(rating) => setRatings((current) => ({ ...current, [dimension.key]: rating }))}
        />
      ))}
      <label className={styles.label} htmlFor="evaluation-comments">
        Other comments
      </label>
      <textarea
        id="evaluation-comments"
        className={styles.textarea}
        value={comments}
        onChange={(event) => setComments(event.target.value)}
        disabled={submitting}
      />
      {error && <p className={styles.fieldError}>{error}</p>}
      <Button type="submit" variant="secondary" disabled={submitting}>
        {submitting ? 'Submitting…' : 'Submit evaluation'}
      </Button>
    </form>
  )
}

export default EvaluationForm
