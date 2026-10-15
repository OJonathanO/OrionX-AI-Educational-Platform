import React from 'react'

export default function LoadingSpinner({ size = 'md' }) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  }

  return (
    <div className="flex items-center justify-center p-4">
      <div
        className={`${sizeClasses[size] || sizeClasses.md} animate-spin rounded-full border-2 border-gray-200 border-t-primary-600`}
      />
    </div>
  )
}
