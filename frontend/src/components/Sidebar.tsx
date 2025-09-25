import React from 'react';

type Props = {
  activeTab: string;
  setActiveTab: (tab: string) => void;
};

export default function Sidebar({ activeTab, setActiveTab }: Props) {
  return (
    <div className="sidebar">
      <div className="nav-tabs">
        <div className="nav-item">
          <button
            className={`nav-link ${activeTab === 'manage-menu' ? 'active' : ''}`}
            onClick={() => setActiveTab('manage-menu')}
          >
            📋 Manage Menu
          </button>
        </div>
        <div className="nav-item">
          <button
            className={`nav-link ${activeTab === 'add-item' ? 'active' : ''}`}
            onClick={() => setActiveTab('add-item')}
          >
            ✨ Add Item
          </button>
        </div>
        <div className="nav-item">
          <button
            className={`nav-link ${activeTab === 'manage-items' ? 'active' : ''}`}
            onClick={() => setActiveTab('manage-items')}
          >
            📝 Manage Items
          </button>
        </div>
        <div className="nav-item">
          <button
            className={`nav-link ${activeTab === 'manage-categories' ? 'active' : ''}`}
            onClick={() => setActiveTab('manage-categories')}
          >
            📂 Manage Categories
          </button>
        </div>
        <div className="nav-item">
          <button
            className={`nav-link ${activeTab === 'manage-units' ? 'active' : ''}`}
            onClick={() => setActiveTab('manage-units')}
          >
            📏 Manage Units
          </button>
        </div>
        <div className="nav-item">
          <button
            className={`nav-link ${activeTab === 'manage-images' ? 'active' : ''}`}
            onClick={() => setActiveTab('manage-images')}
          >
            🖼️ Manage Images
          </button>
        </div>
      </div>
    </div>
  );
}
