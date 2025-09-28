'use client'

import { motion } from 'framer-motion'
import { useAuth } from '@/contexts/AuthContext'
import { Film, User, LogOut, Settings, Menu } from 'lucide-react'

export default function Navbar() {
  const { user, logout } = useAuth()

  return (
    <motion.nav
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6 }}
      className="glass-nav px-4 py-4 sticky top-0 z-50"
    >
      <div className="container mx-auto flex justify-between items-center">
        <motion.div
          whileHover={{ scale: 1.05 }}
          className="flex items-center space-x-3"
        >
          <motion.div
            whileHover={{ rotate: 360 }}
            transition={{ duration: 0.6 }}
            className="w-12 h-12 glass-card flex items-center justify-center neon-glow"
          >
            <Film className="w-6 h-6 text-purple-400" />
          </motion.div>
          <span className="text-2xl font-bold text-gradient">Cineo AI</span>
        </motion.div>

        <div className="flex items-center space-x-4">
          <motion.div
            whileHover={{ scale: 1.05 }}
            className="hidden md:flex items-center space-x-2 text-white/80 glass-card px-4 py-2 rounded-xl"
          >
            <User className="w-4 h-4" />
            <span className="font-medium">{user?.username}</span>
          </motion.div>

          <motion.button
            whileHover={{ scale: 1.05, rotate: 90 }}
            className="text-white/70 hover:text-white transition-colors p-2 glass-card rounded-xl"
          >
            <Settings className="w-5 h-5" />
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.05 }}
            onClick={logout}
            className="text-white/70 hover:text-red-400 transition-colors p-2 glass-card rounded-xl"
          >
            <LogOut className="w-5 h-5" />
          </motion.button>
        </div>
      </div>
    </motion.nav>
  )
}
