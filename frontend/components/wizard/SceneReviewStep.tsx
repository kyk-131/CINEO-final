'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Eye, Check, RefreshCw, ArrowRight, ArrowLeft } from 'lucide-react'

interface SceneReviewStepProps {
  data: any
  updateData: (updates: any) => void
  onNext: () => void
  onPrev: () => void
}

export default function SceneReviewStep({ data, updateData, onNext, onPrev }: SceneReviewStepProps) {
  const [scenes, setScenes] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadScenes()
  }, [])

  const loadScenes = async () => {
    setLoading(true)

    try {
      const token = localStorage.getItem('token')
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

      // For demo, we'll use mock scenes based on the script
      const mockScenes = data.script.map((scene: any, index: number) => ({
        id: index + 1,
        scene_number: scene.scene_number,
        title: scene.title,
        description: scene.description,
        status: 'completed',
        storyboard_url: `https://picsum.photos/400/300?random=${scene.scene_number}`,
        video_url: null
      }))

      setScenes(mockScenes)
      updateData({ scenes: mockScenes })
    } catch (error) {
      console.error('Failed to load scenes:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSceneAction = (sceneId: number, action: 'accept' | 'regenerate') => {
    setScenes(prev => prev.map(scene =>
      scene.id === sceneId
        ? { ...scene, status: action === 'accept' ? 'completed' : 'generating' }
        : scene
    ))
  }

  return (
    <div className="max-w-6xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <div className="w-16 h-16 bg-primary-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <Eye className="w-8 h-8 text-white" />
        </div>
        <h2 className="text-3xl font-bold text-white mb-4">Review Your Scenes</h2>
        <p className="text-dark-300">
          Check the generated storyboards and approve or regenerate scenes
        </p>
      </motion.div>

      {loading ? (
        <div className="text-center py-12">
          <RefreshCw className="w-12 h-12 text-primary-500 animate-spin mx-auto mb-4" />
          <p className="text-dark-300">Loading scenes...</p>
        </div>
      ) : (
        <div className="grid gap-6">
          {scenes.map((scene, index) => (
            <motion.div
              key={scene.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="card p-6"
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-semibold text-white">
                    Scene {scene.scene_number}: {scene.title}
                  </h3>
                  <p className="text-dark-300 mt-1">{scene.description}</p>
                </div>

                <div className="flex space-x-2">
                  <button
                    onClick={() => handleSceneAction(scene.id, 'regenerate')}
                    className="btn-secondary flex items-center space-x-1"
                  >
                    <RefreshCw className="w-4 h-4" />
                    <span>Regenerate</span>
                  </button>

                  <button
                    onClick={() => handleSceneAction(scene.id, 'accept')}
                    disabled={scene.status === 'completed'}
                    className="btn-primary flex items-center space-x-1 disabled:opacity-50"
                  >
                    <Check className="w-4 h-4" />
                    <span>Accept</span>
                  </button>
                </div>
              </div>

              <div className="aspect-video bg-dark-700 rounded-lg flex items-center justify-center">
                {scene.storyboard_url ? (
                  <img
                    src={scene.storyboard_url}
                    alt={`Scene ${scene.scene_number}`}
                    className="w-full h-full object-cover rounded-lg"
                  />
                ) : (
                  <RefreshCw className="w-8 h-8 text-dark-500 animate-spin" />
                )}
              </div>

              {scene.status === 'generating' && (
                <div className="mt-4 text-center">
                  <RefreshCw className="w-6 h-6 text-primary-500 animate-spin mx-auto mb-2" />
                  <p className="text-dark-300">Generating scene...</p>
                </div>
              )}
            </motion.div>
          ))}
        </div>
      )}

      <div className="flex justify-between mt-8">
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
          <span>Finalize Movie</span>
          <ArrowRight className="w-4 h-4" />
        </motion.button>
      </div>
    </div>
  )
}
