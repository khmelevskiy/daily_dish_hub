import { useState, useCallback, type Dispatch, type SetStateAction } from 'react';
import { Item, Unit } from '../types/types';
import * as api from '../services/api';
import type { ApiError } from '../services/api';
import type { ModalContent } from './useModal';

export default function useUnits(params: {
  showMessage: (t: string, m: string) => void;
  setModalContent: Dispatch<SetStateAction<ModalContent>>;
}) {
  const { showMessage, setModalContent } = params;
  const [units, setUnits] = useState<Unit[]>([]);
  const [noUnitItems, setNoUnitItems] = useState<Item[]>([]);
  const [selectedNoUnitItems, setSelectedNoUnitItems] = useState<number[]>([]);

  const loadUnits = useCallback(async () => {
    const data = await api.getUnits();
    setUnits(data || []);
  }, []);
  const loadNoUnit = useCallback(async () => {
    const data = await api.getItemsNoUnit();
    setNoUnitItems(data || []);
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

  const createUnit = useCallback(
    async (name: string) => {
      try {
        await api.createUnit(name);
        showMessage('Success', 'Unit created!');
        setModalContent(null);
        loadUnits();
      } catch (error) {
        showMessage('Error', formatError(error, 'Error creating unit'));
      }
    },
    [formatError, loadUnits, setModalContent, showMessage]
  );

  const updateUnit = useCallback(
    async (id: number, name: string) => {
      try {
        await api.updateUnit(id, name);
        showMessage('Success', 'Unit updated!');
        setModalContent(null);
        loadUnits();
      } catch (error) {
        showMessage('Error', formatError(error, 'Error updating unit'));
      }
    },
    [formatError, loadUnits, setModalContent, showMessage]
  );

  const deleteUnitAction = useCallback(
    async (id: number, keepItems: boolean) => {
      const result = await api.deleteUnit(id, keepItems);
      if (result?.message) {
        showMessage('Success', result.message);
        setModalContent(null);
        loadUnits();
        // If keeping items, reload the list of items without units
        if (keepItems) {
          loadNoUnit();
        }
      }
    },
    [loadUnits, loadNoUnit, setModalContent, showMessage]
  );

  const moveUnitUp = useCallback(
    async (id: number) => {
      await api.moveUnitUp(id);
      loadUnits();
    },
    [loadUnits]
  );
  const moveUnitDown = useCallback(
    async (id: number) => {
      await api.moveUnitDown(id);
      loadUnits();
    },
    [loadUnits]
  );

  const toggleNoUnitItemSelection = useCallback((itemId: number) => {
    setSelectedNoUnitItems((prev) => (prev.includes(itemId) ? prev.filter((id) => id !== itemId) : [...prev, itemId]));
  }, []);
  const selectAllNoUnitItems = useCallback(() => setSelectedNoUnitItems(noUnitItems.map((i) => i.id)), [noUnitItems]);
  const clearNoUnitSelection = useCallback(() => setSelectedNoUnitItems([]), []);

  const moveItemsToUnit = useCallback(
    async (unitId: number) => {
      if (selectedNoUnitItems.length === 0) {
        showMessage('Warning', 'Select items to move');
        return;
      }
      await api.moveNoUnitToUnit(unitId, selectedNoUnitItems);
      showMessage('Success', `Moved ${selectedNoUnitItems.length} items to the selected unit!`);
      setSelectedNoUnitItems([]);
      loadNoUnit();
    },
    [selectedNoUnitItems, loadNoUnit, showMessage]
  );

  return {
    units,
    setUnits,
    loadUnits,
    noUnitItems,
    loadNoUnit,
    selectedNoUnitItems,
    toggleNoUnitItemSelection,
    selectAllNoUnitItems,
    clearNoUnitSelection,
    createUnit,
    updateUnit,
    deleteUnitAction,
    moveUnitUp,
    moveUnitDown,
    moveItemsToUnit,
  };
}
