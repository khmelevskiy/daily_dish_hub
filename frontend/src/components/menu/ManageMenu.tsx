import React from 'react';
import { Item, Category, LocalMenuItem } from '../../types/types';
import TimeSpinner from '../ui/TimeSpinner';
import { filterAvailableItems } from '../../utils/itemUtils';
import useSettings from '../../hooks/useSettings';

type Props = {
  categories: Category[];
  availableItems: Item[];
  localMenuItems: LocalMenuItem[];
  menuDateRange: { start_date: string; end_date: string };
  menuCategoryFilter: string;
  setMenuCategoryFilter: (v: string) => void;
  menuSearchFilter: string;
  setMenuSearchFilter: (v: string) => void;
  categoryFilter: string;
  setCategoryFilter: (v: string) => void;
  searchFilter: string;
  setSearchFilter: (v: string) => void;
  setMenuDateRange: React.Dispatch<React.SetStateAction<{ start_date: string; end_date: string }>>;
  groupItemsByCategory: (items: Item[]) => Record<string, Item[]>;
  filterMenuItems: (items: Item[]) => Item[];
  filterItems: (items: Item[]) => Item[];
  addToMenu: (itemId: number) => void | Promise<void>;
  removeFromLocalMenu: (menuItemId: number) => void;
  saveMenuAndDate: () => void | Promise<void>;
  clearDailyMenu: () => void | Promise<void>;
};

