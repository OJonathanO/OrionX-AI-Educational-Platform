import React, { useState, useEffect } from 'react'
import {
  User,
  Mail,
  Save,
  Shield,
  Download,
  Trash2,
  AlertCircle,
  CheckCircle,
  X,
  Plus,
  XIcon,
  BookOpen,
  Target,
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import ErrorAlert from '../components/ErrorAlert'
import { updateMe, getPreferences, updatePreferences } from '../api/auth'

const ANSWER_STYLES = [
  { value: 'beginner', label: 'Beginner' },
  { value: 'concise', label: 'Concise' },
  { value: 'detailed', label: 'Detailed' },
  { value: 'exam_prep', label: 'Exam Prep' },
  { value: 'step_by_step', label: 'Step-by-Step' },
]

const SUBJECT_OPTIONS = [
  'Mathematics', 'Physics', 'Chemistry', 'Biology', 'History',
  'Literature', 'Computer Science', 'Economics', 'Psychology', 'Philosophy',
]

export default function Profile() {
  const { user, updateUser } = useAuth()
  const [fullName, setFullName] = useState(user?.full_name || '')
  const [email, setEmail] = useState(user?.email || '')
  const [answerStyle, setAnswerStyle] = useState('detailed')
  const [preferredSubjects, setPreferredSubjects] = useState([])
  const [newSubject, setNewSubject] = useState('')
  const [learningGoals, setLearningGoals] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [savingProfile, setSavingProfile] = useState(false)
  const [savingPrefs, setSavingPrefs] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    const fetchPreferences = async () => {
      try {
        const prefs = await getPreferences()
        if (prefs) {
          setAnswerStyle(prefs.default_answer_style || 'detailed')
          setPreferredSubjects(prefs.preferred_subjects || [])
          setLearningGoals(prefs.learning_goals || '')
        }
      } catch (err) {
        // Preferences are optional, fail silently
      }
    }
    fetchPreferences()
  }, [])

  const handleSaveProfile = async (e) => {
    e.preventDefault()
    setSavingProfile(true)
    setError('')
    setSuccess('')
    try {
      const updated = await updateMe({ full_name: fullName, email })
      updateUser(updated)
      setSuccess('Profile updated successfully')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update profile')
    } finally {
      setSavingProfile(false)
    }
  }

  const handleSavePreferences = async (e) => {
    e.preventDefault()
    setSavingPrefs(true)
    setError('')
    setSuccess('')
    try {
      await updatePreferences({
        default_answer_style: answerStyle,
        preferred_subjects: preferredSubjects,
        learning_goals: learningGoals,
      })
      setSuccess('Preferences saved successfully')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save preferences')
    } finally {
      setSavingPrefs(false)
    }
  }

  const handleAddSubject = () => {
    const subject = newSubject.trim()
    if (subject && !preferredSubjects.includes(subject)) {
      setPreferredSubjects((prev) => [...prev, subject])
      setNewSubject('')
    }
  }

  const handleRemoveSubject = (subject) => {
    setPreferredSubjects((prev) => prev.filter((s) => s !== subject))
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleAddSubject()
    }
  }

  const handleDownloadData = () => {
    // In a real app, this would call an API endpoint
    // For now, we'll create a simple JSON download
    const data = {
      profile: { full_name: fullName, email },
      preferences: { answerStyle, preferredSubjects, learningGoals },
      exported_at: new Date().toISOString(),
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'my-data.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleDeleteAccount = async () => {
    setDeleting(true)
    try {
      // In a real app, this would call a delete API endpoint
      // For now, just clear local state
      localStorage.removeItem('token')
      window.location.href = '/login'
    } catch (err) {
      setError('Failed to delete account. Please try again.')
      setDeleting(false)
      setShowDeleteConfirm(false)
    }
  }

  const memberSince = user?.created_at
    ? new Date(user.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
    : 'N/A'

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Profile & Settings</h1>

      <ErrorAlert message={error} onDismiss={() => setError('')} />
      {success && (
        <div className="flex items-center gap-2 p-4 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
          <CheckCircle className="h-4 w-4" />
          {success}
        </div>
      )}

      {/* Profile Section */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Account Information</h2>
        <form onSubmit={handleSaveProfile} className="space-y-4">
          <div>
            <label className="label">Full Name</label>
            <div className="relative">
              <User className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="input pl-10"
              />
            </div>
          </div>
          <div>
            <label className="label">Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input pl-10"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Role</label>
              <p className="input bg-gray-50 text-gray-600 capitalize">{user?.role || 'Student'}</p>
            </div>
            <div>
              <label className="label">Member Since</label>
              <p className="input bg-gray-50 text-gray-600">{memberSince}</p>
            </div>
          </div>
          <button type="submit" className="btn-primary flex items-center gap-2" disabled={savingProfile}>
            <Save className="h-4 w-4" />
            {savingProfile ? 'Saving...' : 'Save Changes'}
          </button>
        </form>
      </div>

      {/* Learning Preferences */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Learning Preferences</h2>
        <form onSubmit={handleSavePreferences} className="space-y-4">
          <div>
            <label className="label">Default Answer Style</label>
            <select
              value={answerStyle}
              onChange={(e) => setAnswerStyle(e.target.value)}
              className="input"
            >
              {ANSWER_STYLES.map((style) => (
                <option key={style.value} value={style.value}>
                  {style.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">Preferred Subjects</label>
            <div className="flex flex-wrap gap-2 mb-2">
              {preferredSubjects.map((subject) => (
                <span
                  key={subject}
                  className="inline-flex items-center gap-1 px-2.5 py-1 bg-primary-50 text-primary-700 text-sm rounded-full"
                >
                  {subject}
                  <button
                    type="button"
                    onClick={() => handleRemoveSubject(subject)}
                    className="text-primary-400 hover:text-primary-700"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={newSubject}
                onChange={(e) => setNewSubject(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Add a subject..."
                className="input flex-1"
                list="subject-suggestions"
              />
              <datalist id="subject-suggestions">
                {SUBJECT_OPTIONS.map((s) => (
                  <option key={s} value={s} />
                ))}
              </datalist>
              <button
                type="button"
                onClick={handleAddSubject}
                className="btn-secondary px-3"
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div>
            <label className="label">Learning Goals</label>
            <textarea
              value={learningGoals}
              onChange={(e) => setLearningGoals(e.target.value)}
              className="input resize-none"
              rows={3}
              placeholder="Describe your learning goals..."
            />
          </div>

          <button type="submit" className="btn-primary flex items-center gap-2" disabled={savingPrefs}>
            <Save className="h-4 w-4" />
            {savingPrefs ? 'Saving...' : 'Save Preferences'}
          </button>
        </form>
      </div>

      {/* Privacy Settings */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Shield className="h-5 w-5 text-primary-600" />
          Privacy & Data
        </h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div>
              <p className="text-sm font-medium text-gray-900">Data Collection</p>
              <p className="text-xs text-gray-500">We collect learning data to improve your experience</p>
            </div>
            <span className="text-xs font-medium text-green-600 bg-green-100 px-2 py-1 rounded-full">Enabled</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div>
              <p className="text-sm font-medium text-gray-900">Personalized Recommendations</p>
              <p className="text-xs text-gray-500">Use your data to generate better recommendations</p>
            </div>
            <span className="text-xs font-medium text-green-600 bg-green-100 px-2 py-1 rounded-full">Enabled</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div>
              <p className="text-sm font-medium text-gray-900">Analytics Tracking</p>
              <p className="text-xs text-gray-500">Track your learning progress and patterns</p>
            </div>
            <span className="text-xs font-medium text-green-600 bg-green-100 px-2 py-1 rounded-full">Enabled</span>
          </div>
        </div>
      </div>

      {/* Data Management */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Data Management</h2>
        <div className="space-y-3">
          <button
            onClick={handleDownloadData}
            className="w-full flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left"
          >
            <Download className="h-5 w-5 text-primary-600" />
            <div>
              <p className="text-sm font-medium text-gray-900">Download My Data</p>
              <p className="text-xs text-gray-500">Export your profile and learning data as JSON</p>
            </div>
          </button>
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="w-full flex items-center gap-3 p-3 border border-red-200 rounded-lg hover:bg-red-50 transition-colors text-left"
          >
            <Trash2 className="h-5 w-5 text-red-600" />
            <div>
              <p className="text-sm font-medium text-red-900">Delete Account</p>
              <p className="text-xs text-red-500">Permanently delete your account and all data</p>
            </div>
          </button>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="h-10 w-10 rounded-full bg-red-100 flex items-center justify-center">
                <AlertCircle className="h-5 w-5 text-red-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Delete Account</h3>
            </div>
            <p className="text-sm text-gray-600 mb-2">
              Are you sure you want to delete your account? This action <strong>cannot be undone</strong>.
            </p>
            <p className="text-sm text-gray-500 mb-6">
              All your documents, conversations, quizzes, and learning data will be permanently deleted.
            </p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setShowDeleteConfirm(false)} className="btn-secondary">
                Cancel
              </button>
              <button
                onClick={handleDeleteAccount}
                disabled={deleting}
                className="btn-primary bg-red-600 hover:bg-red-700"
              >
                {deleting ? 'Deleting...' : 'Delete Account'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
