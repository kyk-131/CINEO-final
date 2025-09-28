'use client'

import React, { createContext, useContext, useState } from 'react'

interface Movie {
  id: number
  title: string
  genre: string
  style: string
  description: string
  status: string
  script?: any[]
  poster_url?: string
  trailer_url?: string
  video_url?: string
}

interface MovieContextType {
  currentMovie: Movie | null
  setCurrentMovie: (movie: Movie | null) => void
  movies: Movie[]
  setMovies: (movies: Movie[]) => void
}

const MovieContext = createContext<MovieContextType | undefined>(undefined)

export function useMovie() {
  const context = useContext(MovieContext)
  if (context === undefined) {
    throw new Error('useMovie must be used within a MovieProvider')
  }
  return context
}

export function MovieProvider({ children }: { children: React.ReactNode }) {
  const [currentMovie, setCurrentMovie] = useState<Movie | null>(null)
  const [movies, setMovies] = useState<Movie[]>([])

  return (
    <MovieContext.Provider value={{ currentMovie, setCurrentMovie, movies, setMovies }}>
      {children}
    </MovieContext.Provider>
  )
}
