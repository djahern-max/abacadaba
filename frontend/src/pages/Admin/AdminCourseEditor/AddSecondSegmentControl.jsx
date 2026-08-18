import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createAdminLesson } from '../../../api/admin'
import Button from '../../../components/Button/Button'
import styles from '../AdminLessonEditor/AdminLessonEditor.module.css'

function AddSecondSegmentControl({ course }) {
  const navigate = useNavigate()
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')

  async function handleClick() {
    setError('')
    setCreating(true)
    try {
      const lesson = await createAdminLesson(course.id, { title: 'Untitled segment' })
      navigate(`/admin/lessons/${lesson.id}`)
    } catch {
      setError('Could not add a second segment.')
      setCreating(false)
    }
  }

  return (
    <section className={styles.section}>
      <Button variant="secondary" onClick={handleClick} disabled={creating}>
        {creating
          ? 'Adding…'
          : 'Add a second segment — this course will split into a course page and a page for each segment.'}
      </Button>
      {error && <p className={styles.fieldError}>{error}</p>}
    </section>
  )
}

export default AddSecondSegmentControl
