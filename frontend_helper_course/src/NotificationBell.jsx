import { useEffect, useRef, useState } from 'react';
import { Bell, Check, X } from 'lucide-react';

export default function NotificationBell({ items = [], markRead }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    function handler(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false);
      }
    }

    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const unread = items.filter((i) => !i.read).length;

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="relative p-2 hover:bg-black/10 dark:hover:bg-white/10 rounded"
      >
        <Bell size={22} />
        {unread > 0 && (
          <span className="absolute -top-1 -right-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-600 text-xs">
            {unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-72 max-h-80 overflow-y-auto rounded bg-white dark:bg-neutral-800 shadow-md z-50">
          {items.length === 0 && <p className="p-4 text-sm text-neutral-500">Нет уведомлений</p>}

          {items.map((n) => (
            <div
              key={n.id}
              className="flex items-start gap-2 p-3 hover:bg-neutral-100 dark:hover:bg-neutral-700 border-b border-neutral-100 dark:border-neutral-700"
            >
              <span className="flex-1 text-sm">{n.text}</span>
              {!n.read && (
                <button
                  onClick={() => markRead(n.id)}
                  className="text-emerald-500 hover:text-emerald-400"
                  title="Отметить прочитанным"
                >
                  <Check size={16} />
                </button>
              )}
            </div>
          ))}

          {items.length > 0 && (
            <button
              onClick={() => markRead('all')}
              className="flex w-full items-center justify-center gap-1 py-2 text-xs text-neutral-500 hover:text-neutral-800 dark:hover:text-white"
            >
              <X size={14} /> Очистить все
            </button>
          )}
        </div>
      )}
    </div>
  );
}
