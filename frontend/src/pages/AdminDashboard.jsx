import React, { useState, useEffect, useCallback } from 'react'
import {
  Users,
  FileText,
  MessageSquare,
  BarChart3,
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
  Server,
  Database,
  Shield,
  Search,
} from 'lucide-react'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'
import { overview } from '../api/analytics'
import client from '../api/client'

export default function AdminDashboard() {
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [documents, setDocuments] = useState([])
  const [errors, setErrors] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [userSearch, setUserSearch] = useState('')
  const [refreshing, setRefreshing] = useState(false)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [overviewData, usersData, docsData] = await Promise.all([
        overview(),
        client.get('/admin/users').then((r) => r.data).catch(() => []),
        client.get('/admin/documents').then((r) => r.data).catch(() => []),
      ])
      setStats(overviewData)
      setUsers(usersData || [])
      setDocuments(docsData || [])

      // Fetch recent errors
      try {
        const errorsData = await client.get('/admin/errors').then((r) => r.data)
        setErrors(errorsData || [])
      } catch {
        setErrors([])
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load admin dashboard')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleRefresh = async () => {
    setRefreshing(true)
    await fetchData()
    setRefreshing(false)
  }

  const handleToggleUserStatus = async (userId, currentStatus) => {
    try {
      const newStatus = currentStatus === 'active' ? 'inactive' : 'active'
      await client.patch(`/admin/users/${userId}`, { status: newStatus })
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, status: newStatus } : u))
      )
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update user status')
    }
  }

  if (loading) return <LoadingSpinner size="lg" />

  const statCards = [
    { label: 'Total Users', value: stats?.total_users || users.length, icon: Users, color: 'text-blue-600 bg-blue-50' },
    { label: 'Total Documents', value: stats?.total_documents || documents.length, icon: FileText, color: 'text-green-600 bg-green-50' },
    { label: 'Active Today', value: stats?.active_today || 0, icon: Activity, color: 'text-purple-600 bg-purple-50' },
    { label: 'Failed Processing', value: stats?.failed_processing || 0, icon: AlertTriangle, color: 'text-red-600 bg-red-50' },
  ]

  const systemHealth = [
    { name: 'API Server', status: 'operational', icon: Server },
    { name: 'Database', status: 'operational', icon: Database },
    { name: 'Auth Service', status: 'operational', icon: Shield },
  ]

  const filteredUsers = users.filter(
    (u) =>
      !userSearch ||
      u.full_name?.toLowerCase().includes(userSearch.toLowerCase()) ||
      u.email?.toLowerCase().includes(userSearch.toLowerCase())
  )

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-gray-600 mt-1">Platform overview and management</p>
        </div>
        <button onClick={handleRefresh} className="btn-secondary flex items-center gap-2" disabled={refreshing}>
          <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <ErrorAlert message={error} onDismiss={() => setError('')} />

      {/* Platform Overview Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="card">
            <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${color} mb-3`}>
              <Icon className="h-5 w-5" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            <p className="text-sm text-gray-600">{label}</p>
          </div>
        ))}
      </div>

      {/* System Health */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Activity className="h-5 w-5 text-primary-600" />
          System Health
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {systemHealth.map(({ name, status, icon: Icon }) => (
            <div key={name} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <Icon className="h-5 w-5 text-gray-600" />
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{name}</p>
                <p className="text-xs text-gray-500 capitalize">{status}</p>
              </div>
              <div className="h-2.5 w-2.5 rounded-full bg-green-500" />
            </div>
          ))}
        </div>
      </div>

      {/* User Management */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Users className="h-5 w-5 text-primary-600" />
            User Management
          </h2>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              value={userSearch}
              onChange={(e) => setUserSearch(e.target.value)}
              placeholder="Search users..."
              className="input pl-9 py-1.5 text-sm w-48"
            />
          </div>
        </div>
        {filteredUsers.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-8">No users found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Name</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 hidden sm:table-cell">Email</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Role</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Status</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 hidden md:table-cell">Docs</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map((user) => (
                  <tr key={user.id} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
                          <span className="text-xs font-medium text-primary-700">
                            {user.full_name?.charAt(0) || user.email?.charAt(0) || 'U'}
                          </span>
                        </div>
                        <span className="text-sm font-medium text-gray-900">{user.full_name || 'N/A'}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600 hidden sm:table-cell">{user.email}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 text-xs font-medium rounded-full capitalize ${
                        user.role === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-700'
                      }`}>
                        {user.role || 'student'}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full ${
                        user.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                      }`}>
                        {user.status === 'active' ? (
                          <CheckCircle className="h-3 w-3" />
                        ) : (
                          <XCircle className="h-3 w-3" />
                        )}
                        {user.status || 'active'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600 hidden md:table-cell">{user.document_count || 0}</td>
                    <td className="py-3 px-4">
                      <div className="flex justify-end">
                        <button
                          onClick={() => handleToggleUserStatus(user.id, user.status)}
                          className={`text-xs font-medium px-3 py-1 rounded-full transition-colors ${
                            user.status === 'active'
                              ? 'bg-red-50 text-red-600 hover:bg-red-100'
                              : 'bg-green-50 text-green-600 hover:bg-green-100'
                          }`}
                        >
                          {user.status === 'active' ? 'Deactivate' : 'Activate'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Document Processing Jobs */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <FileText className="h-5 w-5 text-primary-600" />
          Document Processing
        </h2>
        {documents.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-8">No documents to display.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Title</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 hidden sm:table-cell">Owner</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Status</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 hidden md:table-cell">Error</th>
                </tr>
              </thead>
              <tbody>
                {documents.slice(0, 10).map((doc) => (
                  <tr key={doc.id} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
                    <td className="py-3 px-4 text-sm font-medium text-gray-900">
                      {doc.filename || doc.title || 'Untitled'}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600 hidden sm:table-cell">
                      {doc.owner_name || doc.owner_email || 'N/A'}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full ${
                        doc.status === 'completed' ? 'bg-green-100 text-green-700' :
                        doc.status === 'processing' ? 'bg-blue-100 text-blue-700' :
                        doc.status === 'failed' ? 'bg-red-100 text-red-700' :
                        'bg-yellow-100 text-yellow-700'
                      }`}>
                        {doc.status === 'completed' && <CheckCircle className="h-3 w-3" />}
                        {doc.status === 'processing' && <Clock className="h-3 w-3" />}
                        {doc.status === 'failed' && <XCircle className="h-3 w-3" />}
                        {doc.status || 'pending'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm text-red-600 hidden md:table-cell">
                      {doc.error || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recent Errors */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-red-500" />
          Recent Errors
        </h2>
        {errors.length === 0 ? (
          <div className="flex items-center gap-2 p-4 bg-green-50 rounded-lg">
            <CheckCircle className="h-5 w-5 text-green-600" />
            <p className="text-sm text-green-700">No recent errors. System is running smoothly.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {errors.slice(0, 5).map((err, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-red-50 border border-red-100 rounded-lg">
                <XCircle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-red-800">{err.message || err.error || 'Unknown error'}</p>
                  <p className="text-xs text-red-500 mt-0.5">
                    {err.endpoint || 'N/A'} — {err.created_at ? new Date(err.created_at).toLocaleString() : 'N/A'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
