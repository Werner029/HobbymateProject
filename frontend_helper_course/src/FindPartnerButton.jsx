import { useState } from 'react';
import { Loader } from 'lucide-react';

export default function FindPartnerButton({ onFind }) {
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    setLoading(true);
    try {
      const ok = await onFind();
      if (!ok) {
        setLoading(false);
      }
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      className={`
        relative flex items-center justify-center
        w-48 h-48 rounded-full
        border-2 border-green-500
        text-green-500
        transition-colors duration-200
        ${
          loading
            ? 'cursor-wait bg-green-50 dark:bg-gray-800'
            : 'hover:bg-green-500 hover:text-white'
        }
      `}
    >
      {loading ? (
        <Loader className="animate-spin" size={48} />
      ) : (
        <span className="text-lg font-medium">Найти собеседника</span>
      )}
    </button>
  );
}
