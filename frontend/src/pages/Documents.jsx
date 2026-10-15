import React, { useState, useEffect, useCallback, useRef } from 'react'
import {
  FileText,
  Upload,
  Trash2,
  Eye,
  Search,
  Filter,
  X,
  RefreshCw,
  FileIcon,
  AlertCircle,
  CheckCircle,
  Clock,
  XCircle,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'
import EmptyState from '../components/EmptyState'
import { list, upload, preview, deleteDocument, getStatus } from '../api/documents'

const ITEMS_PER_PAGE = 10

const STATUS_CONFIG = {
  pending: { color: 'bg-yellow-100 text-yellow-800', icon: Clock, label: 'Pending' },
  processing: { color: 'bg-blue-100 text-blue-800', icon: RefreshCw, label: 'Processing' },
  completed: { color: 'bg-green-100 text-green-800', icon: CheckCircle, label: 'Completed' },
  failed: { color: 'bg-red-100 text-red-800', icon: XCircle, label: 'Failed' },
}

const FILE_TYPES = ['pdf', 'doc', 'docx', 'txt']

export default function Documents() {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [search, setSearch] = useState('')
  const [filterType, setFilterType] = useState('')
  const [filterSubject, setFilterSubject] = useState('')
  const [previewDoc, setPreviewDoc] = useState(null)
  const [previewContent, setPreviewContent] = useState('')
  const [previewLoading, setPreviewLoading] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef(null)

  const fetchDocuments = useCallback(async () => {
    setLoading(true)
    try {
      const data = await list()
      setDocuments(data || [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load documents')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDocuments()
  }, [fetchDocuments])

  // Poll for status of processing documents
  useEffect(() => {
    const processingDocs = documents.filter((d) => d.status === 'processing' || d.status === 'pending')
    if (processingDocs.length === 0) return

    const interval = setInterval(async () => {
      try {
        const updatedDocs = await Promise.all(
          processingDocs.map(async (doc) => {
            try {
              const statusData = await getStatus(doc.id)
              return { ...doc, status: statusData.status || statusData }
            } catch {
              return doc
            }
          })
        )
        setDocuments((prev) =>
          prev.map((doc) => {
            const updated = updatedDocs.find((d) => d.id === doc.id)
            return updated || doc
          })
        )
      } catch {
        // Ignore polling errors
      }
    }, 3000)

    return () => clearInterval(interval)
  }, [documents])

  const handleUpload = async (file) => {
    if (!file) return
    setUploading(true)
    setUploadProgress(0)
    setError('')
    try {
      await upload(file, (progressEvent) => {
        const percent = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1))
        setUploadProgress(percent)
      })
      await fetchDocuments()
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0]
    if (file) handleUpload(file)
    e.target.value = ''
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (file) handleUpload(file)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = () => {
    setDragOver(false)
  }

  const handlePreview = async (doc) => {
    setPreviewDoc(doc)
    setPreviewLoading(true)
    setPreviewContent('')
    try {
      const data = await preview(doc.id)
      setPreviewContent(data?.content || data?.text || data?.extracted_text || 'No preview available')
    } catch (err) {
      setPreviewContent('Failed to load preview. The document may still be processing.')
    } finally {
      setPreviewLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!deleteConfirm) return
    try {
      await deleteDocument(deleteConfirm.id)
      setDocuments((prev) => prev.filter((d) => d.id !== deleteConfirm.id))
      setDeleteConfirm(null)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete document')
      setDeleteConfirm(null)
    }
  }

  const handleRetry = async (doc) => {
    setError('')
    try {
      // Re-upload by fetching the file and re-uploading
      // Since we don't have the original file, we'll just refresh status
      const statusData = await getStatus(doc.id)
      setDocuments((prev) =>
        prev.map((d) => (d.id === doc.id ? { ...d, status: statusData.status || 'pending' } : d))
      )
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to retry processing')
    }
  }

  // Filter and search
  const filteredDocs = documents.filter((doc) => {
    const matchesSearch = !search || doc.filename?.toLowerCase().includes(search.toLowerCase()) || doc.title?.toLowerCase().includes(search.toLowerCase())
    const matchesType = !filterType || doc.file_type?.toLowerCase() === filterType
    const matchesSubject = !filterSubject || doc.subject?.toLowerCase() === filterSubject.toLowerCase()
    return matchesSearch && matchesType && matchesSubject
  })

  // Pagination
  const totalPages = Math.ceil(filteredDocs.length / ITEMS_PER_PAGE)
  const paginatedDocs = filteredDocs.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE)

  // Get unique subjects for filter
  const subjects = [...new Set(documents.map((d) => d.subject).filter(Boolean))]

  const getFileTypeBadge = (type) => {
    const ext = type?.toLowerCase() || ''
    if (ext === 'pdf') return 'bg-red-100 text-red-700'
    if (ext === 'doc' || ext === 'docx') return 'bg-blue-100 text-blue-700'
    if (ext === 'txt') return 'bg-gray-100 text-gray-700'
    return 'bg-gray-100 text-gray-700'
  }

  if (loading) return <LoadingSpinner size="lg" />

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Materials</h1>
          <p className="text-gray-600 mt-1">Upload and manage your study documents</p>
        </div>
      </div>

      <ErrorAlert message={error} onDismiss={() => setError('')} />

      {/* Upload Area */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
          dragOver ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-primary-400'
        }`}
      >
        <Upload className="h-10 w-10 text-gray-400 mx-auto mb-3" />
        <p className="text-gray-700 font-medium mb-1">
          {uploading ? `Uploading... ${uploadProgress}%` : 'Drag and drop your files here'}
        </p>
        <p className="text-sm text-gray-500 mb-4">Supports PDF, DOC, DOCX, TXT</p>
        {uploading && (
          <div className="max-w-xs mx-auto mb-4">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}
        <label className="btn-primary cursor-pointer inline-flex items-center gap-2">
          <Upload className="h-4 w-4" />
          {uploading ? 'Uploading...' : 'Choose File'}
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            onChange={handleFileSelect}
            accept=".pdf,.doc,.docx,.txt"
            disabled={uploading}
          />
        </label>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setCurrentPage(1) }}
            placeholder="Search documents..."
            className="input pl-10"
          />
        </div>
        <select
          value={filterType}
          onChange={(e) => { setFilterType(e.target.value); setCurrentPage(1) }}
          className="input sm:w-40"
        >
          <option value="">All Types</option>
          {FILE_TYPES.map((type) => (
            <option key={type} value={type}>{type.toUpperCase()}</option>
          ))}
        </select>
        <select
          value={filterSubject}
          onChange={(e) => { setFilterSubject(e.target.value); setCurrentPage(1) }}
          className="input sm:w-40"
        >
          <option value="">All Subjects</option>
          {subjects.map((subject) => (
            <option key={subject} value={subject}>{subject}</option>
          ))}
        </select>
      </div>

      {/* Document List */}
      {documents.length === 0 ? (
        <div className="card">
          <EmptyState
            icon={FileText}
            title="No documents yet"
            description="Upload your study materials to get started with AI-powered learning."
          />
        </div>
      ) : filteredDocs.length === 0 ? (
        <div className="card">
          <EmptyState
            icon={Search}
            title="No matching documents"
            description="Try adjusting your search or filters."
          />
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Title</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 hidden sm:table-cell">Type</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 hidden md:table-cell">Subject</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Status</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 hidden lg:table-cell">Date</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody>
                {paginatedDocs.map((doc) => {
                  const statusConfig = STATUS_CONFIG[doc.status] || STATUS_CONFIG.pending
                  const StatusIcon = statusConfig.icon
                  return (
                    <tr key={doc.id} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-3">
                          <FileText className="h-5 w-5 text-gray-400 flex-shrink-0" />
                          <span className="text-sm font-medium text-gray-900 truncate max-w-[200px]">
                            {doc.filename || doc.title || 'Untitled'}
                          </span>
                        </div>
                      </td>
                      <td className="py-3 px-4 hidden sm:table-cell">
                        <span className={`inline-block px-2 py-0.5 text-xs font-medium rounded ${getFileTypeBadge(doc.file_type)}`}>
                          {(doc.file_type || 'file').toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600 hidden md:table-cell">{doc.subject || '—'}</td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full ${statusConfig.color}`}>
                          <StatusIcon className="h-3 w-3" />
                          {statusConfig.label}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-500 hidden lg:table-cell">
                        {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : '—'}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => handlePreview(doc)}
                            className="p-1.5 text-gray-400 hover:text-primary-600 transition-colors"
                            title="Preview"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          {doc.status === 'failed' && (
                            <button
                              onClick={() => handleRetry(doc)}
                              className="p-1.5 text-gray-400 hover:text-yellow-600 transition-colors"
                              title="Retry"
                            >
                              <RefreshCw className="h-4 w-4" />
                            </button>
                          )}
                          <button
                            onClick={() => setDeleteConfirm(doc)}
                            className="p-1.5 text-gray-400 hover:text-red-600 transition-colors"
                            title="Delete"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
              <p className="text-sm text-gray-600">
                Showing {(currentPage - 1) * ITEMS_PER_PAGE + 1}–{Math.min(currentPage * ITEMS_PER_PAGE, filteredDocs.length)} of {filteredDocs.length}
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="p-1.5 rounded border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <span className="text-sm text-gray-600">{currentPage} / {totalPages}</span>
                <button
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="p-1.5 rounded border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Preview Modal */}
      {previewDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h3 className="font-semibold text-gray-900 truncate">{previewDoc.filename || previewDoc.title}</h3>
              <button onClick={() => setPreviewDoc(null)} className="p-1 text-gray-400 hover:text-gray-600">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {previewLoading ? (
                <LoadingSpinner />
              ) : (
                <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans">{previewContent}</pre>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="h-10 w-10 rounded-full bg-red-100 flex items-center justify-center">
                <AlertCircle className="h-5 w-5 text-red-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Delete Document</h3>
            </div>
            <p className="text-sm text-gray-600 mb-6">
              Are you sure you want to delete <strong>{deleteConfirm.filename || deleteConfirm.title}</strong>? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setDeleteConfirm(null)} className="btn-secondary">
                Cancel
              </button>
              <button onClick={handleDelete} className="btn-primary bg-red-600 hover:bg-red-700">
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
