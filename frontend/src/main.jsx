import React from 'react'
import ReactDOM from 'react-dom/client'
// Fix Leaflet icons BEFORE any react-leaflet imports
import './utils/leaflet-icons'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)