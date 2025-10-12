import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

export default function HistoryPage() {
  const [data, setData] = useState(null);
  useEffect(() => {
    axios.get('/api/interactions/').then((r) => setData(r.data));
  }, []);

  if (!data) return <p className="p-8 text-center">Загрузка…</p>;

  const unreject = (id) =>
    axios.delete(`/api/interactions/${id}/unreject/`).then(() =>
      setData((d) => ({
        ...d,
        rejected: d.rejected.filter((u) => u.id !== id),
      })),
    );

  return (
    <div className="max-w-xl mx-auto p-6 text-gray-900 dark:text-gray-100">
      <h1 className="text-2xl font-bold mb-6">История взаимодействий</h1>

      <h2 className="text-xl font-semibold mb-3">Понравились:</h2>
      {data.liked.length ? (
        data.liked.map((u) => (
          <Link key={u.id} to={`/profile/${u.id}`} className="block mb-2 hover:text-emerald-500">
            {u.first_name} {u.last_name}
          </Link>
        ))
      ) : (
        <p className="mb-6 text-neutral-500">Пусто</p>
      )}

      <h2 className="text-xl font-semibold mb-3">Отклонены:</h2>
      {data.rejected.length ? (
        data.rejected.map((u) => (
          <div key={u.id} className="flex items-center justify-between mb-2">
            <Link to={`/profile/${u.id}`} className="hover:text-emerald-500">
              {u.first_name} {u.last_name}
            </Link>
            <button
              onClick={() => unreject(u.id)}
              className="px-3 py-1 text-sm bg-gray-600 hover:bg-gray-500 rounded text-white"
            >
              Вернуть
            </button>
          </div>
        ))
      ) : (
        <p className="mb-6 text-neutral-500">Пусто</p>
      )}
    </div>
  );
}
