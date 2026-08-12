import { useEffect, useState } from 'react'
import { getCourses } from '../../api/courses'
import CourseCard from '../../components/CourseCard/CourseCard'
import styles from './CourseList.module.css'

function CourseList() {
  const [state, setState] = useState({ status: 'loading', courses: [] })

  useEffect(() => {
    getCourses()
      .then((courses) => setState({ status: 'loaded', courses }))
      .catch(() => setState({ status: 'error', courses: [] }))
  }, [])

  if (state.status === 'loading') {
    return <p className={styles.message}>Loading courses&hellip;</p>
  }

  if (state.status === 'error') {
    return <p className={styles.message}>Couldn&apos;t load courses. Please try again later.</p>
  }

  if (state.courses.length === 0) {
    return <p className={styles.message}>No courses yet. Check back soon.</p>
  }

  return (
    <div className={styles.grid}>
      {state.courses.map((course) => (
        <CourseCard key={course.id} course={course} />
      ))}
    </div>
  )
}

export default CourseList
