import React from 'react';
import { Category, Unit, AppImage } from '../../types/types';
import useSettings from '../../hooks/useSettings';

type Props = {
  categories: Category[];
  units: Unit[];
  images: AppImage[];
  selectedCategory: number | null;
  handleCategorySelection: (categoryId: number) => void;
  selectedImage: number | null;
  selectImage: (imageId: number) => void;
  clearSelectedImage: () => void;
  createItem: (formData: Record<string, FormDataEntryValue>) => void | Promise<void>;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  galleryInputRef: React.RefObject<HTMLInputElement | null>;
  handleFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void | Promise<void>;
  handleGalleryUpload: (e: React.ChangeEvent<HTMLInputElement>) => void | Promise<void>;
};

export default function AddItem(props: Props) {
  const { currency_symbol } = useSettings();
  const {
    categories,
    units,
    images,
    selectedCategory,
    handleCategorySelection,
    selectedImage,
    selectImage,
    clearSelectedImage,
    createItem,
    fileInputRef,
    galleryInputRef,
    handleFileUpload,
    handleGalleryUpload,
  } = props;

  const onSubmit: React.FormEventHandler<HTMLFormElement> = (e) => {
    e.preventDefault();
    const form = e.currentTarget as HTMLFormElement;
    const formData = Object.fromEntries(new FormData(form).entries()) as Record<
      string,
      FormDataEntryValue
    >;
    createItem(formData);
  };

  return (
    <div className="tab-content active">
      <div className="add-item-layout">
        <div className="categories-section">
          <h3>📂 Select Category</h3>
          <div className="categories-listbox">
            <select
              size={8}
              onChange={(e) => {
                const value = parseInt(e.target.value);
                if (value > 0) {
                  handleCategorySelection(value);
                }
              }}
              value={selectedCategory || ''}
            >
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.title}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-section">
          <form onSubmit={onSubmit}>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="name">Item name *</label>
                <input type="text" id="name" name="name" required placeholder="" disabled={!selectedCategory} />
              </div>
              <div className="form-group">
                <label htmlFor="price">Price ({currency_symbol}) *</label>
                <input
                  type="number"
                  id="price"
                  name="price"
                  step="0.01"
                  min="0.01"
                  required
                  placeholder="0.00"
                  disabled={!selectedCategory}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="unit_id">Unit</label>
                <select id="unit_id" name="unit_id" disabled={!selectedCategory}>
                  <option value="">No unit</option>
                  {units.map((unit) => (
                    <option key={unit.id} value={unit.id}>
                      {unit.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="category_id">Category ID</label>
                <input
                  type="number"
                  id="category_id"
                  name="category_id"
                  required
                  readOnly
                  value={selectedCategory || ''}
                  disabled={!selectedCategory}
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="description">Description</label>
              <textarea
                id="description"
                name="description"
                rows={3}
                placeholder="Additional item description..."
                disabled={!selectedCategory}
              />
            </div>

            <div className="form-group">
              <label>Item image</label>
              <div className="image-upload-section">
                <div className="upload-area">
                  <input
                    type="file"
                    accept="image/*"
                    capture="environment"
                    style={{ display: 'none' }}
                    ref={fileInputRef}
                    onChange={handleFileUpload}
                  />
                  <input
                    type="file"
                    accept="image/*"
                    style={{ display: 'none' }}
                    ref={galleryInputRef}
                    onChange={handleGalleryUpload}
                  />
                  <div className="upload-buttons">
                    <button
                      type="button"
                      className="upload-btn gallery-btn"
                      onClick={() => galleryInputRef.current?.click()}
                    >
                      📁 Upload image
                    </button>
                  </div>
                </div>

                <div className="image-gallery">
                  <h4>🖼️ Choose from uploaded</h4>
                  <div className="images-grid">
                    {images.length > 0 ? (
                      images.map((img) => (
                        <div
                          key={img.id}
                          className={`image-item ${selectedImage === img.id ? 'selected' : ''}`}
                          onClick={() => selectImage(img.id)}
                        >
                          <img src={img.url} alt={img.original_filename} />
                          <div className="image-overlay" />
                        </div>
                      ))
                    ) : (
                      <div className="no-images-message">
                        <p>No uploaded images</p>
                        <p>Upload images on the "Manage Images" tab</p>
                      </div>
                    )}
                  </div>
                </div>

                <input type="hidden" name="image_id" value={selectedImage || ''} />
                {selectedImage && (
                  <div className="selected-image-info">
                    <span>✅ Image selected</span>
                    <button type="button" className="clear-image-btn" onClick={clearSelectedImage}>
                      ❌ Remove
                    </button>
                  </div>
                )}
              </div>
            </div>

            <div className="form-actions">
              <button type="submit" className="btn" disabled={!selectedCategory}>
                Create
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
