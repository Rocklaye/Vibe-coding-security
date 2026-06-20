/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useEffect } from 'react';
import { Login } from './components/Login';
import { Feed } from './components/Feed';
import { Network } from './components/Network';
import { Messages } from './components/Messages';
import { Navbar } from './components/Navbar';

export default function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [currentUser, setCurrentUser] = useState<any>(JSON.parse(localStorage.getItem('user') || 'null'));
  const [currentMenu, setCurrentMenu] = useState('feed');

  const handleLogin = (newToken: string, user: any) => {
    setToken(newToken);
    setCurrentUser(user);
    localStorage.setItem('token', newToken);
    localStorage.setItem('user', JSON.stringify(user));
  };

  const handleLogout = () => {
    setToken(null);
    setCurrentUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  if (!token || !currentUser) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="min-h-screen bg-slate-100 font-sans">
      <Navbar 
        currentMenu={currentMenu} 
        setCurrentMenu={setCurrentMenu} 
        logout={handleLogout} 
        token={token} 
      />
      
      <main className="max-w-6xl mx-auto w-full">
        {currentMenu === 'feed' && <Feed token={token} />}
        {currentMenu === 'network' && <Network token={token} currentUser={currentUser} />}
        {currentMenu === 'messages' && <Messages token={token} currentUser={currentUser} />}
      </main>
    </div>
  );
}
