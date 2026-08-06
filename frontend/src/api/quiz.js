import { apiFetch } from './client'

export function getQuiz(slug, attemptId) {
  const query = attemptId ? `?attempt_id=${attemptId}` : ''
  return apiFetch(`/api/v1/lessons/${slug}/quiz${query}`)
}
