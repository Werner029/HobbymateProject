import { Link, useNavigate } from 'react-router-dom';
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useKeycloak } from '@react-keycloak/web';
import FindPartnerButton from './FindPartnerButton';

function MatchCard({ user, onLike, onSkip, onDislike }) {
  return (
    <div className="w-80 bg-gray-800 text-white rounded-2xl p-6 shadow-lg flex flex-col items-center">
      <img
        src={user.profile_photo || '/default-avatar.png'}
        alt={`${user.first_name} ${user.last_name}`}
        className="w-32 h-32 rounded-full object-cover mb-4"
      />
      <h3 className="text-xl font-semibold mb-1">
        <Link to={`/profile/${user.id}`} className="hover:text-emerald-400 transition">
          {`${user.first_name} ${user.last_name}`}
        </Link>
      </h3>

      <div className="flex gap-4 mt-6">
        <button
          onClick={onDislike}
          className="w-12 h-12 rounded-full bg-red-600 hover:bg-red-500 text-2xl"
        >
          ×
        </button>
        <button
          onClick={onSkip}
          className="w-12 h-12 rounded-full bg-gray-600 hover:bg-gray-500 text-2xl"
        >
          ⇄
        </button>
        <button
          onClick={onLike}
          className="w-12 h-12 rounded-full bg-emerald-600 hover:bg-emerald-500 text-2xl"
        >
          ♥
        </button>
      </div>
    </div>
  );
}

function MatchDeck() {
  const [queue, setQueue] = useState([]);
  const [current, setCurrent] = useState(null);
  const [exhausted, setExh] = useState(false);
  const navigate = useNavigate();

  useEffect(loadMore, []);

  function loadMore() {
    axios
      .get('/api/matches/?limit=10')
      .then((r) => {
        setQueue((prev) => {
          const merged = [...prev, ...r.data];
          if (merged.length === 0) setExh(true);
          return merged;
        });
        setCurrent((c) => c ?? r.data[0] ?? null);
      })
      .catch(console.error);
  }

  async function swipe(action) {
    if (!current) return;
    try {
      const { data } = await axios.post(`/api/matches/${current.id}/swipe/`, {
        action,
      });
      if (action === 'like' && data.mutual && data.dialog_id) {
        navigate(`/dialogs/${data.dialog_id}`);
        return;
      }
    } catch (e) {
      console.error('Ошибка swipe:', e);
    } finally {
      const next = queue[1];
      setQueue((q) => q.slice(1));
      setCurrent(next);
      if (!next) loadMore();
    }
  }

  if (exhausted)
    return (
      <div className="text-center text-white space-y-4">
        <p>Все доступные кандидаты закончились.</p>
        <button
          onClick={() => {
            axios.post('/api/interactions/reset/').then(() => {
              setExh(false);
              loadMore();
            });
          }}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded"
        >
          Начать поиск заново
        </button>
      </div>
    );
  if (!current) return <p className="text-white">Поиск кандидатов…</p>;

  return (
    <MatchCard
      user={current}
      onLike={() => swipe('like')}
      onSkip={() => swipe('skip')}
      onDislike={() => swipe('dislike')}
    />
  );
}

export default function Home() {
  const { keycloak } = useKeycloak();
  const auth = keycloak?.authenticated;
  const [showDeck, setShowDeck] = useState(false);
  const [hello, setHello] = useState('');

  useEffect(() => {
    if (!auth) return;
    axios.get('/api/hello/').then((r) => setHello(r.data.message));
  }, [auth]);

  async function handleFind() {
    const { data: me } = await axios.get('/api/profile/me/');
    const goodInterests = me.interest_vector?.some((n) => n > 2);
    if (!goodInterests) {
      alert('Поставьте оценки интересам выше 2, чтобы начать поиск.');
      return;
    }
    setShowDeck(true);
  }

  return (
    <>
      <section className="min-h-screen flex flex-col justify-center items-center bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-center px-4">
        {auth && hello && <p className="mb-4 text-xl font-semibold text-emerald-500">{hello}</p>}

        {!auth ? (
          <GuestBlock onLogin={() => keycloak.login({ redirectUri: window.location.origin })} />
        ) : showDeck ? (
          <MatchDeck />
        ) : (
          <FindPartnerButton onFind={handleFind} />
        )}
      </section>

      {!auth && <PreviewSection />}
    </>
  );
}

function GuestBlock({ onLogin }) {
  return (
    <>
      <img src="/favicon-96x96.png" alt="HobbyMate logo" className="w-24 h-24 mb-6" />
      <h1 className="text-4xl font-bold mb-4 text-gray-900 dark:text-white">Добро пожаловать</h1>
      <p className="mb-8 text-gray-700 dark:text-neutral-300">
        Сервис <strong>HobbyMate</strong> подбирает собеседников по интересам.
      </p>
      <button
        onClick={onLogin}
        className="px-6 py-3 rounded bg-emerald-600 hover:bg-emerald-500 transition text-lg font-semibold text-white"
      >
        Войти
      </button>
    </>
  );
}

function PreviewSection() {
  return (
    <section className="bg-white dark:bg-gray-800 py-16 px-4">
      <div className="container mx-auto space-y-24">
        <PreviewRow
          imgSrc="/preview-dialogs.png"
          title="Мгновенные диалоги"
          text="Общайтесь с подходящими собеседниками мгновенно — благодаря интеллектуальному подбору по интересам."
        />
        <PreviewRow
          imgSrc="/preview-groups.png"
          title="Интересные группы"
          text="Присоединяйтесь к тематическим группам по хобби, делитесь опытом и находите единомышленников."
          reverse
        />
        <PreviewRow
          imgSrc="/preview-support.png"
          title="Помощь всегда рядом"
          text="Наш чат поддержки быстро решит любые вопросы и подскажет, как пользоваться HobbyMate."
        />
      </div>
    </section>
  );
}

function PreviewRow({ imgSrc, title, text, reverse = false }) {
  return (
    <div
      className={`flex flex-col ${reverse ? 'md:flex-row-reverse' : 'md:flex-row'} items-center gap-8`}
    >
      <div className="w-full md:w-1/2">
        <img src={imgSrc} alt={title} className="w-full rounded shadow-lg" />
      </div>
      <div className="w-full md:w-1/2 text-center md:text-left">
        <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">{title}</h2>
        <p className="text-gray-700 dark:text-neutral-400">{text}</p>
      </div>
    </div>
  );
}
