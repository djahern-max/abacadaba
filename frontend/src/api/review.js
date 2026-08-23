import { apiFetch } from './client'

export function getReviewQuestions(courseSlug, lessonSlug) {
  return apiFetch(`/api/v1/courses/${courseSlug}/lessons/${lessonSlug}/review`)
}

export function submitReviewAnswer(courseSlug, lessonSlug, questionId, choiceId) {
  return apiFetch(`/api/v1/courses/${courseSlug}/lessons/${lessonSlug}/review/${questionId}`, {
    method: 'POST',
    body: JSON.stringify({ choice_id: choiceId }),
  })
}
