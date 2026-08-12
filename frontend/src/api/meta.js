import { apiFetch } from './client'

export function getFieldsOfStudy() {
  return apiFetch('/api/v1/meta/fields-of-study')
}

export function getProgramLevels() {
  return apiFetch('/api/v1/meta/program-levels')
}
