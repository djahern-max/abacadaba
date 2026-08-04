import { apiFetch } from './client'

export function getQuiz(slug) {
  return apiFetch(`/api/v1/lessons/${slug}/quiz`)
}

export function submitAnswer(slug, questionId, choiceId) {
  return apiFetch(`/api/v1/lessons/${slug}/quiz/answers`, {
    method: 'POST',
    body: JSON.stringify({ question_id: questionId, choice_id: choiceId }),
  })
}
