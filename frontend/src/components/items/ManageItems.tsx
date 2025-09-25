import React from 'react';
import { Item, Category } from '../../types/types';
import useSettings from '../../hooks/useSettings';

type Props = {
  items: Item[];
  categories: Category[];
  productCategoryFilter: string;
  setProductCategoryFilter: (v: string) => void;
  productSearchFilter: string;
  setProductSearchFilter: (v: string) => void;
  filterProducts: (items: Item[]) => Item[];
  editItem: (id: number) => void | Promise<void>;
  deleteItem: (id: number) => void | Promise<void>;
};

export default function ManageItems(props: Props) {
  const { formatPrice } = useSettings();
  const {
    items,
    categories,
    productCategoryFilter,
    setProductCategoryFilter,
    productSearchFilter,
    setProductSearchFilter,
    filterProducts,
    editItem,
    deleteItem,
  } = props;

  return (
    <div className="tab-content active">
      <div className="manage-items-content">
        <div className="filters-section">
          <h3>🔍 Filters</h3>
          <div className="filters-row">
            <div className="filter-group">
              <label htmlFor="category-filter">Category:</label>
              <select
                id="category-filter"
                value={productCategoryFilter}
                onChange={(e) => setProductCategoryFilter(e.target.value)}
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
              <label htmlFor="search-items">Search:</label>
              <input
                type="text"
                id="search-items"
                placeholder="Item name..."
                value={productSearchFilter}
                onChange={(e) => setProductSearchFilter(e.target.value)}
              />
            </div>
          </div>
        </div>

        <div className="items-list">
          <h3>📋 Items</h3>
          <div className="items-container">
            {filterProducts(items).map((item) => (
              <div key={item.id} className="item-card">
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
                <div className="item-name">{item.name}</div>
                <div className="item-price">
                  {formatPrice(item.price)} / {item.unit_name || 'no unit'}
                </div>
                <div className="item-category">{item.category_title || 'Unknown category'}</div>
                {item.description && <div className="item-description">{item.description}</div>}
                <div className="item-actions">
                  <button className="btn-edit" onClick={() => editItem(item.id)}>
                    ✏️ Edit
                  </button>
                  <button className="btn-delete" onClick={() => deleteItem(item.id)}>
                    🗑️ Delete
                  </button>
                </div>
              </div>
            ))}
            {filterProducts(items).length === 0 && <div className="loading">No items</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
