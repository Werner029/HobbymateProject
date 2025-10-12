import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useLocation, useNavigate } from 'react-router-dom';
import { useKeycloak } from '@react-keycloak/web';

export default function Profile() {
  const { keycloak } = useKeycloak();
  const navigate = useNavigate();
  const location = useLocation();
  const returnTo = location.state?.returnTo || '/';
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState({});
  const [ratings, setRatings] = useState([]);
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const initForm = (d) => {
    setForm({
      first_name: d.first_name || '',
      last_name: d.last_name || '',
      phone_number: d.phone_number || '',
      date_of_birth: d.date_of_birth || '',
      bio: d.bio || '',
      tg_link: d.tg_link || '',
      vk_link: d.vk_link || '',
      profile_photo: null,
      is_offline: d.is_offline ?? false,
      is_can_write: d.is_can_write ?? true,
      city_name: d.city_name || '',
      privacy: d.privacy_settings_vector || Array(9).fill(1),
    });
  };

  const initRatings = (d) => {
    setRatings(
      Array.isArray(d.interests_ratings) && d.interests_ratings.length
        ? d.interests_ratings
        : Array.from({ length: 15 }, (_, i) => ({
            interest_id: i + 1,
            interest_name: `Интерес ${i + 1}`,
            rating: d.interests_ratings?.[i]?.rating || 1,
          })),
    );
  };

  useEffect(() => {
    if (!keycloak.authenticated) return;
    axios
      .get('/api/profile/me/')
      .then(({ data }) => {
        setProfile(data);
        initForm(data);
        initRatings(data);
        setEditing(!data.first_name || !data.last_name);
      })
      .catch(() => setEditing(true))
      .finally(() => setLoading(false));
  }, [keycloak]);

  if (loading) return <div className="p-8 text-center">Загрузка профиля…</div>;

  const handleChange = (e) => {
    const { name, type, value, checked, files } = e.target;
    setForm({
      ...form,
      [name]: type === 'file' ? files[0] : type === 'checkbox' ? checked : value,
    });
  };
  const togglePrivacy = (idx) => {
    setForm((f) => ({
      ...f,
      privacy: f.privacy.map((v, i) => (i === idx ? +!v : v)),
    }));
  };
  const handleRating = (id, val) => {
    setRatings(ratings.map((r) => (r.interest_id === id ? { ...r, rating: val } : r)));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    const fd = new FormData();
    Object.entries(form).forEach(([k, v]) => {
      if (k !== 'privacy' && v !== null && v !== undefined) fd.append(k, v);
    });
    fd.append('privacy_settings_vector', JSON.stringify(form.privacy));
    fd.append(
      'interests_ratings',
      JSON.stringify(
        ratings.map((r) => ({
          interest_id: r.interest_id,
          rating: r.rating,
        })),
      ),
    );
    try {
      const { data: upd } = await axios.patch('/api/profile/me/', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setProfile(upd);
      setEditing(false);
      navigate(returnTo, { replace: true });
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  const V = profile;
  return (
    <div className="container mx-auto py-8 px-4 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
      <h1 className="text-2xl font-bold mb-6">
        {editing ? 'Редактирование профиля' : 'Ваш профиль'}
      </h1>

      {!editing && V.profile_photo && (
        <img src={V.profile_photo} alt="" className="mb-6 w-32 h-32 rounded-full object-cover" />
      )}

      {!editing ? (
        <>
          <p className="dark:text-gray-200">
            <b>Имя:</b> {V.first_name} {V.last_name}
          </p>
          <p className="dark:text-gray-200">
            <b>Email:</b> {V.email}
          </p>
          <p className="dark:text-gray-200">
            <b>Телефон:</b> {V.phone_number || '-'}
          </p>
          <p className="dark:text-gray-200">
            <b>Дата рождения:</b> {V.date_of_birth || '-'}
          </p>
          <p className="dark:text-gray-200">
            <b>О себе:</b> {V.bio || '-'}
          </p>
          <p className="dark:text-gray-200">
            <b>Telegram:</b> {V.tg_link || '-'}
          </p>
          <p className="dark:text-gray-200">
            <b>VK:</b> {V.vk_link || '-'}
          </p>
          <p className="dark:text-gray-200">
            <b>Город:</b> {V.city_name || '-'}
          </p>
          <p className="dark:text-gray-200">
            <b>Общение оффлайн:</b> {V.is_offline ? 'Да' : 'Нет'}
          </p>
          <p className="dark:text-gray-200">
            <b>Личные сообщения:</b> {V.is_can_write ? 'Разрешены' : 'Запрещены'}
          </p>

          <h2 className="mt-6 font-semibold dark:text-gray-200">Рейтинги интересов:</h2>
          <ul className="list-disc ml-6 dark:text-gray-300">
            {ratings.map((r) => (
              <li key={r.interest_id}>
                {r.interest_name}: {r.rating}
              </li>
            ))}
          </ul>

          <button
            className="mt-6 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded"
            onClick={() => {
              initForm(profile);
              initRatings(profile);
              setEditing(true);
            }}
          >
            Редактировать
          </button>
        </>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4 max-w-lg">
          <div>
            <label className="block font-semibold mb-1 dark:text-gray-200">Email</label>
            <p className="border p-2 rounded bg-gray-100 dark:bg-gray-700 dark:text-gray-200">
              {V.email}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Email нельзя изменить</p>
          </div>

          {[
            { name: 'first_name', label: 'Имя', req: true },
            {
              name: 'last_name',
              label: 'Фамилия',
              req: true,
            },
            { name: 'phone_number', label: 'Телефон', type: 'tel' },
            {
              name: 'date_of_birth',
              label: 'Дата рождения',
              type: 'date',
            },
            { name: 'bio', label: 'О себе', as: 'textarea' },
            {
              name: 'tg_link',
              label: 'Telegram',
              plh: '@username',
            },
            { name: 'vk_link', label: 'VK ссылка', plh: 'https://vk.com/...' },
          ].map((f) => {
            const Tag = f.as || 'input';
            return (
              <div key={f.name}>
                <label className="block font-semibold mb-1 dark:text-gray-200">
                  {f.label}
                  {f.req && '*'}
                </label>
                <Tag
                  name={f.name}
                  type={f.type || 'text'}
                  placeholder={f.plh}
                  value={form[f.name] || ''}
                  onChange={handleChange}
                  required={f.req}
                  className="w-full border p-2 rounded text-gray-900 dark:text-gray-200 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            );
          })}

          <div>
            <label className="block font-semibold mb-1 dark:text-gray-200">Фото профиля</label>
            <input
              name="profile_photo"
              type="file"
              accept="image/*"
              onChange={handleChange}
              className="w-full text-gray-900 dark:text-gray-200"
            />
          </div>

          <div>
            <label className="block font-semibold mb-1 dark:text-gray-200">Город</label>
            <input
              name="city_name"
              type="text"
              placeholder="Введите ваш город"
              value={form.city_name || ''}
              onChange={handleChange}
              className="w-full border p-2 rounded text-gray-900 dark:text-gray-200 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <label className="flex items-center space-x-2">
            <input
              id="is_offline"
              name="is_offline"
              type="checkbox"
              checked={form.is_offline}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <span className="dark:text-gray-200">Общение оффлайн</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              id="is_can_write"
              name="is_can_write"
              type="checkbox"
              checked={form.is_can_write}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <span className="dark:text-gray-200">Принимать личные сообщения</span>
          </label>

          <h2 className="mt-6 font-semibold dark:text-gray-200">Конфиденциальность</h2>
          {[
            'Фото',
            'Email',
            'Телефон',
            'Дата рождения',
            'О себе',
            'Telegram',
            'VK',
            'Город',
            'Общение офлайн',
          ].map((l, i) => (
            <label key={i} className="flex items-center space-x-2 dark:text-gray-200">
              <input
                type="checkbox"
                checked={!!form.privacy[i]}
                onChange={() => togglePrivacy(i)}
                className="h-4 w-4"
              />
              <span>{l}</span>
            </label>
          ))}

          <h2 className="mt-6 font-semibold dark:text-gray-200">Рейтинги интересов</h2>
          {ratings.map((r) => (
            <div key={r.interest_id} className="mt-2">
              <p className="mb-1 dark:text-gray-300">{r.interest_name}</p>
              <div className="flex space-x-2">
                {[1, 2, 3, 4, 5].map((v) => (
                  <label key={v} className="flex items-center dark:text-gray-300">
                    <input
                      type="radio"
                      name={`rating-${r.interest_id}`}
                      checked={r.rating === v}
                      onChange={() => handleRating(r.interest_id, v)}
                      className="mr-1"
                    />
                    {v}
                  </label>
                ))}
              </div>
            </div>
          ))}

          <div className="flex space-x-3 mt-6">
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded flex-1"
            >
              {saving ? 'Сохранение...' : 'Сохранить'}
            </button>
            <button
              type="button"
              onClick={() => setEditing(false)}
              className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded flex-1"
            >
              Отмена
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