export default function ManageMenu(props: Props) {
  const { formatPrice } = useSettings();
  const {
    categories,
    availableItems,
    localMenuItems,
    menuDateRange,
    menuCategoryFilter,
    setMenuCategoryFilter,
    menuSearchFilter,
    setMenuSearchFilter,
    categoryFilter,
    setCategoryFilter,
    searchFilter,
    setSearchFilter,
    setMenuDateRange,
    groupItemsByCategory,
    filterMenuItems,
    filterItems,
    addToMenu,
    removeFromLocalMenu,
    saveMenuAndDate,
    clearDailyMenu,
  } = props;

  return (
    <div className="tab-content active">
      <div className="manage-menu-content">
        <div className="menu-actions">
          <div className="menu-title">
            <span>🍽️ Today's Menu</span>
          </div>
          <div className="action-buttons">
            <button className="btn" onClick={saveMenuAndDate}>
              💾 Save Menu & Dates
            </button>
            <button className="btn-danger" onClick={clearDailyMenu}>
              🗑️ Clear Menu
            </button>
          </div>
        </div>

        <div className="menu-date-section">
          <h3>📅 Menu Date</h3>
          <div className="date-inputs">
            <div className="form-group">
              <label htmlFor="start-date">Start:</label>
              <div className="datetime-inputs">
                <input
                  type="date"
                  id="start-date"
                  value={menuDateRange.start_date.split(' ')[0] || ''}
                  onChange={(e) => {
                    const time = menuDateRange.start_date.split(' ')[1] || '10:00';
                    setMenuDateRange((prev) => ({
                      ...prev,
                      start_date: `${e.target.value} ${time}`,
                    }));
                  }}
                />
                <div className="time-input">
                  <TimeSpinner
                    value={parseInt(menuDateRange.start_date.split(' ')[1]?.split(':')[0] || '10')}
                    min={0}
                    max={23}
                    onChange={(hours) => {
                      const date = menuDateRange.start_date.split(' ')[0] || new Date().toISOString().split('T')[0];
                      const minutes = menuDateRange.start_date.split(' ')[1]?.split(':')[1] || '00';
                      setMenuDateRange((prev) => ({
                        ...prev,
                        start_date: `${date} ${hours.toString().padStart(2, '0')}:${minutes}`,
                      }));
                    }}
                    placeholder="10"
                  />
                  <span className="time-separator">:</span>
                  <TimeSpinner
                    value={parseInt(menuDateRange.start_date.split(' ')[1]?.split(':')[1] || '00')}
                    min={0}
                    max={59}
                    onChange={(minutes) => {
                      const date = menuDateRange.start_date.split(' ')[0] || new Date().toISOString().split('T')[0];
                      const hours = menuDateRange.start_date.split(' ')[1]?.split(':')[0] || '10';
                      setMenuDateRange((prev) => ({
                        ...prev,
                        start_date: `${date} ${hours}:${minutes.toString().padStart(2, '0')}`,
                      }));
                    }}
                    placeholder="00"
                  />
                </div>
              </div>
            </div>
            <div className="form-group">
              <label htmlFor="end-date">End:</label>
              <div className="datetime-inputs">
                <input
                  type="date"
                  id="end-date"
                  value={menuDateRange.end_date.split(' ')[0] || ''}
                  onChange={(e) => {
                    const time = menuDateRange.end_date.split(' ')[1] || '22:00';
                    setMenuDateRange((prev) => ({
                      ...prev,
                      end_date: `${e.target.value} ${time}`,
                    }));
                  }}
                />
                <div className="time-input">
                  <TimeSpinner
                    value={parseInt(menuDateRange.end_date.split(' ')[1]?.split(':')[0] || '22')}
                    min={0}
                    max={23}
                    onChange={(hours) => {
                      const date = menuDateRange.end_date.split(' ')[0] || new Date().toISOString().split('T')[0];
                      const minutes = menuDateRange.end_date.split(' ')[1]?.split(':')[1] || '00';
                      setMenuDateRange((prev) => ({
                        ...prev,
                        end_date: `${date} ${hours.toString().padStart(2, '0')}:${minutes}`,
                      }));
                    }}
                    placeholder="22"
                  />
                  <span className="time-separator">:</span>
                  <TimeSpinner
                    value={parseInt(menuDateRange.end_date.split(' ')[1]?.split(':')[1] || '00')}
                    min={0}
                    max={59}
                    onChange={(minutes) => {
                      const date = menuDateRange.end_date.split(' ')[0] || new Date().toISOString().split('T')[0];
                      const hours = menuDateRange.end_date.split(' ')[1]?.split(':')[0] || '22';
                      setMenuDateRange((prev) => ({
                        ...prev,
                        end_date: `${date} ${hours}:${minutes.toString().padStart(2, '0')}`,
                      }));
                    }}
                    placeholder="00"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="menu-content">
          <div className="menu-left">
            <h4>📋 Items in Menu</h4>
            <div className="menu-filters">
              <div className="filter-group">
                <label htmlFor="menu-items-category-filter">Category:</label>
                <select
                  id="menu-items-category-filter"
                  value={menuCategoryFilter}
                  onChange={(e) => setMenuCategoryFilter(e.target.value)}
                >
                  <option value="">All categories</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.title}>
                      {cat.title}
                    </option>
                  ))}
                </select>
              </div>
              <div className="filter-group">
                <label htmlFor="menu-items-search">Search:</label>
                <input
                  type="text"
                  id="menu-items-search"
                  placeholder="Item name..."
                  value={menuSearchFilter}
                  onChange={(e) => setMenuSearchFilter(e.target.value)}
                />
              </div>
            </div>
            <div className="menu-items-container">
              {localMenuItems.length === 0 ? (
                <div className="empty-state">
                  <p>🍽️ Menu is empty</p>
                  <p>Add items from the right list</p>
                </div>
              ) : (
                Object.entries(
                  groupItemsByCategory(filterMenuItems(localMenuItems.map((mi) => mi.item)))
                ).map(([category, items]) => (
                    <div key={category} className="category-group">
                      <h5 className="category-title">{category}</h5>
                      {items.map((item) => (
                        <div key={item.id} className="menu-item">
                          <div className="item-image">
                            {item.image_url ? (
                              <img
                                src={item.image_url}
                                alt={item.name}
                                onError={(e) => {
                                  const target = e.currentTarget as HTMLImageElement;
                                  target.style.display = 'none';
                                  const fallback = target.parentElement?.querySelector(
                                    '.image-fallback'
                                  ) as HTMLElement;
                                  if (fallback) fallback.style.display = 'flex';
                                }}
                              />
                            ) : null}
                            <span
                              className="image-fallback"
                              style={
                                {
                                  display: item.image_url ? 'none' : 'flex',
                                } as React.CSSProperties
                              }
                            >
                              🍽️
                            </span>
                          </div>
                          <div className="item-info">
                            <span className="item-name">{item.name}</span>
                            <span className="item-price">
                              {formatPrice(item.price)} / {item.unit_name || 'pcs'}
                            </span>
                            {item.description && <span className="item-description">{item.description}</span>}
                          </div>
                          <button
                            className="btn-remove"
                            onClick={() => {
                              const entry = localMenuItems.find((mi) => mi.item.id === item.id);
                              if (entry) {
                                removeFromLocalMenu(entry.id);
                              }
                            }}
                          >
                            ❌ Remove
                          </button>
                        </div>
                      ))}
                    </div>
                  )
                )
              )}
            </div>
          </div>

          <div className="menu-right">
            <h4>➕ Add to Menu</h4>
            <div className="add-menu-filters">
              <div className="filter-group">
                <label htmlFor="menu-category-filter">Category:</label>
                <select
                  id="menu-category-filter"
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                >
                  <option value="">All categories</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.title}>
                      {cat.title}
                    </option>
                  ))}
                </select>
              </div>
              <div className="filter-group">
                <label htmlFor="menu-search">Search:</label>
                <input
                  type="text"
                  id="menu-search"
                  placeholder="Item name..."
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                />
              </div>
            </div>

            <div className="available-items-container">
              {Object.entries(
                groupItemsByCategory(filterAvailableItems(availableItems, categoryFilter, searchFilter, localMenuItems))
              ).map(([category, items]: [string, Item[]]) => (
                <div key={category} className="category-group">
                  <h5 className="category-title">{category}</h5>
                  {items.map((item: Item) => (
                    <div key={item.id} className="available-item">
                      <div className="item-image">
                        {item.image_url ? (
                          <img
                            src={item.image_url}
                            alt={item.name}
                            onError={(e) => {
                              const target = e.currentTarget as HTMLImageElement;
                              target.style.display = 'none';
                              const fallback = target.parentElement?.querySelector('.image-fallback') as HTMLElement;
                              if (fallback) fallback.style.display = 'flex';
                            }}
                          />
                        ) : null}
                        <span
                          className="image-fallback"
                          style={
                            {
                              display: item.image_url ? 'none' : 'flex',
                            } as React.CSSProperties
                          }
                        >
                          🍽️
                        </span>
                      </div>
                      <div className="item-info">
                        <span className="item-name">{item.name}</span>
                        <span className="item-price">
                          {formatPrice(item.price)} / {item.unit_name || 'pcs'}
                        </span>
                        {item.description && <span className="item-description">{item.description}</span>}
                      </div>
                      <button className="btn-add" onClick={() => addToMenu(item.id)}>
                        ➕ Add
                      </button>
                    </div>
                  ))}
                </div>
              ))}
              {filterAvailableItems(availableItems, categoryFilter, searchFilter, localMenuItems).length === 0 && (
                <div className="empty-state">
                  <p>✅ All items already in the menu</p>
                  <p>or no items match the filters</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
