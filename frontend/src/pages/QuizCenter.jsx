import React, { useState, useEffect, useCallback } from 'react'
import {
  HelpCircle,
  Plus,
  Clock,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  X,
  AlertCircle,
  Trophy,
  RotateCcw,
  FileText,
  Sparkles,
} from 'lucide-react'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'
import EmptyState from '../components/EmptyState'
import { list, get, generate, submit, getResults, getAttempts } from '../api/quizzes'
import { list as listDocuments } from '../api/documents'

const DIFFICULTIES = ['Easy', 'Medium', 'Hard']
const QUESTION_TYPES = [
  { value: 'multiple_choice', label: 'Multiple Choice' },
  { value: 'true_false', label: 'True/False' },
  { value: 'short_answer', label: 'Short Answer' },
  { value: 'fill_in_blank', label: 'Fill in the Blank' },
]

export default function QuizCenter() {
  const [view, setView] = useState('list') // list | create | take | results
  const [quizzes, setQuizzes] = useState([])
  const [attempts, setAttempts] = useState([])
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Create quiz state
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedDoc, setSelectedDoc] = useState('')
  const [numQuestions, setNumQuestions] = useState(5)
  const [difficulty, setDifficulty] = useState('Medium')
  const [questionTypes, setQuestionTypes] = useState(['multiple_choice'])
  const [generating, setGenerating] = useState(false)

  // Take quiz state
  const [activeQuiz, setActiveQuiz] = useState(null)
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [answers, setAnswers] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const [showSubmitConfirm, setShowSubmitConfirm] = useState(false)

  // Results state
  const [results, setResults] = useState(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [quizData, attemptData, docData] = await Promise.all([
        list(),
        getAttempts(),
        listDocuments(),
      ])
      setQuizzes(quizData || [])
      setAttempts(attemptData || [])
      setDocuments((docData || []).filter((d) => d.status === 'completed'))
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load quizzes')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleGenerate = async () => {
    if (!selectedDoc) {
      setError('Please select a document')
      return
    }
    if (questionTypes.length === 0) {
      setError('Please select at least one question type')
      return
    }
    setGenerating(true)
    setError('')
    try {
      const params = {
        document_id: selectedDoc,
        num_questions: numQuestions,
        difficulty: difficulty.toLowerCase(),
        question_types: questionTypes,
      }
      const quiz = await generate(params)
      setShowCreateModal(false)
      setQuizzes((prev) => [quiz, ...prev])
      startQuiz(quiz)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate quiz')
    } finally {
      setGenerating(false)
    }
  }

  const startQuiz = async (quiz) => {
    try {
      const fullQuiz = await get(quiz.id)
      setActiveQuiz(fullQuiz)
      setCurrentQuestion(0)
      setAnswers({})
      setResults(null)
      setView('take')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load quiz')
    }
  }

  const handleAnswerChange = (questionId, answer) => {
    setAnswers((prev) => ({ ...prev, [questionId]: answer }))
  }

  const handleSubmit = async () => {
    setSubmitting(true)
    setError('')
    try {
      const formattedAnswers = Object.entries(answers).map(([question_id, answer]) => ({
        question_id,
        answer,
      }))
      const result = await submit(activeQuiz.id, formattedAnswers)
      setResults(result)
      setView('results')
      fetchData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit quiz')
    } finally {
      setSubmitting(false)
      setShowSubmitConfirm(false)
    }
  }

  const resetQuiz = () => {
    setView('list')
    setActiveQuiz(null)
    setResults(null)
    setCurrentQuestion(0)
    setAnswers({})
  }

  const toggleQuestionType = (type) => {
    setQuestionTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    )
  }

  if (loading) return <LoadingSpinner size="lg" />

  // Quiz Taking View
  if (view === 'take' && activeQuiz) {
    const questions = activeQuiz.questions || []
    const question = questions[currentQuestion]
    const totalQuestions = questions.length
    const progress = ((currentQuestion + 1) / totalQuestions) * 100

    return (
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">{activeQuiz.title || 'Quiz'}</h1>
          <button onClick={resetQuiz} className="btn-secondary text-sm">
            Exit Quiz
          </button>
        </div>

        <ErrorAlert message={error} onDismiss={() => setError('')} />

        {/* Progress Bar */}
        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Question {currentQuestion + 1} of {totalQuestions}
            </span>
            <span className="text-sm text-gray-500">
              {Object.keys(answers).length} answered
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-primary-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Question Card */}
        {question && (
          <div className="card">
            <div className="flex items-start gap-3 mb-4">
              <span className="inline-flex items-center justify-center h-8 w-8 rounded-full bg-primary-100 text-primary-700 text-sm font-bold flex-shrink-0">
                {currentQuestion + 1}
              </span>
              <div className="flex-1">
                <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">
                  {question.type?.replace('_', ' ') || 'Question'}
                </p>
                <h3 className="text-lg font-medium text-gray-900">{question.question || question.text}</h3>
              </div>
            </div>

            {/* Answer Input */}
            <div className="mt-6">
              {question.type === 'multiple_choice' && question.options && (
                <div className="space-y-3">
                  {question.options.map((option, i) => (
                    <label
                      key={i}
                      className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                        answers[question.id] === i
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-200 hover:border-primary-300'
                      }`}
                    >
                      <input
                        type="radio"
                        name={`question-${question.id}`}
                        checked={answers[question.id] === i}
                        onChange={() => handleAnswerChange(question.id, i)}
                        className="text-primary-600"
                      />
                      <span className="text-sm text-gray-700">{option}</span>
                    </label>
                  ))}
                </div>
              )}

              {question.type === 'true_false' && (
                <div className="flex gap-4">
                  {['True', 'False'].map((val) => (
                    <label
                      key={val}
                      className={`flex-1 flex items-center justify-center gap-2 p-3 rounded-lg border cursor-pointer transition-colors ${
                        answers[question.id] === val
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-200 hover:border-primary-300'
                      }`}
                    >
                      <input
                        type="radio"
                        name={`question-${question.id}`}
                        checked={answers[question.id] === val}
                        onChange={() => handleAnswerChange(question.id, val)}
                        className="text-primary-600"
                      />
                      <span className="text-sm font-medium text-gray-700">{val}</span>
                    </label>
                  ))}
                </div>
              )}

              {(question.type === 'short_answer' || question.type === 'fill_in_blank') && (
                <textarea
                  value={answers[question.id] || ''}
                  onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                  className="input resize-none"
                  rows={3}
                  placeholder="Type your answer here..."
                />
              )}
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => setCurrentQuestion((q) => Math.max(0, q - 1))}
            disabled={currentQuestion === 0}
            className="btn-secondary flex items-center gap-1"
          >
            <ChevronLeft className="h-4 w-4" />
            Previous
          </button>
          {currentQuestion < totalQuestions - 1 ? (
            <button
              onClick={() => setCurrentQuestion((q) => q + 1)}
              className="btn-primary flex items-center gap-1"
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </button>
          ) : (
            <button
              onClick={() => setShowSubmitConfirm(true)}
              className="btn-primary flex items-center gap-1"
            >
              <CheckCircle className="h-4 w-4" />
              Submit Quiz
            </button>
          )}
        </div>

        {/* Submit Confirmation */}
        {showSubmitConfirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
            <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="h-10 w-10 rounded-full bg-yellow-100 flex items-center justify-center">
                  <AlertCircle className="h-5 w-5 text-yellow-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">Submit Quiz?</h3>
              </div>
              <p className="text-sm text-gray-600 mb-2">
                You have answered {Object.keys(answers).length} of {totalQuestions} questions.
              </p>
              {Object.keys(answers).length < totalQuestions && (
                <p className="text-sm text-yellow-600 mb-4">
                  You have {totalQuestions - Object.keys(answers).length} unanswered question(s).
                </p>
              )}
              <div className="flex justify-end gap-3 mt-6">
                <button onClick={() => setShowSubmitConfirm(false)} className="btn-secondary">
                  Review Answers
                </button>
                <button onClick={handleSubmit} className="btn-primary" disabled={submitting}>
                  {submitting ? 'Submitting...' : 'Submit'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  // Results View
  if (view === 'results' && results) {
    const score = results.score || 0
    const correct = results.correct_count || results.correct || 0
    const incorrect = results.incorrect_count || results.incorrect || 0
    const total = results.total_questions || (correct + incorrect)
    const percentage = total > 0 ? Math.round((correct / total) * 100) : 0

    return (
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="text-center">
          <Trophy className="h-16 w-16 text-yellow-500 mx-auto mb-4" />
          <h1 className="text-3xl font-bold text-gray-900">Quiz Complete!</h1>
          <p className="text-gray-600 mt-1">{activeQuiz?.title || 'Quiz Results'}</p>
        </div>

        <ErrorAlert message={error} onDismiss={() => setError('')} />

        {/* Score Card */}
        <div className="card text-center">
          <div className="text-5xl font-bold text-primary-600 mb-2">{percentage}%</div>
          <p className="text-gray-600 mb-4">Your Score</p>
          <div className="flex justify-center gap-8">
            <div>
              <p className="text-2xl font-bold text-green-600">{correct}</p>
              <p className="text-sm text-gray-500">Correct</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-red-600">{incorrect}</p>
              <p className="text-sm text-gray-500">Incorrect</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-600">{total}</p>
              <p className="text-sm text-gray-500">Total</p>
            </div>
          </div>
        </div>

        {/* Answer Review */}
        {results.review && results.review.length > 0 && (
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Review Answers</h2>
            <div className="space-y-4">
              {results.review.map((item, i) => (
                <div
                  key={i}
                  className={`p-4 rounded-lg border ${
                    item.is_correct ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`h-6 w-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                      item.is_correct ? 'bg-green-200' : 'bg-red-200'
                    }`}>
                      {item.is_correct ? (
                        <CheckCircle className="h-4 w-4 text-green-700" />
                      ) : (
                        <X className="h-4 w-4 text-red-700" />
                      )}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{item.question}</p>
                      <p className="text-sm text-gray-600 mt-1">
                        Your answer: <span className={item.is_correct ? 'text-green-700' : 'text-red-700'}>{item.user_answer || 'No answer'}</span>
                      </p>
                      {!item.is_correct && item.correct_answer && (
                        <p className="text-sm text-green-700 mt-1">Correct answer: {item.correct_answer}</p>
                      )}
                      {item.explanation && (
                        <p className="text-sm text-gray-500 mt-2 italic">{item.explanation}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex justify-center gap-4">
          <button onClick={resetQuiz} className="btn-secondary flex items-center gap-2">
            <RotateCcw className="h-4 w-4" />
            Back to Quizzes
          </button>
          {activeQuiz && (
            <button onClick={() => startQuiz(activeQuiz)} className="btn-primary flex items-center gap-2">
              <RotateCcw className="h-4 w-4" />
              Retake Quiz
            </button>
          )}
        </div>
      </div>
    )
  }

  // List View
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Quiz Center</h1>
          <p className="text-gray-600 mt-1">Generate and take AI-powered quizzes</p>
        </div>
        <button onClick={() => setShowCreateModal(true)} className="btn-primary flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Generate Quiz
        </button>
      </div>

      <ErrorAlert message={error} onDismiss={() => setError('')} />

      {/* Quiz List */}
      {quizzes.length === 0 ? (
        <div className="card">
          <EmptyState
            icon={HelpCircle}
            title="No quizzes yet"
            description="Generate your first AI-powered quiz to test your knowledge."
            action={
              <button onClick={() => setShowCreateModal(true)} className="btn-primary inline-flex items-center gap-2">
                <Plus className="h-4 w-4" />
                Generate Quiz
              </button>
            }
          />
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {quizzes.map((quiz) => (
            <div key={quiz.id} className="card">
              <div className="flex items-start justify-between mb-3">
                <h3 className="font-semibold text-gray-900">{quiz.title || 'Untitled Quiz'}</h3>
                <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                  quiz.difficulty === 'easy' ? 'bg-green-100 text-green-700' :
                  quiz.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-red-100 text-red-700'
                }`}>
                  {quiz.difficulty || 'Medium'}
                </span>
              </div>
              <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
                <span className="flex items-center gap-1">
                  <HelpCircle className="h-4 w-4" />
                  {quiz.question_count || 0} questions
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  {quiz.duration || 15} min
                </span>
              </div>
              <button onClick={() => startQuiz(quiz)} className="btn-primary w-full">
                Start Quiz
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Attempt History */}
      {attempts.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Attempts</h2>
          <div className="space-y-2">
            {attempts.slice(0, 5).map((attempt) => (
              <div key={attempt.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                <div className="flex items-center gap-3">
                  <div className={`h-8 w-8 rounded-full flex items-center justify-center ${
                    (attempt.score || 0) >= 70 ? 'bg-green-100' : 'bg-red-100'
                  }`}>
                    <CheckCircle className={`h-4 w-4 ${
                      (attempt.score || 0) >= 70 ? 'text-green-600' : 'text-red-600'
                    }`} />
                  </div>
                  <span className="text-sm text-gray-700">{attempt.quiz_title || 'Quiz'}</span>
                </div>
                <span className={`text-sm font-medium ${
                  (attempt.score || 0) >= 70 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {attempt.score}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Create Quiz Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Generate New Quiz</h3>
              <button onClick={() => setShowCreateModal(false)} className="p-1 text-gray-400 hover:text-gray-600">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-6 space-y-5">
              {/* Document Selection */}
              <div>
                <label className="label">Select Document</label>
                {documents.length === 0 ? (
                  <p className="text-sm text-gray-500 p-3 bg-gray-50 rounded-lg">
                    No completed documents available. Upload a document first.
                  </p>
                ) : (
                  <select
                    value={selectedDoc}
                    onChange={(e) => setSelectedDoc(e.target.value)}
                    className="input"
                  >
                    <option value="">Choose a document...</option>
                    {documents.map((doc) => (
                      <option key={doc.id} value={doc.id}>
                        {doc.filename || doc.title || 'Untitled'}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {/* Number of Questions */}
              <div>
                <label className="label">Number of Questions: {numQuestions}</label>
                <input
                  type="range"
                  min={3}
                  max={20}
                  value={numQuestions}
                  onChange={(e) => setNumQuestions(parseInt(e.target.value))}
                  className="w-full accent-primary-600"
                />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>3</span>
                  <span>20</span>
                </div>
              </div>

              {/* Difficulty */}
              <div>
                <label className="label">Difficulty</label>
                <div className="flex gap-2">
                  {DIFFICULTIES.map((d) => (
                    <button
                      key={d}
                      onClick={() => setDifficulty(d)}
                      className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium border transition-colors ${
                        difficulty === d
                          ? 'border-primary-500 bg-primary-50 text-primary-700'
                          : 'border-gray-200 text-gray-600 hover:border-primary-300'
                      }`}
                    >
                      {d}
                    </button>
                  ))}
                </div>
              </div>

              {/* Question Types */}
              <div>
                <label className="label">Question Types</label>
                <div className="grid grid-cols-2 gap-2">
                  {QUESTION_TYPES.map((type) => (
                    <label
                      key={type.value}
                      className={`flex items-center gap-2 p-2 rounded-lg border cursor-pointer transition-colors ${
                        questionTypes.includes(type.value)
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-200 hover:border-primary-300'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={questionTypes.includes(type.value)}
                        onChange={() => toggleQuestionType(type.value)}
                        className="text-primary-600 rounded"
                      />
                      <span className="text-sm text-gray-700">{type.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Generate Button */}
              <button
                onClick={handleGenerate}
                disabled={generating || !selectedDoc}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                <Sparkles className="h-4 w-4" />
                {generating ? 'Generating Quiz...' : 'Generate Quiz'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
