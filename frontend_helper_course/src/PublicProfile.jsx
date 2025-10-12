import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import { useKeycloak } from '@react-keycloak/web';

export default function PublicProfile() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { keycloak } = useKeycloak();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    axios
      .get(`/api/profile/${id}/`)
      .then(({ data }) => setUser(data))
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, [id]);

  async function startPrivateChat() {
    setCreating(true);
    try {
      const { data: dialog } = await axios.post('/api/dialogs/', {
        partner: id,
      });
      navigate(`/dialogs/${dialog.id}`);
    } catch (err) {
      console.error('Не удалось создать диалог:', err);
      alert('Ошибка сервера, попробуйте позже.');
    } finally {
      setCreating(false);
    }
  }

  if (loading) return <div className="p-8 text-center">Загрузка профиля…</div>;
  if (!user) return <div className="p-8 text-center">Пользователь не найден</div>;
  const isMe = Number(id) === Number(keycloak.tokenParsed?.sub);

  return (
    <div className="container mx-auto py-8 px-4 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 max-w-lg">
      <h1 className="text-2xl font-bold mb-6">Профиль пользователя</h1>

      {user.profile_photo && (
        <img
          src={user.profile_photo}
          alt="Фото профиля"
          className="mb-6 w-32 h-32 rounded-full object-cover"
        />
      )}

      <p>
        <b>Имя:</b> {user.first_name} {user.last_name}
      </p>
      <p>
        <b>Email:</b> {user.email}
      </p>
      <p>
        <b>Телефон:</b> {user.phone_number || '—'}
      </p>
      <p>
        <b>Дата рождения:</b> {user.date_of_birth || '—'}
      </p>
      <p>
        <b>О себе:</b> {user.bio || '—'}
      </p>
      <p>
        <b>Telegram:</b> {user.tg_link || '—'}
      </p>
      <p>
        <b>VK:</b> {user.vk_link || '—'}
      </p>
      <p>
        <b>Город:</b> {user.city_name || '—'}
      </p>
      <p>
        <b>Общение офлайн:</b> {user.is_offline ? 'Да' : 'Нет'}
      </p>

      {!isMe && user.is_can_write && (
        <button
          onClick={startPrivateChat}
          disabled={creating}
          className="mt-8 px-6 py-3 rounded bg-emerald-600 hover:bg-emerald-500 transition text-lg font-semibold text-white disabled:opacity-50"
        >
          {creating ? 'Создаём чат…' : 'Написать лично'}
        </button>
      )}
    </div>
  );
}
