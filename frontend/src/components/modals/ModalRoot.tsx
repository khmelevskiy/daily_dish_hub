import React, { useEffect, useMemo, useState } from 'react';
import { AppImage } from '../../types/types';
import type { ModalContent } from '../../hooks/useModal';

type Props = {
  modalContent: ModalContent;
  closeModal: () => void;
  createCategory: (title: string) => void | Promise<void>;
  updateCategory: (id: number, title: string) => void | Promise<void>;
  deleteCategoryAction: (id: number, keep: boolean) => void | Promise<void>;
  createUnit: (name: string) => void | Promise<void>;
  updateUnit: (id: number, name: string) => void | Promise<void>;
  deleteUnitAction: (id: number, keep: boolean) => void | Promise<void>;
  updateItem: (id: number, formData: Record<string, unknown>) => void | Promise<void>;
  categories?: Array<{ id: number; title: string }>;
  units?: Array<{ id: number; name: string }>;
  images?: AppImage[];
  selectedImage?: number | null;
  setSelectedImage?: (id: number | null) => void;
};

export default function ModalRoot(props: Props) {
  const {
    modalContent,
    closeModal,
    createCategory,
    updateCategory,
    deleteCategoryAction,
    createUnit,
    updateUnit,
    deleteUnitAction,
    updateItem,
    categories = [],
    units = [],
    images = [],
    selectedImage = null,
    setSelectedImage,
  } = props;

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      closeModal();
    }
  };

  const [newCategoryTitle, setNewCategoryTitle] = useState('');
  const [editCategoryTitle, setEditCategoryTitle] = useState('');
  const [newUnitName, setNewUnitName] = useState('');
  const [editUnitName, setEditUnitName] = useState('');

  const [itemName, setItemName] = useState('');
  const [itemPrice, setItemPrice] = useState<string>('');
  const [itemCategoryId, setItemCategoryId] = useState<string>('');
  const [itemUnitId, setItemUnitId] = useState<string>('');
  const [itemDescription, setItemDescription] = useState('');

  useEffect(() => {
    if (!modalContent) return;

    switch (modalContent.type) {
      case 'add-category':
        setNewCategoryTitle('');
        break;
      case 'edit-category':
        setEditCategoryTitle(modalContent.data.title || '');
        break;
      case 'add-unit':
        setNewUnitName('');
        break;
      case 'edit-unit':
        setEditUnitName(modalContent.data.name || '');
        break;
      case 'edit-item':
        setItemName(modalContent.data.name || '');
        setItemPrice(String(modalContent.data.price ?? ''));
        setItemCategoryId(modalContent.data.category_id ? String(modalContent.data.category_id) : '');
        setItemUnitId(modalContent.data.unit_id ? String(modalContent.data.unit_id) : '');
        setItemDescription(modalContent.data.description || '');
        break;
      default:
        break;
    }
  }, [modalContent]);

  const headerTitle = useMemo(() => {
    if (!modalContent) {
      return '';
    }
    switch (modalContent.type) {
      case 'message':
        return modalContent.data.title;
      case 'add-category':
        return 'Add Category';
      case 'edit-category':
        return 'Edit Category';
      case 'delete-category':
        return 'Delete Category';
      case 'add-unit':
        return 'Add Unit';
      case 'edit-unit':
        return 'Edit Unit';
      case 'delete-unit':
        return 'Delete Unit';
      case 'edit-item':
        return 'Edit Item';
      default:
        return '';
    }
  }, [modalContent]);

  if (!modalContent) return null;

  return (
    <div className="modal show" onClick={handleBackdropClick}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{headerTitle}</h3>
          <span className="close" onClick={closeModal}>
            &times;
          </span>
        </div>
        <div className="modal-body">
          {modalContent.type === 'message' && <p>{modalContent.data.message}</p>}

          {modalContent.type === 'add-category' && (
            <div>
              <p>Enter a new category name:</p>
              <div className="form-group">
                <label htmlFor="new-category-title">Category name</label>
                <input
                  type="text"
                  id="new-category-title"
                  placeholder="e.g. Soups"
                  value={newCategoryTitle}
                  onChange={(e) => setNewCategoryTitle(e.target.value)}
                />
              </div>
              <div className="modal-footer">
                <button
                  className="btn"
                  onClick={() => {
                    if (newCategoryTitle.trim()) createCategory(newCategoryTitle.trim());
                  }}
                >
                  Create
                </button>
                <button className="btn-secondary" onClick={closeModal}>
                  Cancel
                </button>
              </div>
            </div>
          )}

          {modalContent.type === 'edit-category' && (
            <div>
              <p>Edit category name:</p>
              <div className="form-group">
                <label htmlFor="edit-category-title">Category name</label>
                <input
                  type="text"
                  id="edit-category-title"
                  value={editCategoryTitle}
                  onChange={(e) => setEditCategoryTitle(e.target.value)}
                />
              </div>
              <div className="modal-footer">
                <button
                  className="btn"
                  onClick={() => {
                    if (editCategoryTitle.trim()) updateCategory(modalContent.data.id, editCategoryTitle.trim());
                  }}
                >
                  Save
                </button>
                <button className="btn-secondary" onClick={closeModal}>
                  Cancel
                </button>
              </div>
            </div>
          )}

          {modalContent.type === 'delete-category' && (
            <div>
              <p>
                Are you sure you want to delete category <strong>"{modalContent.data.title}"</strong>?
              </p>
              <p
                style={{
                  fontSize: '0.9rem',
                  color: '#6b7280',
                  marginTop: '10px',
                }}
              >
                Choose what to do with items in this category:
              </p>
              <div className="modal-footer">
                <button className="btn-danger" onClick={() => deleteCategoryAction(modalContent.data.id, false)}>
                  Delete category and items
                </button>
                <button className="btn" onClick={() => deleteCategoryAction(modalContent.data.id, true)}>
                  Delete category only
                </button>
                <button className="btn-secondary" onClick={closeModal}>
                  Cancel
                </button>
              </div>
            </div>
          )}

          {modalContent.type === 'add-unit' && (
            <div>
              <p>Enter a new unit name:</p>
              <div className="form-group">
                <label htmlFor="new-unit-name">Unit name</label>
                <input
                  type="text"
                  id="new-unit-name"
                  placeholder="e.g. portion"
                  value={newUnitName}
                  onChange={(e) => setNewUnitName(e.target.value)}
                />
              </div>
              <div className="modal-footer">
                <button
                  className="btn"
                  onClick={() => {
                    if (newUnitName.trim()) createUnit(newUnitName.trim());
                  }}
                >
                  Create
                </button>
                <button className="btn-secondary" onClick={closeModal}>
                  Cancel
                </button>
              </div>
            </div>
          )}

          {modalContent.type === 'edit-unit' && (
            <div>
              <p>Edit unit name:</p>
              <div className="form-group">
                <label htmlFor="edit-unit-name">Unit name</label>
                <input
                  type="text"
                  id="edit-unit-name"
                  value={editUnitName}
                  onChange={(e) => setEditUnitName(e.target.value)}
                />
              </div>
              <div className="modal-footer">
                <button
                  className="btn"
                  onClick={() => {
                    if (editUnitName.trim()) updateUnit(modalContent.data.id, editUnitName.trim());
                  }}
                >
                  Save
                </button>
                <button className="btn-secondary" onClick={closeModal}>
                  Cancel
                </button>
              </div>
            </div>
          )}

          {modalContent.type === 'delete-unit' && (
            <div>
              <p>
                Are you sure you want to delete unit <strong>"{modalContent.data.name}"</strong>?
              </p>
              <div className="modal-footer">
                <button className="btn-danger" onClick={() => deleteUnitAction(modalContent.data.id, false)}>
                  Delete unit and items
                </button>
                <button className="btn" onClick={() => deleteUnitAction(modalContent.data.id, true)}>
                  Delete unit only
                </button>
                <button className="btn-secondary" onClick={closeModal}>
                  Cancel
                </button>
              </div>
            </div>
          )}

          {modalContent.type === 'edit-item' && (
            <div>
              <div className="form-group">
                <label htmlFor="item-name">Item name</label>
                <input id="item-name" value={itemName} onChange={(e) => setItemName(e.target.value)} />
              </div>
              <div className="form-group">
                <label htmlFor="edit-item-price">Price</label>
                <input
                  id="edit-item-price"
                  type="number"
                  value={itemPrice}
                  onChange={(e) => setItemPrice(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label htmlFor="edit-item-category">Category</label>
                <select
                  id="edit-item-category"
                  value={itemCategoryId}
                  onChange={(e) => setItemCategoryId(e.target.value)}
                >
                  <option value="">Select a category</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.title}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="edit-item-unit">Unit</label>
                <select
                  id="edit-item-unit"
                  value={itemUnitId}
                  onChange={(e) => setItemUnitId(e.target.value)}
                >
                  <option value="">No unit</option>
                  {units.map((unit) => (
                    <option key={unit.id} value={unit.id}>
                      {unit.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="edit-item-description">Description</label>
                <textarea
                  id="edit-item-description"
                  value={itemDescription}
                  onChange={(e) => setItemDescription(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>Item image</label>
                <div className="image-upload-section">
                  <div className="image-gallery">
                    <h4>🖼️ Choose from uploaded</h4>
                    <div className="images-grid">
                      <div
                        className={`image-item ${selectedImage === null ? 'selected' : ''}`}
                        onClick={() => setSelectedImage && setSelectedImage(null)}
                      >
                        <div className="no-image-placeholder">
                          <span>❌ No image</span>
                        </div>
                      </div>
                      {images.map((img) => (
                        <div
                          key={img.id}
                          className={`image-item ${selectedImage === img.id ? 'selected' : ''}`}
                          onClick={() => setSelectedImage && setSelectedImage(img.id)}
                        >
                          <img src={img.url} alt={img.original_filename} />
                          <div className="image-overlay" />
                        </div>
                      ))}
                    </div>
                  </div>
                  {selectedImage && (
                    <div className="selected-image-info">
                      <span>✅ Image selected</span>
                      <button
                        type="button"
                        className="clear-image-btn"
                        onClick={() => setSelectedImage && setSelectedImage(null)}
                      >
                        ❌ Remove
                      </button>
                    </div>
                  )}
                </div>
              </div>
              <div className="modal-footer">
                <button
                  className="btn"
                  onClick={() => {
                    const formData = {
                      name: itemName,
                      price: parseFloat(itemPrice || '0'),
                      description: itemDescription || null,
                      category_id: itemCategoryId ? parseInt(itemCategoryId, 10) : null,
                      unit_id: itemUnitId ? parseInt(itemUnitId, 10) : null,
                      image_id: selectedImage,
                    };
                    updateItem(modalContent.data.id, formData);
                  }}
                >
                  Save
                </button>
                <button className="btn-secondary" onClick={closeModal}>
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
