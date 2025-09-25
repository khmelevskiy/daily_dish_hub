import React from 'react';
import { AppImage } from '../../types/types';

type Props = {
  images: AppImage[];
  handleGalleryUpload: (e: React.ChangeEvent<HTMLInputElement>) => void | Promise<void>;
  deleteImage: (imageId: number) => void | Promise<void>;
  galleryInputRef: React.RefObject<HTMLInputElement | null>;
};

export default function ImageManager({ images, handleGalleryUpload, deleteImage, galleryInputRef }: Props) {
  return (
    <div className="tab-content active">
      <div className="manage-images-content">
        <div className="images-header">
          <h3>🖼️ Manage Images</h3>
          <button className="btn" onClick={() => galleryInputRef.current?.click()}>
            ➕ Upload Image
          </button>
          <input
            ref={galleryInputRef}
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            onChange={handleGalleryUpload}
          />
        </div>
        <div className="images-list">
          <h4>📋 Images ({images.length})</h4>
          <div className="images-grid-large">
            {images.map((img) => (
              <div key={img.id} className="image-card">
                <div className="image-preview">
                  <img src={img.url} alt={img.original_filename || 'image'} />
                </div>
                <div className="image-info">
                  <div className="image-name">{img.original_filename || `#${img.id}`}</div>
                  <div className="image-actions">
                    <button className="btn-delete" onClick={() => deleteImage(img.id)} title="Delete image">
                      🗑️ Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
            {images.length === 0 && <div className="loading">No uploaded images</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
