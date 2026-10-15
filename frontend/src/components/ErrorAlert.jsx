import React from 'react'
import { XCircle, X } from 'lucide-react'

export default function ErrorAlert({ message, onDismiss }) {
  if (!message) return null

  return (
    <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
      <XCircle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
      <p className="flex-1 text-sm text-red-700">{message}</p>
      {onDismiss && (
        <button onClick={onDismiss} className="text-red-400 hover:text-red-600">
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  )
}
