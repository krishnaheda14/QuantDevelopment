import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider, CssBaseline } from '@mui/material'
import { Toaster } from 'react-hot-toast'
import App from './App'
import { theme } from './theme'
import './index.css'

// Debug: Log app initialization
console.log('[APP] Initializing GEMSCAP Quant Analytics Frontend')
console.log('[APP] Environment:', (import.meta as any).env?.MODE)
console.log('[APP] API Proxy:', '/api → http://localhost:3000')

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000,
    },
  },
})

// Debug: Log React Query initialization
console.log('[REACT-QUERY] Client initialized with default options')

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <App />
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#1e1e1e',
                color: '#fff',
                border: '1px solid #333',
              },
            }}
          />
        </ThemeProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)

console.log('[APP] React app mounted successfully')
