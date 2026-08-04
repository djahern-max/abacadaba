import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getQuiz } from '../../api/quiz'
import QuestionCard from '../../components/QuestionCard/QuestionCard'
import styles from './Quiz.module.css'

function Quiz() {
  const { slug } = useParams()
  const [state, setState] = useState({ status: 'loading', quiz: null })

  useEffect(() => {
    setState({ status: 'loading', quiz: null })
    getQuiz(slug)
      .then((quiz) => setState({ status: 'loaded', quiz }))
      .catch((error) => {
        setState({ status: error.status === 404 ? 'not-found' : 'error', quiz: null })
      })
  }, [slug])

  if (state.status === 'loading') {
    return <p className={styles.message}>Loading quiz&hellip;</p>
  }

  if (state.status === 'not-found') {
    return (
      <div className={styles.message}>
        <p>This lesson doesn&apos;t have a quiz yet.</p>
        <Link to={`/lessons/${slug}`}>Back to lesson</Link>
      </div>
    )
  }

  if (state.status === 'error') {
    return <p className={styles.message}>Couldn&apos;t load this quiz. Please try again later.</p>
  }

  const { quiz } = state

  return (
    <div className={styles.quiz}>
      <Link to={`/lessons/${slug}`} className={styles.back}>
        &larr; Back to lesson
      </Link>
      <h1 className={styles.title}>{quiz.lesson_title}</h1>
      <span className={styles.count}>{quiz.question_count} questions</span>
      <p className={styles.note}>Answering your questions is coming soon &mdash; for now, take a look.</p>
      <div className={styles.questions}>
        {quiz.questions.map((question) => (
          <QuestionCard key={question.id} question={question} />
        ))}
      </div>
    </div>
  )
}

export default Quiz
