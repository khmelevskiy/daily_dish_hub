import { useState, useCallback, type Dispatch, type SetStateAction } from 'react';
import { Category, Item } from '../types/types';
import * as api from '../services/api';
import type { ApiError } from '../services/api';
import type { ModalContent } from './useModal';

export default function useCategories(params: {
  showMessage: (t: string, m: string) => void;
  setModalContent: Dispatch<SetStateAction<ModalContent>>;
}) {
  const { showMessage, setModalContent } = params;
  const [categories, setCategories] = useState<Category[]>([]);
  const [orphanedItems, setOrphanedItems] = useState<Item[]>([]);
  const [selectedOrphanedItems, setSelectedOrphanedItems] = useState<number[]>([]);

  const loadCategories = useCallback(async () => {
    const data = await api.getCategories();
    setCategories(data || []);
  }, []);

  const loadOrphaned = useCallback(async () => {
    const data = await api.getItemsOrphaned();
    setOrphanedItems(data || []);
  }, []);

  const formatError = useCallback((error: unknown, fallback: string) => {
    if (!error) return fallback;
    if (typeof error === 'string') return error;
    if (error instanceof Error) return error.message;
    if (error && typeof error === 'object') {
      const record = error as Partial<ApiError> & Record<string, unknown>;
      const detailCandidate = record.detail ?? record.message;
      if (typeof detailCandidate === 'string' && detailCandidate.trim()) {
        return detailCandidate;
      }
      if (Array.isArray(detailCandidate)) {
        return detailCandidate
          .map((entry) => {
            if (entry && typeof entry === 'object') {
              const detailRecord = entry as Record<string, unknown>;
              const loc = Array.isArray(detailRecord.loc) ? detailRecord.loc.join('.') : detailRecord.loc;
              const msg = typeof detailRecord.msg === 'string' ? detailRecord.msg : String(entry);
              return loc ? `${loc}: ${msg}` : msg;
            }
            return String(entry);
          })
          .join(', ');
      }
    }
    return fallback;
  }, []);

  const createCategory = useCallback(
    async (title: string) => {
      try {
        await api.createCategory(title);
        showMessage('Success', 'Category created!');
        setModalContent(null);
        loadCategories();
      } catch (error) {
        showMessage('Error', formatError(error, 'Error creating category'));
      }
    },
    [formatError, loadCategories, setModalContent, showMessage]
  );

  const updateCategory = useCallback(
    async (id: number, title: string) => {
      try {
        await api.updateCategory(id, title);
        showMessage('Success', 'Category updated!');
        setModalContent(null);
        loadCategories();
      } catch (error) {
        showMessage('Error', formatError(error, 'Error updating category'));
      }
    },
    [formatError, loadCategories, setModalContent, showMessage]
  );

  const deleteCategoryAction = useCallback(
    async (id: number, keepItems: boolean) => {
      const result = await api.deleteCategory(id, keepItems);
      if (result?.message) {
        showMessage('Success', result.message);
        setModalContent(null);
        loadCategories();
        // If keeping items, reload the list of items without a category
        if (keepItems) {
          loadOrphaned();
        }
      }
    },
    [loadCategories, loadOrphaned, setModalContent, showMessage]
  );

  const moveCategoryUp = useCallback(
    async (id: number) => {
      await api.moveCategoryUp(id);
      loadCategories();
    },
    [loadCategories]
  );

  const moveCategoryDown = useCallback(
    async (id: number) => {
      await api.moveCategoryDown(id);
      loadCategories();
    },
    [loadCategories]
  );

  const toggleOrphanedItemSelection = useCallback((itemId: number) => {
    setSelectedOrphanedItems((prev) =>
      prev.includes(itemId) ? prev.filter((id) => id !== itemId) : [...prev, itemId]
    );
  }, []);
  const selectAllOrphanedItems = useCallback(
    () => setSelectedOrphanedItems(orphanedItems.map((i) => i.id)),
    [orphanedItems]
  );
  const clearOrphanedSelection = useCallback(() => setSelectedOrphanedItems([]), []);

  const moveItemsToCategory = useCallback(
    async (categoryId: number) => {
      if (selectedOrphanedItems.length === 0) {
        showMessage('Warning', 'Select items to move');
        return;
      }
      await api.moveOrphanedToCategory(categoryId, selectedOrphanedItems);
      showMessage('Success', `Moved ${selectedOrphanedItems.length} items to the selected category!`);
      setSelectedOrphanedItems([]);
      loadOrphaned();
    },
    [selectedOrphanedItems, loadOrphaned, showMessage]
  );

  return {
    categories,
    setCategories,
    loadCategories,
    orphanedItems,
    loadOrphaned,
    selectedOrphanedItems,
    toggleOrphanedItemSelection,
    selectAllOrphanedItems,
    clearOrphanedSelection,
    createCategory,
    updateCategory,
    deleteCategoryAction,
    moveCategoryUp,
    moveCategoryDown,
    moveItemsToCategory,
  };
}
