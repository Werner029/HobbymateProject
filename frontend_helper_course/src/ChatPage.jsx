import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import axios from 'axios';
import { useDialogCtx } from './DialogCtx.jsx';

const safeSrc = (value, fallback = '/default-avatar.png') => {
  try {
    if (!value) return fallback;
    const u = new URL(value, window.location.origin);
    const allowedProtocols = new Set(['http:', 'https:']);
    const isRelative = u.origin === window.location.origin;
    if (isRelative || allowedProtocols.has(u.protocol)) return u.href;
  } catch {
    /* ignore invalid URL */
  }
  return fallback;
};

export default function ChatPage() {
  const { id } = useParams();
  const wsRef = useRef(null);
  const [myId, setMyId] = useState(null);
  const { setOpen } = useDialogCtx();

  const [dialogs, setDialogs] = useState([]);
  const [meta, setMeta] = useState(null);
  const [messages, setMessages] = useState([]);
  const [myContacts, setMyContacts] = useState({});
  const [text, setText] = useState('');

  const [loadingDialogs, setLD] = useState(true);
  const [loadingMsgs, setLM] = useState(false);

  useEffect(() => {
    setOpen(id ? Number(id) : null);
    return () => setOpen(null);
  }, [id, setOpen]);

  useEffect(() => {
    axios
      .get('/api/profile/me/')
      .then(({ data }) => {
        setMyId(data.id);
        setMyContacts({
          tg: data.tg_link,
          vk: data.vk_link,
          tel: data.phone_number,
        });
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    axios
      .get('/api/dialogs/me/')
      .then(({ data }) => setDialogs(data))
      .finally(() => setLD(false));
  }, []);

  useEffect(() => {
    if (!id) {
      return;
    }
    axios
      .get(`/api/dialogs/${id}/`)
      .then(({ data }) => setMeta(data))
      .catch(() => setMeta(null));
  }, [id]);

  useEffect(() => {
    if (!id) return;
    setTimeout(() => setLM(true), 0);
    axios
      .get(`/api/dialogs/${id}/messages/`)
      .then(({ data }) => setMessages(data))
      .finally(() => setLM(false));

    const token = localStorage.getItem('kc_token');
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${proto}://${window.location.host}/ws/dialogs/${id}/?token=${token}`;

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.close(1000, 'switch-dialog');
    }
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (ev) => {
      console.debug('[WS] MSG', ev.data);
      try {
        const msg = JSON.parse(ev.data);
        setMessages((prev) => [...prev, msg]);
      } catch (e) {
        console.error('[WS] parse err', e);
      }
    };
    ws.onclose = (ev) => console.debug('[WS] CLOSE', ev.code, ev.reason);
    ws.onerror = (ev) => console.error('[WS] ERROR', ev);

    wsRef.current = ws;
    return () => ws.close(1000, 'unmount');
  }, [id]);

  const send = (overrideText) => {
    const body = (overrideText ?? text).trim();
    if (!body || !id || wsRef.current.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({ text: body }));
    setText('');
  };

  const offerOtherContact = () => {
    const tmpl =
      `Предлагаю продолжить общение:\n` +
      `Telegram: ${myContacts.tg || '—'}\n` +
      `VK: ${myContacts.vk || '—'}\n` +
      `Телефон: ${myContacts.tel || '—'}`;
    send(tmpl);
  };

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      <aside className="w-72 border-r overflow-y-auto bg-gray-50 dark:bg-gray-900">
        <h2 className="p-3 font-semibold">Диалоги</h2>
        <div className="px-3 py-1 font-medium">Личные</div>
        {loadingDialogs ? (
          <p className="p-3">Загрузка…</p>
        ) : (
          dialogs
            .filter((d) => !d.is_group)
            .map((d) => {
              const p = d.partner;
              const title =
                p.first_name || p.last_name ? `${p.first_name} ${p.last_name}`.trim() : p.username;
              return (
                <Link
                  key={d.id}
                  to={`/dialogs/${d.id}`}
                  className={`block px-4 py-2 hover:bg-gray-200 dark:hover:bg-gray-700
                    ${String(d.id) === id ? 'bg-gray-200 dark:bg-gray-700' : ''}`}
                >
                  {title}
                </Link>
              );
            })
        )}
        <div className="px-3 py-1 font-medium mt-4">Групповые</div>
        {dialogs
          .filter((d) => d.is_group)
          .map((d) => (
            <Link
              key={d.id}
              to={`/dialogs/${d.id}`}
              className={`block px-4 py-2 hover:bg-gray-200 dark:hover:bg-gray-700
              ${String(d.id) === id ? 'bg-gray-200 dark:bg-gray-700' : ''}`}
            >
              {d.group_name}
            </Link>
          ))}
      </aside>

      <section className="flex-1 flex flex-col">
        {!id ? (
          <div className="flex-1 flex items-center justify-center text-gray-500">Чат не выбран</div>
        ) : (
          <>
            <div className="border-b p-3 bg-gray-100 dark:bg-gray-800 flex items-center">
              {meta?.is_group ? (
                <h2 className="text-lg font-semibold">{meta.group_name}</h2>
              ) : (
                meta?.partner && (
                  <Link
                    to={meta.partner.id === myId ? '/profile' : `/profile/${meta.partner.id}`}
                    className="flex items-center space-x-2 hover:underline"
                  >
                    <img
                      src={safeSrc(meta.partner?.avatar)}
                      className="w-8 h-8 rounded-full"
                      alt=""
                    />

                    <span className="text-lg font-semibold">
                      {meta.partner.first_name || meta.partner.last_name
                        ? `${meta.partner.first_name} ${meta.partner.last_name}`.trim()
                        : meta.partner.username}
                    </span>
                  </Link>
                )
              )}
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {loadingMsgs ? (
                <p>Загрузка…</p>
              ) : (
                messages.map((m) => (
                  <div key={m.id} className="flex items-start space-x-3">
                    <img src={safeSrc(m.sender_avatar)} className="w-8 h-8 rounded-full" alt="" />
                    <div>
                      <div className="flex items-center space-x-2">
                        <Link
                          to={
                            (m.sender_id ?? m.sender === myId)
                              ? '/profile'
                              : `/profile/${m.sender_id ?? m.sender}`
                          }
                          className="font-medium hover:underline"
                        >
                          {m.sender_first_name || m.sender_last_name
                            ? `${m.sender_first_name} ${m.sender_last_name}`.trim()
                            : m.sender_name}
                        </Link>
                        <span className="text-xs text-gray-500">
                          {new Date(m.created_at).toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="mt-1 px-3 py-2 bg-blue-600 text-white rounded-lg">
                        {m.text}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="border-t p-3 flex space-x-2">
              <button
                onClick={offerOtherContact}
                className="px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded"
                title="Предложить контакты"
              >
                Отправить соцсети
              </button>
              <input
                className="flex-1 border rounded px-3 py-2 bg-white dark:bg-gray-800"
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && send()}
                placeholder="Введите сообщение…"
              />
              <button
                onClick={() => send()}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded"
              >
                ➤
              </button>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
