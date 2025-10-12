import { useEffect, useState } from 'react';
import axios from 'axios';

export default function SupportPage() {
  const [text, setText] = useState('');
  const [subs, setSubs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios
      .get('/api/feedback/')
      .then(({ data }) => setSubs(data))
      .finally(() => setLoading(false));
  }, []);

  const send = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    const { data } = await axios.post('/api/feedback/', { text });
    setSubs((s) => [data, ...s]);
    setText('');
  };

  return (
    <div className="p-4 max-w-lg mx-auto">
      <h1 className="text-2xl mb-4">Обратная связь</h1>

      <form onSubmit={send} className="space-y-2 mb-6">
        <textarea
          rows={4}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Ваш вопрос или отзыв…"
          className="
            w-full border rounded p-2 
            bg-white text-gray-900 
            dark:bg-gray-700 dark:text-gray-100
            focus:outline-none focus:ring
          "
        />
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Отправить
        </button>
      </form>

      <h2 className="text-xl mb-2">Мои обращения</h2>
      {loading ? (
        <p>Загрузка…</p>
      ) : subs.length === 0 ? (
        <p className="text-gray-500">Нет обращений</p>
      ) : (
        <ul className="space-y-4">
          {subs.map((f) => (
            <li key={f.id} className="border p-4 rounded bg-white dark:bg-gray-800">
              <p className="whitespace-pre-wrap">{f.text}</p>
              <p className="text-sm text-gray-500 mt-2">
                {new Date(f.created_at).toLocaleString()}
                {' — '}
                {f.is_answered ? 'Отвечено' : 'В ожидании'}
              </p>

              {f.is_answered && f.answer_text && (
                <div className="mt-3 p-3 bg-gray-100 dark:bg-gray-700 rounded">
                  <h3 className="font-semibold mb-1">Ответ администратора:</h3>
                  <p className="whitespace-pre-wrap">{f.answer_text}</p>
                  <p className="text-xs text-gray-500 mt-2">
                    {f.answered_by?.username}
                    {' • '}
                    {new Date(f.answered_at).toLocaleString()}
                  </p>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
