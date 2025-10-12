import axios from 'axios';

const api = axios.create({ baseURL: 'https://hobbymate.ru/api' });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('kc_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
export default api;
