'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { FileText, ArrowRight, ArrowLeft, Loader } from 'lucide-react'

interface ScriptGenerationStepProps {
  data: any
  updateData: (updates: any) => void
  onNext: () => void
  onPrev: () => void
}

export default function ScriptGenerationStep({ data, updateData, onNext, onPrev }: ScriptGenerationStepProps) {
  const [loading, setLoading] = useState(true)
  const [script, setScript] = useState<any>(null)

  useEffect(() => {
    generateScript()
  }, [])

  const generateScript = async () => {
    setLoading(true)

    try {
      const token = localStorage.getItem('token')
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

      const response = await fetch(`${API_BASE}/movies/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          title: data.title,
          genre: data.genre,
          style: data.style,
          description: data.description
        })
      })

      if (response.ok) {
        const movieData = await response.json()
        setScript(movieData.script)
        updateData({ script: movieData.script })
      } else {
        // Mock script for demo
        const mockScript = [
          {
            scene_number: 1,
            title: "Opening Scene",
            description: "The protagonist wakes up in a mysterious world",
            dialogue: ["I don't remember how I got here...", "This place is incredible!"]
          },
          {
            scene_number: 2,
            title: "Discovery",
            description: "Our hero finds a hidden artifact",
            dialogue: ["What is this strange object?", "It seems to be calling to me"]
          },
          {
            scene_number: 3,
            title: "Climax",
            description: "The final confrontation begins",
            dialogue: ["I won't let you destroy this world!", "Your journey ends here!"]
          }
        ]
        setScript(mockScript)
        updateData({ script: mockScript })
      }
    } catch (error) {
      console.error('Script generation failed:', error)
      // Use mock script as fallback
      const mockScript = [
        {
          scene_number: 1,
          title: "Opening Scene",
          description: "The protagonist wakes up in a mysterious world",
          dialogue: ["I don't remember how I got here...", "This place is incredible!"]
        },
        {
          scene_number: 2,
          title: "Discovery",
          description: "Our hero finds a hidden artifact",
          dialogue: ["What is this strange object?", "It seems to be calling to me"]
        },
        {
          scene_number: 3,
          title: "Climax",
          description: "The final confrontation begins",
          dialogue: ["I won't let you destroy this world!", "Your journey ends here!"]
        }
      ]
      setScript(mockScript)
      updateData({ script: mockScript })
    } finally {
      setLoading(false)
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
          <FileText className="w-8 h-8 text-white" />
        </div>
        <h2 className="text-3xl font-bold text-white mb-4">Generating Your Script</h2>
        <p className="text-dark-300">
          AI is creating a compelling screenplay based on your idea
        </p>
      </motion.div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-12">
          <Loader className="w-12 h-12 text-primary-500 animate-spin mb-4" />
          <p className="text-dark-300">Generating script...</p>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="card p-6">
            <h3 className="text-xl font-semibold text-white mb-4">Generated Script</h3>

            {script && script.map((scene: any, index: number) => (
              <motion.div
                key={scene.scene_number}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.2 }}
                className="border-l-4 border-primary-500 pl-4 mb-6 last:mb-0"
              >
                <h4 className="text-lg font-medium text-white mb-2">
                  Scene {scene.scene_number}: {scene.title}
                </h4>
                <p className="text-dark-300 mb-3">{scene.description}</p>

                {scene.dialogue && scene.dialogue.length > 0 && (
                  <div className="bg-dark-700 p-3 rounded-lg">
                    <h5 className="text-sm font-medium text-dark-200 mb-2">Dialogue:</h5>
                    <ul className="space-y-1">
                      {scene.dialogue.map((line: string, lineIndex: number) => (
                        <li key={lineIndex} className="text-dark-300 italic">
                          "{line}"
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
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
              onClick={onNext}
              className="btn-primary flex items-center space-x-2"
            >
              <span>Review Scenes</span>
              <ArrowRight className="w-4 h-4" />
            </motion.button>
          </div>
        </div>
      )}
    </div>
  )
}
