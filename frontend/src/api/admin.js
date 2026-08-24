import { apiFetch } from './client'

const BASE_URL = import.meta.env.VITE_API_URL

// --- courses -----------------------------------------------------------------

export function getAdminCourses() {
  return apiFetch('/api/v1/admin/courses')
}

export function getAdminCourse(id) {
  return apiFetch(`/api/v1/admin/courses/${id}`)
}

export function getCourseStats(id) {
  return apiFetch(`/api/v1/admin/courses/${id}/stats`)
}

export function getCourseEvaluations(id) {
  return apiFetch(`/api/v1/admin/courses/${id}/evaluations`)
}

export function createAdminCourse(payload) {
  return apiFetch('/api/v1/admin/courses', { method: 'POST', body: JSON.stringify(payload) })
}

export function updateAdminCourse(id, payload) {
  return apiFetch(`/api/v1/admin/courses/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })
}

export function deleteAdminCourse(id) {
  return apiFetch(`/api/v1/admin/courses/${id}`, { method: 'DELETE' })
}

export function publishAdminCourse(id) {
  return apiFetch(`/api/v1/admin/courses/${id}/publish`, { method: 'POST' })
}

export function checkAdminCoursePublish(id) {
  return apiFetch(`/api/v1/admin/courses/${id}/publish?dry_run=true`, { method: 'POST' })
}

export function unpublishAdminCourse(id) {
  return apiFetch(`/api/v1/admin/courses/${id}/unpublish`, { method: 'POST' })
}

// --- learning objectives -------------------------------------------------------

export function createAdminObjective(courseId, text) {
  return apiFetch(`/api/v1/admin/courses/${courseId}/objectives`, {
    method: 'POST',
    body: JSON.stringify({ text }),
  })
}

export function updateAdminObjective(id, text) {
  return apiFetch(`/api/v1/admin/objectives/${id}`, { method: 'PATCH', body: JSON.stringify({ text }) })
}

export function deleteAdminObjective(id) {
  return apiFetch(`/api/v1/admin/objectives/${id}`, { method: 'DELETE' })
}

export function moveAdminObjective(id, direction) {
  return apiFetch(`/api/v1/admin/objectives/${id}/move`, {
    method: 'POST',
    body: JSON.stringify({ direction }),
  })
}

// --- credit ------------------------------------------------------------------

export function getAdminCourseCredit(courseId) {
  return apiFetch(`/api/v1/admin/courses/${courseId}/credit`)
}

export function recomputeAdminCourseCredit(courseId) {
  return apiFetch(`/api/v1/admin/courses/${courseId}/credit`, { method: 'POST' })
}

// --- subject matter experts -----------------------------------------------------

export function getAdminSMEs() {
  return apiFetch('/api/v1/admin/smes')
}

export function getAdminSME(id) {
  return apiFetch(`/api/v1/admin/smes/${id}`)
}

export function createAdminSME(payload) {
  return apiFetch('/api/v1/admin/smes', { method: 'POST', body: JSON.stringify(payload) })
}

export function updateAdminSME(id, payload) {
  return apiFetch(`/api/v1/admin/smes/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })
}

export function deleteAdminSME(id) {
  return apiFetch(`/api/v1/admin/smes/${id}`, { method: 'DELETE' })
}

// --- sources ---------------------------------------------------------------------

