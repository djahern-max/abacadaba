import { Link, Route, Routes } from 'react-router-dom'
import Header from './components/Header/Header'
import LessonList from './pages/LessonList/LessonList'
import LessonDetail from './pages/LessonDetail/LessonDetail'
import Quiz from './pages/Quiz/Quiz'
import Result from './pages/Result/Result'
import Verify from './pages/Verify/Verify'
import Login from './pages/Login/Login'
import Register from './pages/Register/Register'
import Progress from './pages/Progress/Progress'
import AdminGuard from './pages/Admin/AdminGuard'
import AdminLessonList from './pages/Admin/AdminLessonList/AdminLessonList'
import AdminLessonEditor from './pages/Admin/AdminLessonEditor/AdminLessonEditor'
import Stats from './pages/Admin/Stats/Stats'
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
          <Route path="/" element={<LessonList />} />
          <Route path="/lessons/:slug" element={<LessonDetail />} />
          <Route path="/lessons/:slug/quiz" element={<Quiz />} />
          <Route path="/attempts/:attemptId" element={<Result />} />
          <Route path="/verify/:code" element={<Verify />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/me" element={<Progress />} />
          <Route
            path="/admin"
            element={
              <AdminGuard>
                <AdminLessonList />
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
            path="/admin/lessons/:id/stats"
            element={
              <AdminGuard>
                <Stats />
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
