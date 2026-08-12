import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getCourseStats } from '../../../api/admin'
import styles from './Stats.module.css'

const BAD_QUESTION_THRESHOLD = 40

function percent(ratio) {
  return ratio === null ? '—' : `${Math.round(ratio * 100)}%`
}

function SummaryRow({ summary }) {
  return (
    <section className={styles.summaryRow}>
      <div className={styles.stat}>
        <span className={styles.statValue}>{summary.attempts_started}</span>
        <span className={styles.statLabel}>Attempts started</span>
      </div>
      <div className={styles.stat}>
        <span className={styles.statValue}>{percent(summary.completion_rate)}</span>
        <span className={styles.statLabel}>Completion rate</span>
      </div>
      <div className={styles.stat}>
        <span className={styles.statValue}>{percent(summary.pass_rate)}</span>
        <span className={styles.statLabel}>Pass rate</span>
      </div>
      <div className={styles.stat}>
        <span className={styles.statValue}>
          {summary.mean_score === null ? '—' : summary.mean_score.toFixed(1)}
        </span>
        <span className={styles.statLabel}>Mean score</span>
      </div>
    </section>
  )
}

function ChoiceDistribution({ choices }) {
  return (
    <details>
      <summary>Choice distribution</summary>
      <ul className={styles.choiceList}>
        {choices.map((choice) => (
          <li key={choice.choice_id} className={choice.is_correct ? styles.correctChoice : undefined}>
            {choice.text}: {choice.picked_count}
            {choice.is_correct && ' (correct)'}
          </li>
        ))}
      </ul>
    </details>
  )
}

function QuestionRow({ question, choices }) {
  const flagged = question.pct_correct !== null && question.pct_correct < BAD_QUESTION_THRESHOLD
  return (
    <tr className={flagged ? styles.flaggedRow : undefined}>
      <td>{question.lesson_title}</td>
      <td>{question.position}</td>
      <td>{question.prompt}</td>
      <td>{question.answered}</td>
      <td>
        {question.pct_correct === null ? '—' : `${Math.round(question.pct_correct)}%`}
        {flagged && <span className={styles.badge}>Likely a bad question</span>}
      </td>
      <td>
        <ChoiceDistribution choices={choices} />
      </td>
    </tr>
  )
}

function Stats() {
  const { id } = useParams()
  const [state, setState] = useState({ status: 'loading', data: null })

  useEffect(() => {
    setState({ status: 'loading', data: null })
    getCourseStats(id)
      .then((data) => setState({ status: 'loaded', data }))
      .catch(() => setState({ status: 'error', data: null }))
  }, [id])

  if (state.status === 'loading') {
    return <p className={styles.message}>Loading&hellip;</p>
  }
  if (state.status === 'error') {
    return <p className={styles.message}>Couldn&apos;t load stats for this course.</p>
  }

  const { data } = state
  const { course_stats: summary, question_stats: questions, choice_distribution: distribution, dropoff } = data
  const choicesByQuestionId = Object.fromEntries(distribution.map((row) => [row.question_id, row.choices]))

  return (
    <div className={styles.page}>
      <Link to={`/admin/courses/${id}`} className={styles.back}>
        &larr; Back to course
      </Link>
      <h1 className={styles.heading}>Stats</h1>

      {summary.attempts_started === 0 ? (
        <p className={styles.message}>No attempts yet. Stats will appear once someone takes the assessment.</p>
      ) : (
        <>
          <SummaryRow summary={summary} />

          <section className={styles.section}>
            <h2 className={styles.sectionHeading}>Questions, worst first</h2>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Segment</th>
                  <th>#</th>
                  <th>Prompt</th>
                  <th>Answered</th>
                  <th>% correct</th>
                  <th>Choices</th>
                </tr>
              </thead>
              <tbody>
                {questions.map((question) => (
                  <QuestionRow
                    key={question.question_id}
                    question={question}
                    choices={choicesByQuestionId[question.question_id] ?? []}
                  />
                ))}
              </tbody>
            </table>
          </section>

          <section className={styles.section}>
            <h2 className={styles.sectionHeading}>Drop-off by question</h2>
            <ul className={styles.dropoffList}>
              {dropoff.map((point) => (
                <li key={point.question_id}>
                  {point.lesson_title}, question {point.position}: {point.attempts_reached} attempt(s) reached it
                </li>
              ))}
            </ul>
          </section>
        </>
      )}
    </div>
  )
}

export default Stats
