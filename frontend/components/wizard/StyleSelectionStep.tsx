'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Palette, ArrowRight, ArrowLeft } from 'lucide-react'

interface StyleSelectionStepProps {
  data: any
  updateData: (updates: any) => void
  onNext: () => void
  onPrev: () => void
}

export default function StyleSelectionStep({ data, updateData, onNext, onPrev }: StyleSelectionStepProps) {
  const [style, setStyle] = useState(data.style)

  const styles = [
    { id: 'cinematic', name: 'Cinematic', description: 'Hollywood-style dramatic lighting and composition' },
    { id: 'anime', name: 'Anime', description: 'Vibrant colors and dynamic animation style' },
    { id: 'fantasy', name: 'Fantasy', description: 'Magical and ethereal visual effects' },
    { id: 'realistic', name: 'Realistic', description: 'Natural lighting and practical effects' },
    { id: 'noir', name: 'Film Noir', description: 'Dark, moody, black and white aesthetic' },
    { id: 'sci-fi', name: 'Sci-Fi', description: 'Futuristic technology and sleek designs' }
  ]

  const handleNext = () => {
    if (style) {
      updateData({ style })
      onNext()
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <div className="w-16 h-16 bg-primary-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <Palette className="w-8 h-8 text-white" />
        </div>
        <h2 className="text-3xl font-bold text-white mb-4">Choose Your Visual Style</h2>
        <p className="text-dark-300">
          Select the aesthetic that best matches your movie's vision
        </p>
      </motion.div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {styles.map((styleOption) => (
          <motion.div
            key={styleOption.id}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setStyle(styleOption.id)}
            className={`card p-4 cursor-pointer transition-colors ${
              style === styleOption.id ? 'ring-2 ring-primary-500 bg-primary-600/10' : ''
            }`}
          >
            <h3 className="text-lg font-semibold text-white mb-2">{styleOption.name}</h3>
            <p className="text-dark-300 text-sm">{styleOption.description}</p>
          </motion.div>
        ))}
      </div>

      <div className="flex justify-between">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onPrev}
          className="btn-secondary flex items-center space-x-2"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Previous</span>
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleNext}
          disabled={!style}
          className="btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span>Generate Script</span>
          <ArrowRight className="w-4 h-4" />
        </motion.button>
      </div>
    </div>
  )
}