export function createAdminSource(courseId, payload) {
  return apiFetch(`/api/v1/admin/courses/${courseId}/sources`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateAdminSource(id, payload) {
  return apiFetch(`/api/v1/admin/sources/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })
}

export function deleteAdminSource(id) {
  return apiFetch(`/api/v1/admin/sources/${id}`, { method: 'DELETE' })
}

export function moveAdminSource(id, direction) {
  return apiFetch(`/api/v1/admin/sources/${id}/move`, {
    method: 'POST',
    body: JSON.stringify({ direction }),
  })
}

// --- lessons -----------------------------------------------------------------

export function getAdminLesson(id) {
  return apiFetch(`/api/v1/admin/lessons/${id}`)
}

export function createAdminLesson(courseId, payload) {
  return apiFetch(`/api/v1/admin/courses/${courseId}/lessons`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateAdminLesson(id, payload) {
  return apiFetch(`/api/v1/admin/lessons/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })
}

export function deleteAdminLesson(id) {
  return apiFetch(`/api/v1/admin/lessons/${id}`, { method: 'DELETE' })
}

export function moveAdminLesson(id, direction) {
  return apiFetch(`/api/v1/admin/lessons/${id}/move`, {
    method: 'POST',
    body: JSON.stringify({ direction }),
  })
}

// --- questions and choices -----------------------------------------------------

export function createAdminQuestion(lessonId, prompt) {
  return apiFetch(`/api/v1/admin/lessons/${lessonId}/questions`, {
    method: 'POST',
    body: JSON.stringify({ prompt }),
  })
}

export function updateAdminQuestion(id, updates) {
  return apiFetch(`/api/v1/admin/questions/${id}`, { method: 'PATCH', body: JSON.stringify(updates) })
}

export function deleteAdminQuestion(id) {
  return apiFetch(`/api/v1/admin/questions/${id}`, { method: 'DELETE' })
}

export function moveAdminQuestion(id, direction) {
  return apiFetch(`/api/v1/admin/questions/${id}/move`, {
    method: 'POST',
    body: JSON.stringify({ direction }),
  })
}

export function createAdminChoice(questionId, text) {
  return apiFetch(`/api/v1/admin/questions/${questionId}/choices`, {
    method: 'POST',
    body: JSON.stringify({ text }),
  })
}

export function updateAdminChoice(id, text) {
  return apiFetch(`/api/v1/admin/choices/${id}`, { method: 'PATCH', body: JSON.stringify({ text }) })
}

export function deleteAdminChoice(id) {
  return apiFetch(`/api/v1/admin/choices/${id}`, { method: 'DELETE' })
}

export function moveAdminChoice(id, direction) {
  return apiFetch(`/api/v1/admin/choices/${id}/move`, {
    method: 'POST',
    body: JSON.stringify({ direction }),
  })
}

export function setCorrectChoice(questionId, choiceId) {
  return apiFetch(`/api/v1/admin/questions/${questionId}/correct-choice`, {
    method: 'POST',
    body: JSON.stringify({ choice_id: choiceId }),
  })
}

// --- uploads -------------------------------------------------------------------

function uploadFile(url, file, onProgress) {
  return new Promise((resolve, reject) => {
    const formData = new FormData()
    formData.append('file', file)

    const xhr = new XMLHttpRequest()
    xhr.open('POST', url)
    xhr.withCredentials = true

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100))
      }
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText))
      } else {
        const error = new Error(`Upload failed: ${xhr.status}`)
        error.status = xhr.status
        error.body = JSON.parse(xhr.responseText || '{}')
        reject(error)
      }
    }
    xhr.onerror = () => reject(new Error('Upload failed'))
    xhr.send(formData)
  })
}

export function uploadAdminVideo(slug, file, onProgress) {
  return uploadFile(`${BASE_URL}/api/v1/admin/lessons/${slug}/video`, file, onProgress)
}

export function uploadAdminThumbnail(lessonId, file, onProgress) {
  return uploadFile(`${BASE_URL}/api/v1/admin/lessons/${lessonId}/thumbnail`, file, onProgress)
}

export function uploadAdminCourseThumbnail(courseId, file, onProgress) {
  return uploadFile(`${BASE_URL}/api/v1/admin/courses/${courseId}/thumbnail`, file, onProgress)
}

// --- policies --------------------------------------------------------------------

export function updateAdminPolicy(slug, payload) {
  return apiFetch(`/api/v1/admin/policies/${slug}`, { method: 'PATCH', body: JSON.stringify(payload) })
}

// --- currency dashboard ------------------------------------------------------------

export function getAdminCurrency() {
  return apiFetch('/api/v1/admin/currency')
}

// --- sponsor profile -----------------------------------------------------------

export function getAdminSponsor() {
  return apiFetch('/api/v1/admin/sponsor')
}

export function updateAdminSponsor(payload) {
  return apiFetch('/api/v1/admin/sponsor', { method: 'PATCH', body: JSON.stringify(payload) })
}

// --- completions -----------------------------------------------------------------

function completionsQuery(filters = {}) {
  const params = new URLSearchParams()
  if (filters.courseId) params.set('course_id', filters.courseId)
  if (filters.startDate) params.set('start_date', filters.startDate)
  if (filters.endDate) params.set('end_date', filters.endDate)
  if (filters.passed !== undefined && filters.passed !== '') params.set('passed', filters.passed)
  const query = params.toString()
  return query ? `?${query}` : ''
}

export function getAdminCompletions(filters) {
  return apiFetch(`/api/v1/admin/completions${completionsQuery(filters)}`)
}

export function adminCompletionsCsvUrl(filters) {
  return `${BASE_URL}/api/v1/admin/completions.csv${completionsQuery(filters)}`
}
