'use client'

import { Inter } from 'next/font/google'
import './globals.css'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from '@/contexts/AuthContext'
import { MovieProvider } from '@/contexts/MovieContext'
import BackgroundEffects from '@/components/BackgroundEffects'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'Cineo AI - Futuristic AI Movie Generator',
  description: 'Create stunning AI-generated movies with cutting-edge artificial intelligence',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} relative overflow-x-hidden`}>
        <AuthProvider>
          <MovieProvider>
            <BackgroundEffects />
            <div className="relative z-10 min-h-screen">
              {children}
              <Toaster
                position="top-right"
                toastOptions={{
                  style: {
                    background: 'rgba(15, 23, 42, 0.9)',
                    color: '#f1f5f9',
                    backdropFilter: 'blur(20px)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  },
                }}
              />
            </div>
          </MovieProvider>
        </AuthProvider>
      </body>
    </html>
  )
}
