import { apiFetch } from './client'

export function startAttempt(slug) {
  return apiFetch(`/api/v1/lessons/${slug}/attempts`, { method: 'POST' })
}

export function submitAttemptAnswer(attemptId, questionId, choiceId) {
  return apiFetch(`/api/v1/attempts/${attemptId}/answers`, {
    method: 'POST',
    body: JSON.stringify({ question_id: questionId, choice_id: choiceId }),
  })
}

export function getAttemptResult(attemptId) {
  return apiFetch(`/api/v1/attempts/${attemptId}/result`)
}
