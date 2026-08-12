import { apiFetch } from './client'

export function getQuiz(courseSlug, attemptId) {
  const query = attemptId ? `?attempt_id=${attemptId}` : ''
  return apiFetch(`/api/v1/courses/${courseSlug}/quiz${query}`)
}
