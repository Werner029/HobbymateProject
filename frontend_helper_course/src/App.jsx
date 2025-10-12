import React, { useContext, useEffect, useRef, useState } from 'react';
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { useKeycloak } from '@react-keycloak/web';
import axios from 'axios';
import { Moon, Sun } from 'lucide-react';
import { Theme } from './ThemeProvider';
import Home from './Home';
import HistoryPage from './HistoryPage';
import Profile from './Profile';
import GroupsPage from './GroupsPage';
import ChatPage from './ChatPage';
import PublicProfile from './PublicProfile';
import SupportPage from './SupportPage';
import { useDialogCtx } from './DialogCtx.jsx';
import NotificationBell from './NotificationBell';

function Layout() {
  const { keycloak, _INITIALIZED } = useKeycloak();
  const wsNotif = useRef(null);
  const auth = keycloak?.authenticated;
  const { openId } = useDialogCtx();
  const navigate = useNavigate();
  const location = useLocation();
  const [profileChecked, setProfileChecked] = useState(false);
  const login = () => keycloak.login({ redirectUri: window.location.origin });
  const logout = () => {
    localStorage.removeItem('kc_token');
    delete axios.defaults.headers.common.Authorization;
    keycloak.logout({
      redirectUri: window.location.origin + '?loggedOut',
      federated: true,
    });
  };
  const { dark, toggle } = useContext(Theme);
  const [notes, setNotes] = useState([]);
  useEffect(() => {
    if (!auth) return;

    const url =
      `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://` +
      `${window.location.host}/ws/notifications/?token=${localStorage.getItem('kc_token')}`;

    wsNotif.current?.close();
    const w = new WebSocket(url);

    w.onmessage = (e) => {
      try {
        const n = JSON.parse(e.data);
        if (Number(n.dialog) === openId) return;

        setNotes((prev) => [{ id: Date.now(), ...n, read: false }, ...prev]);
      } catch (err) {
        console.error('WS notify parse error', err);
      }
    };

    w.onerror = console.error;
    wsNotif.current = w;
    return () => w.close();
  }, [auth, openId]);

  const markRead = (id) => {
    setNotes((prev) =>
      id === 'all' ? [] : prev.map((n) => (n.id === id ? { ...n, read: true } : n)),
    );
  };
  useEffect(() => {
    if (!keycloak) return;
    const timer = setInterval(() => {
      keycloak
        .updateToken(30)
        .then((refreshed) => {
          if (refreshed) {
            localStorage.setItem('kc_token', keycloak.token);
          }
        })
        .catch((err) => console.error('Ошибка обновления токена', err));
    }, 50_000);
    return () => clearInterval(timer);
  }, [keycloak]);

  useEffect(() => {
    if (!auth) return;
    axios
      .get('/api/profile/me/')
      .then(({ data }) => {
        const incomplete =
          !data.first_name || !data.last_name || !data.email || !data.interest_vector;
        if (incomplete) {
          navigate('/profile', {
            replace: true,
            state: { returnTo: location.pathname },
          });
        }
      })
      .catch(() => {
        navigate('/profile', {
          replace: true,
          state: { returnTo: location.pathname },
        });
      })
      .finally(() => setProfileChecked(true));
  }, [auth, location.pathname, navigate]);

  if (auth && !profileChecked) {
    return <div className="flex items-center justify-center h-screen">Загрузка профиля…</div>;
  }

  return (
    <div className="min-h-screen flex flex-col bg-neutral-100 dark:bg-neutral-900 text-neutral-900 dark:text-white">
      <header className="bg-white/70 dark:bg-neutral-800/60 backdrop-blur border-b border-neutral-200 dark:border-neutral-700">
        <nav className="container mx-auto flex items-center gap-6 py-4 px-4">
          <Link to="/" className="font-semibold hover:text-emerald-400">
            Главная
          </Link>
          {auth && (
            <>
              <Link to="/dialogs" className="hover:text-emerald-400">
                Диалоги
              </Link>
              <Link to="/groups" className="hover:text-emerald-400">
                Группы
              </Link>
              <Link to="/profile" className="hover:text-emerald-400">
                Профиль
              </Link>
              <Link to="/history" className="hover:text-emerald-400">
                История взаимодействий
              </Link>
              <Link to="/support" className="hover:text-emerald-400">
                Поддержка
              </Link>
            </>
          )}
          <div className="ml-auto flex items-center gap-3">
            <NotificationBell items={notes} markRead={markRead} />

            <button
              onClick={toggle}
              className="p-2 rounded hover:bg-black/10 dark:hover:bg-white/10"
            >
              {dark ? <Sun size={20} /> : <Moon size={20} />}
            </button>

            {auth ? (
              <button
                onClick={logout}
                className="p-2 rounded hover:bg-black/10 dark:hover:bg-white/10"
              >
                Выйти
              </button>
            ) : (
              <button
                onClick={login}
                className="p-2 rounded hover:bg-black/10 dark:hover:bg-white/10"
              >
                Войти
              </button>
            )}
          </div>
        </nav>
      </header>

      <main className="flex-grow">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/dialogs" element={auth ? <ChatPage /> : <Navigate to="/" />} />
          <Route path="/dialogs/:id" element={auth ? <ChatPage /> : <Navigate to="/" />} />
          <Route path="/groups" element={auth ? <GroupsPage /> : <Navigate to="/" />} />
          <Route path="/notifications" element={auth ? <>Уведомления</> : <Navigate to="/" />} />
          <Route path="/profile" element={auth ? <Profile /> : <Navigate to="/" />} />
          <Route path="/profile/:id" element={auth ? <PublicProfile /> : <Navigate to="/" />} />
          <Route path="/support" element={auth ? <SupportPage /> : <Navigate to="/" />} />
          <Route path="/history" element={auth ? <HistoryPage /> : <Navigate to="/" />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return <Layout />;
}
