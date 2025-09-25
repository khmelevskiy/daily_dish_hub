import React from 'react';
import { Category, Item } from '../../types/types';
import useSettings from '../../hooks/useSettings';

type Props = {
  categories: Category[];
  availableItems: Item[];
  orphanedItems: Item[];
  selectedOrphanedItems: number[];
  showAddCategoryModal: () => void;
  editCategory: (id: number, title: string) => void;
  deleteCategory: (id: number, title: string) => void;
  moveCategoryUp: (id: number) => void | Promise<void>;
  moveCategoryDown: (id: number) => void | Promise<void>;
  selectAllOrphanedItems: () => void;
  clearOrphanedSelection: () => void;
  toggleOrphanedItemSelection: (id: number) => void;
  moveItemsToCategory: (id: number) => void | Promise<void>;
};

export default function CategoryManager(props: Props) {
  const { formatPrice } = useSettings();
  const {
    categories,
    availableItems,
    orphanedItems,
    selectedOrphanedItems,
    showAddCategoryModal,
    editCategory,
    deleteCategory,
    moveCategoryUp,
    moveCategoryDown,
    selectAllOrphanedItems,
    clearOrphanedSelection,
    toggleOrphanedItemSelection,
    moveItemsToCategory,
  } = props;

  return (
    <div className="tab-content active">
      <div className="manage-categories-content">
        <div className="categories-header">
          <h3>📂 Manage Categories</h3>
          <button className="btn" onClick={showAddCategoryModal}>
            ➕ Add Category
          </button>
        </div>

        <div className="categories-list">
          <h4>📋 Categories</h4>
          <div className="categories-container">
            {categories.map((cat, index) => (
              <div key={cat.id} className="category-card">
                <div className="category-info">
                  <div className="category-name">{cat.title}</div>
                  <div className="category-stats">
                    Items: {availableItems.filter((item) => item.category_id === cat.id).length}
                  </div>
                </div>
                <div className="category-actions">
                  <div className="order-buttons">
                    <button
                      className="btn-order"
                      disabled={index === 0}
                      title="Move up"
                      onClick={() => moveCategoryUp(cat.id)}
                    >
                      ⬆️
                    </button>
                    <button
                      className="btn-order"
                      disabled={index === categories.length - 1}
                      title="Move down"
                      onClick={() => moveCategoryDown(cat.id)}
                    >
                      ⬇️
                    </button>
                  </div>
                  <button className="btn-edit" onClick={() => editCategory(cat.id, cat.title)}>
                    ✏️ Edit
                  </button>
                  <button className="btn-delete" onClick={() => deleteCategory(cat.id, cat.title)}>
                    🗑️ Delete
                  </button>
                </div>
              </div>
            ))}
            {categories.length === 0 && <div className="loading">No categories</div>}
          </div>
        </div>

        {orphanedItems.length > 0 && (
          <div className="orphaned-items-section">
            <div className="orphaned-header">
              <h4>⚠️ Items without category ({orphanedItems.length})</h4>
              <div className="selection-controls">
                <button
                  className="btn-small"
                  onClick={selectAllOrphanedItems}
                  disabled={selectedOrphanedItems.length === orphanedItems.length}
                >
                  Select all
                </button>
                <button
                  className="btn-small"
                  onClick={clearOrphanedSelection}
                  disabled={selectedOrphanedItems.length === 0}
                >
                  Clear selection
                </button>
                <span className="selection-info">
                  Selected: {selectedOrphanedItems.length} of {orphanedItems.length}
                </span>
              </div>
            </div>
            <div className="orphaned-items-container">
              {orphanedItems.map((item) => (
                <div
                  key={item.id}
                  className={`orphaned-item ${selectedOrphanedItems.includes(item.id) ? 'selected' : ''}`}
                  onClick={() => toggleOrphanedItemSelection(item.id)}
                >
                  <div className="item-checkbox">
                    <input
                      type="checkbox"
                      checked={selectedOrphanedItems.includes(item.id)}
                      onChange={() => toggleOrphanedItemSelection(item.id)}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </div>
                  <div className="item-info">
                    <div className="item-name">{item.name}</div>
                    <div className="item-price">
                      {formatPrice(item.price)} / {item.unit_name || 'no unit'}
                    </div>
                  </div>
                </div>
              ))}
              {selectedOrphanedItems.length > 0 && (
                <div className="orphaned-actions">
                  <p>Move selected items to category:</p>
                  <div className="category-selector">
                    <select
                      id="orphaned-category-select"
                      onChange={(e) => {
                        const categoryId = parseInt(e.target.value);
                        if (categoryId > 0) {
                          moveItemsToCategory(categoryId);
                          (e.target as HTMLSelectElement).value = '';
                        }
                      }}
                    >
                      <option value="">Select a category...</option>
                      {categories.map((cat) => (
                        <option key={cat.id} value={cat.id}>
                          {cat.title}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
