import client from './client'

export const upload = async (file, onProgress) => {
  const formData = new FormData()
  formData.append('file', file)
  const res = await client.post('/documents', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress,
  })
  return res.data
}

export const list = async () => {
  const res = await client.get('/documents')
  return res.data
}

export const get = async (id) => {
  const res = await client.get(`/documents/${id}`)
  return res.data
}

export const getStatus = async (id) => {
  const res = await client.get(`/documents/${id}/status`)
  return res.data
}

export const preview = async (id) => {
  const res = await client.get(`/documents/${id}/preview`)
  return res.data
}

export const deleteDocument = async (id) => {
  const res = await client.delete(`/documents/${id}`)
  return res.data
}
