import client from './client'

export const get = async () => {
  const res = await client.get('/recommendations')
  return res.data
}

export const refresh = async () => {
  const res = await client.post('/recommendations/refresh')
  return res.data
}

export const bookmark = async (id) => {
  const res = await client.post(`/recommendations/${id}/bookmark`)
  return res.data
}

export const unbookmark = async (id) => {
  const res = await client.delete(`/recommendations/${id}/bookmark`)
  return res.data
}
