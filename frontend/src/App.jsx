import { Link, Route, Routes } from 'react-router-dom'
import Header from './components/Header/Header'
import CourseList from './pages/CourseList/CourseList'
import CourseDetail from './pages/CourseDetail/CourseDetail'
import LessonSegment from './pages/LessonSegment/LessonSegment'
import Quiz from './pages/Quiz/Quiz'
import Result from './pages/Result/Result'
import Verify from './pages/Verify/Verify'
import Login from './pages/Login/Login'
import Register from './pages/Register/Register'
import Progress from './pages/Progress/Progress'
import AdminGuard from './pages/Admin/AdminGuard'
import AdminCourseList from './pages/Admin/AdminCourseList/AdminCourseList'
import AdminCourseEditor from './pages/Admin/AdminCourseEditor/AdminCourseEditor'
import AdminLessonEditor from './pages/Admin/AdminLessonEditor/AdminLessonEditor'
import AdminSMEList from './pages/Admin/AdminSMEList/AdminSMEList'
import AdminSponsorSettings from './pages/Admin/AdminSponsorSettings/AdminSponsorSettings'
import AdminCompletions from './pages/Admin/AdminCompletions/AdminCompletions'
import Stats from './pages/Admin/Stats/Stats'
import Evaluations from './pages/Admin/Evaluations/Evaluations'
import styles from './App.module.css'

function NotFound() {
  return (
    <div className={styles.notFound}>
      <p>Page not found.</p>
      <Link to="/">Back home</Link>
    </div>
  )
}

function App() {
  return (
    <div className={styles.app}>
      <Header />
      <main className={styles.main}>
        <Routes>
          <Route path="/" element={<CourseList />} />
          <Route path="/courses/:slug" element={<CourseDetail />} />
          <Route path="/courses/:slug/lessons/:lessonSlug" element={<LessonSegment />} />
          <Route path="/courses/:slug/quiz" element={<Quiz />} />
          <Route path="/attempts/:attemptId" element={<Result />} />
          <Route path="/verify/:code" element={<Verify />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/me" element={<Progress />} />
          <Route
            path="/admin"
            element={
              <AdminGuard>
                <AdminCourseList />
              </AdminGuard>
            }
          />
          <Route
            path="/admin/courses/:id"
            element={
              <AdminGuard>
                <AdminCourseEditor />
              </AdminGuard>
            }
          />
          <Route
            path="/admin/courses/:id/stats"
            element={
              <AdminGuard>
                <Stats />
              </AdminGuard>
            }
          />
          <Route
            path="/admin/courses/:id/evaluations"
            element={
              <AdminGuard>
                <Evaluations />
              </AdminGuard>
            }
          />
          <Route
            path="/admin/lessons/:id"
            element={
              <AdminGuard>
                <AdminLessonEditor />
              </AdminGuard>
            }
          />
          <Route
            path="/admin/smes"
            element={
              <AdminGuard>
                <AdminSMEList />
              </AdminGuard>
            }
          />
          <Route
            path="/admin/sponsor"
            element={
              <AdminGuard>
                <AdminSponsorSettings />
              </AdminGuard>
            }
          />
          <Route
            path="/admin/completions"
            element={
              <AdminGuard>
                <AdminCompletions />
              </AdminGuard>
            }
          />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
