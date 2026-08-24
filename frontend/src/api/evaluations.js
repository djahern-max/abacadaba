import { apiFetch } from './client'

export function getEvaluationDimensions() {
  return apiFetch('/api/v1/meta/evaluation-dimensions')
}

export function getAttemptEvaluation(attemptId) {
  return apiFetch(`/api/v1/attempts/${attemptId}/evaluation`)
}

export function submitAttemptEvaluation(attemptId, payload) {
  return apiFetch(`/api/v1/attempts/${attemptId}/evaluation`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
