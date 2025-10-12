import { useEffect, useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';

export default function GroupsPage() {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null);

  useEffect(() => {
    axios
      .get('/api/groups/me')
      .then((r) => setGroups(r.data))
      .finally(() => setLoading(false));
  }, []);

  const toggleMembers = (g) => {
    if (g.members)
      return setGroups((s) => s.map((x) => (x.id === g.id ? { ...x, open: !x.open } : x)));
    axios.get(`/api/groups/${g.id}/members/`).then((r) => {
      setGroups((s) => s.map((x) => (x.id === g.id ? { ...x, members: r.data, open: true } : x)));
    });
  };

  const saveGroup = async (id, name, description) => {
    await axios.patch(`/api/groups/${id}/`, { name, description });
    setGroups((s) => s.map((g) => (g.id === id ? { ...g, name, description } : g)));
    setEditing(null);
  };

  if (loading) return <p className="p-4">Загрузка…</p>;
  if (!groups.length)
    return (
      <div className="p-8 text-center text-gray-600 dark:text-gray-400">
        Ещё нет групп, в которых вы состоите.
      </div>
    );

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-2xl font-bold">Мои группы</h1>

      {groups.map((g) => (
        <div
          key={g.id}
          className="p-4 bg-white dark:bg-gray-800 border rounded-lg shadow-sm space-y-2"
        >
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">{g.name}</h2>
            <button
              onClick={() => setEditing(g)}
              className="px-3 py-1 bg-gray-600 hover:bg-gray-500 rounded text-white text-sm"
            >
              Изменить
            </button>
          </div>
          <p className="text-sm text-gray-500">Участников: {g.members_count}</p>
          {g.description && <p className="text-gray-700 dark:text-gray-300">{g.description}</p>}
          <div className="flex gap-3 mt-2">
            <Link
              to={`/dialogs/${g.chat_id}`}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded"
            >
              Перейти в чат
            </Link>
            <button
              onClick={() => toggleMembers(g)}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded"
            >
              {g.open ? 'Скрыть участников' : 'Участники'}
            </button>
          </div>
          {g.open && g.members && (
            <div className="mt-3 space-y-1">
              {g.members.map((m) => (
                <Link
                  key={m.user_id}
                  to={`/profile/${m.user_id}`}
                  className="block hover:text-emerald-400"
                >
                  {m.first_name} {m.last_name} {m.is_admin && '(админ)'}
                </Link>
              ))}
            </div>
          )}
        </div>
      ))}

      {editing && <EditModal group={editing} onClose={() => setEditing(null)} onSave={saveGroup} />}
    </div>
  );
}

function EditModal({ group, onClose, onSave }) {
  const [name, setName] = useState(group.name);
  const [desc, setDesc] = useState(group.description);
  const [saving, setSaving] = useState(false);
  const submit = async () => {
    setSaving(true);
    await onSave(group.id, name, desc);
    setSaving(false);
  };
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-neutral-800 p-6 rounded w-96 space-y-4">
        <h2 className="text-lg font-semibold text-white">Редактировать группу</h2>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full p-2 rounded bg-neutral-700 text-white"
        />
        <textarea
          value={desc || ''}
          onChange={(e) => setDesc(e.target.value)}
          rows={4}
          className="w-full p-2 rounded bg-neutral-700 text-white"
        />
        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 bg-gray-600 rounded text-white">
            Отмена
          </button>
          <button
            onClick={submit}
            disabled={saving}
            className="px-4 py-2 bg-emerald-600 rounded text-white"
          >
            {saving ? 'Сохранение…' : 'Сохранить'}
          </button>
        </div>
      </div>
    </div>
  );
}
