import React from 'react';
import { User } from '../types/types';

type Props = {
  currentUser: User | null;
  onLogout: () => void;
};

export default function Header({ currentUser, onLogout }: Props) {
  return (
    <div className="header-actions">
      <button className="btn-view-menu" onClick={() => window.open('/', '_self')}>
        🍽️ VIEW MENU
      </button>
      <div className="user-info">
        <span>👤 {currentUser?.username}</span>
        <button className="btn-logout" onClick={onLogout}>
          🚪 Logout
        </button>
      </div>
    </div>
  );
}
