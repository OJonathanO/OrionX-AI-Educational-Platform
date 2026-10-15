import client from './client'

export const generate = async (params) => {
  const res = await client.post('/quizzes/generate', params)
  return res.data
}

export const list = async () => {
  const res = await client.get('/quizzes')
  return res.data
}

export const get = async (id) => {
  const res = await client.get(`/quizzes/${id}`)
  return res.data
}

export const submit = async (id, answers) => {
  const res = await client.post(`/quizzes/${id}/submit`, { answers })
  return res.data
}

export const getResults = async (id) => {
  const res = await client.get(`/quizzes/${id}/results`)
  return res.data
}

export const getAttempts = async () => {
  const res = await client.get('/quizzes/attempts')
  return res.data
}
