import { useState, useCallback } from 'react';
import { AppImage } from '../types/types';
import * as api from '../services/api';

export default function useImages() {
  const [images, setImages] = useState<AppImage[]>([]);

  const loadImages = useCallback(async () => {
    const data = await api.getImages();
    setImages(data);
  }, []);

  const upload = useCallback(async (file: File) => {
    const uploaded = await api.uploadImage(file);
    setImages((prev) => [uploaded, ...prev]);
    return uploaded;
  }, []);

  const remove = useCallback(async (imageId: number) => {
    await api.deleteImage(imageId);
    setImages((prev) => prev.filter((i) => i.id !== imageId));
  }, []);

  return { images, setImages, loadImages, upload, remove };
}
