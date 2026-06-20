import { useState, useEffect } from 'react';
import { Bell, Briefcase, MessageSquare, Users, User as UserIcon } from 'lucide-react';
import { Notification } from '../types';

export function Navbar({ currentMenu, setCurrentMenu, logout, token }: any) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showNotifs, setShowNotifs] = useState(false);

  useEffect(() => {
    const fetchNotifs = async () => {
      const res = await fetch('/api/notifications', { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) setNotifications(await res.json());
    };
    fetchNotifs();
    const interval = setInterval(fetchNotifs, 10000);
    return () => clearInterval(interval);
  }, [token]);

  const navItems = [
    { id: 'feed', icon: Briefcase, label: 'Accueil' },
    { id: 'network', icon: Users, label: 'Réseau' },
    { id: 'messages', icon: MessageSquare, label: 'Messagerie' },
  ];

  const unreadCount = notifications.filter(n => n.is_read === 0).length;

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center cursor-pointer" onClick={() => setCurrentMenu('feed')}>
              <div className="w-8 h-8 bg-blue-600 rounded text-white flex items-center justify-center font-bold text-xl">
                in
              </div>
            </div>
            <div className="hidden sm:ml-8 sm:flex sm:space-x-8">
              {navItems.map(item => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    onClick={() => setCurrentMenu(item.id)}
                    className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                      currentMenu === item.id 
                        ? 'border-blue-500 text-gray-900' 
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    }`}
                  >
                    <div className="flex flex-col items-center">
                      <Icon size={20} className="mb-1" />
                      <span className="text-[10px] uppercase hidden md:block">{item.label}</span>
                    </div>
                  </button>
                )
              })}
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="relative">
              <button 
                onClick={() => setShowNotifs(!showNotifs)}
                className="text-gray-500 hover:text-gray-700 p-2 relative flex flex-col items-center"
              >
                <Bell size={20} className="mb-1" />
                <span className="text-[10px] uppercase hidden md:block">Notifications</span>
                {unreadCount > 0 && (
                  <span className="absolute top-1 right-2 inline-flex items-center justify-center px-1.5 py-0.5 text-xs font-bold leading-none text-white transform translate-x-1/4 -translate-y-1/4 bg-red-600 rounded-full">
                    {unreadCount}
                  </span>
                )}
              </button>
              
              {showNotifs && (
                <div className="origin-top-right absolute right-0 mt-2 w-80 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-50">
                  <div className="py-2 p-4">
                    <h3 className="text-sm font-medium text-gray-900 border-b pb-2 mb-2">Notifications</h3>
                    <div className="space-y-3 max-h-64 overflow-y-auto">
                      {notifications.length > 0 ? notifications.map(notif => (
                        <div key={notif.id} className={`text-sm ${notif.is_read ? 'text-gray-500' : 'text-gray-900 font-medium'}`}>
                          <p>{notif.content}</p>
                          <span className="text-xs text-gray-400">{new Date(notif.created_at).toLocaleString()}</span>
                        </div>
                      )) : <p className="text-sm text-gray-500">Aucune notification.</p>}
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            <div className="border-l border-gray-200 h-6"></div>
            
            <button onClick={logout} className="text-sm text-red-600 hover:text-red-800 font-medium whitespace-nowrap">
              Déconnexion
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
