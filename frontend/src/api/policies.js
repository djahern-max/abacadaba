import { apiFetch } from './client'

export function getPolicies() {
  return apiFetch('/api/v1/policies')
}

export function getPolicy(slug) {
  return apiFetch(`/api/v1/policies/${slug}`)
}
