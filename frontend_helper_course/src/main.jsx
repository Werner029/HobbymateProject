import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ReactKeycloakProvider } from '@react-keycloak/web';
import { DialogProvider } from './DialogCtx';
import kc from './keycloak';
import ThemeProvider from './ThemeProvider';
import App from './App';
import './index.css';
import axios from 'axios';

const handleTokens = ({ token }) => {
  if (token) {
    localStorage.setItem('kc_token', token);
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete axios.defaults.headers.common['Authorization'];
  }
};

const saved = localStorage.getItem('kc_token');
if (saved) axios.defaults.headers.common['Authorization'] = `Bearer ${saved}`;

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ReactKeycloakProvider
      authClient={kc}
      initOptions={{ onLoad: 'check-sso', pkceMethod: 'S256' }}
      onTokens={handleTokens}
    >
      <ThemeProvider>
        <DialogProvider>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </DialogProvider>
      </ThemeProvider>
    </ReactKeycloakProvider>
  </React.StrictMode>,
);
