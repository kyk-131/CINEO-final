'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, ArrowLeft, ArrowRight, Sparkles } from 'lucide-react'
import MovieIdeaStep from '@/components/wizard/MovieIdeaStep'
import StyleSelectionStep from '@/components/wizard/StyleSelectionStep'
import ScriptGenerationStep from '@/components/wizard/ScriptGenerationStep'
import SceneReviewStep from '@/components/wizard/SceneReviewStep'
import FinalizationStep from '@/components/wizard/FinalizationStep'

interface MovieWizardProps {
  onClose: () => void
  onMovieCreated: () => void
}

type WizardStep = 'idea' | 'style' | 'script' | 'review' | 'finalize'

export default function MovieWizard({ onClose, onMovieCreated }: MovieWizardProps) {
  const [currentStep, setCurrentStep] = useState<WizardStep>('idea')
  const [movieData, setMovieData] = useState({
    title: '',
    genre: '',
    style: '',
    description: '',
    script: null,
    scenes: []
  })

  const steps = [
    { id: 'idea', title: 'Movie Idea', description: 'Tell us about your movie' },
    { id: 'style', title: 'Style & Tone', description: 'Choose visual style and tone' },
    { id: 'script', title: 'Script Generation', description: 'AI generates your script' },
    { id: 'review', title: 'Scene Review', description: 'Review and approve scenes' },
    { id: 'finalize', title: 'Finalize', description: 'Generate poster and trailer' }
  ]

  const currentStepIndex = steps.findIndex(step => step.id === currentStep)

  const nextStep = () => {
    if (currentStepIndex < steps.length - 1) {
      setCurrentStep(steps[currentStepIndex + 1].id as WizardStep)
    }
  }

  const prevStep = () => {
    if (currentStepIndex > 0) {
      setCurrentStep(steps[currentStepIndex - 1].id as WizardStep)
    }
  }

  const updateMovieData = (updates: Partial<typeof movieData>) => {
    setMovieData(prev => ({ ...prev, ...updates }))
  }

  const renderStep = () => {
    switch (currentStep) {
      case 'idea':
        return <MovieIdeaStep data={movieData} updateData={updateMovieData} onNext={nextStep} />
      case 'style':
        return <StyleSelectionStep data={movieData} updateData={updateMovieData} onNext={nextStep} onPrev={prevStep} />
      case 'script':
        return <ScriptGenerationStep data={movieData} updateData={updateMovieData} onNext={nextStep} onPrev={prevStep} />
      case 'review':
        return <SceneReviewStep data={movieData} updateData={updateMovieData} onNext={nextStep} onPrev={prevStep} />
      case 'finalize':
        return <FinalizationStep data={movieData} updateData={updateMovieData} onComplete={onMovieCreated} onPrev={prevStep} />
      default:
        return null
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-dark-900 rounded-2xl border border-dark-700 w-full max-w-4xl max-h-[90vh] overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-dark-700">
          <div>
            <h2 className="text-2xl font-bold text-white">Create New Movie</h2>
            <p className="text-dark-300 mt-1">Step {currentStepIndex + 1} of {steps.length}</p>
          </div>

          <button
            onClick={onClose}
            className="text-dark-400 hover:text-white transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="px-6 py-4">
          <div className="flex items-center space-x-2 mb-4">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    index <= currentStepIndex
                      ? 'bg-primary-600 text-white'
                      : 'bg-dark-700 text-dark-400'
                  }`}
                >
                  {index < currentStepIndex ? <Sparkles className="w-4 h-4" /> : index + 1}
                </div>

                {index < steps.length - 1 && (
                  <div
                    className={`w-12 h-0.5 mx-2 ${
                      index < currentStepIndex ? 'bg-primary-600' : 'bg-dark-700'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>

          <div className="text-center">
            <h3 className="text-lg font-semibold text-white">{steps[currentStepIndex].title}</h3>
            <p className="text-dark-300 text-sm">{steps[currentStepIndex].description}</p>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              {renderStep()}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center p-6 border-t border-dark-700">
          <button
            onClick={prevStep}
            disabled={currentStepIndex === 0}
            className={`btn-secondary flex items-center space-x-2 ${
              currentStepIndex === 0 ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Previous</span>
          </button>

          <div className="flex items-center space-x-4">
            <button onClick={onClose} className="text-dark-300 hover:text-white">
              Cancel
            </button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
}
