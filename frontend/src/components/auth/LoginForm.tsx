import React, { useState } from 'react';

type Props = {
  onLogin: (username: string, password: string) => Promise<boolean>;
  onSuccess: () => void;
  loginError: string;
};

export default function LoginForm({ onLogin, onSuccess, loginError }: Props) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const success = await onLogin(username, password);
    if (success) {
      onSuccess();
    }
  };

  return (
    <div className="login-container">
      <div className="login-form">
        <h2>🔐 Admin Sign In</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username:</label>
            <input type="text" id="username" value={username} onChange={(e) => setUsername(e.target.value)} required />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password:</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {loginError && <div className="error-message">{loginError}</div>}
          <div className="login-buttons">
            <button type="submit" className="btn">
              Sign In
            </button>
            <button type="button" className="btn-secondary" onClick={() => (window.location.href = '/')}>
              📋 Menu
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
