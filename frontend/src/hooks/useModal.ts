import { useState, useCallback } from 'react';
import type { Item } from '../types/types';

export type MessageModal = { type: 'message'; data: { title: string; message: string } };
export type AddCategoryModal = { type: 'add-category' };
export type EditCategoryModal = { type: 'edit-category'; data: { id: number; title: string } };
export type DeleteCategoryModal = { type: 'delete-category'; data: { id: number; title: string } };
export type AddUnitModal = { type: 'add-unit' };
export type EditUnitModal = { type: 'edit-unit'; data: { id: number; name: string } };
export type DeleteUnitModal = { type: 'delete-unit'; data: { id: number; name: string } };
export type EditItemModal = { type: 'edit-item'; data: Item };

export type ModalState =
  | MessageModal
  | AddCategoryModal
  | EditCategoryModal
  | DeleteCategoryModal
  | AddUnitModal
  | EditUnitModal
  | DeleteUnitModal
  | EditItemModal;

export type ModalContent = ModalState | null;

export default function useModal() {
  const [modalContent, setModalContent] = useState<ModalContent>(null);

  const showModal = useCallback((title: string, message: string) => {
    setModalContent({ type: 'message', data: { title, message } });
  }, []);

  const closeModal = useCallback(() => {
    setModalContent(null);
  }, []);

  return { modalContent, setModalContent, showModal, closeModal };
}
