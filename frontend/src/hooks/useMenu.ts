import { useState, useCallback, Dispatch, SetStateAction } from 'react';
import * as api from '../services/api';
import { Item, LocalMenuItem } from '../types/types';

type MenuDateRangeState = {
  start_date: string;
  end_date: string;
};

type UseMenuReturn = {
  localMenuItems: LocalMenuItem[];
  setLocalMenuItems: Dispatch<SetStateAction<LocalMenuItem[]>>;
  menuDateRange: MenuDateRangeState;
  setMenuDateRange: Dispatch<SetStateAction<MenuDateRangeState>>;
  addToMenu: (itemId: number) => Promise<void>;
  removeFromLocalMenu: (menuItemId: number) => void;
  clear: () => Promise<void>;
  loadMenuDate: () => Promise<void>;
  saveMenuAndDate: () => Promise<void>;
};

export default function useMenu(params: { showMessage: (title: string, msg: string) => void }): UseMenuReturn {
  const { showMessage } = params;
  const [localMenuItems, setLocalMenuItems] = useState<LocalMenuItem[]>([]);
  const [menuDateRange, setMenuDateRange] = useState<MenuDateRangeState>({ start_date: '', end_date: '' });

  const addToMenu = useCallback(
    async (itemId: number) => {
      const item = await api.getItem(itemId);
      if (localMenuItems.some((mi) => mi.item_id === itemId)) {
        showMessage('Warning', 'This item is already in the menu');
        return;
      }
      setLocalMenuItems((prev) => [...prev, { id: Date.now(), item_id: itemId, item }]);
    },
    [localMenuItems, showMessage]
  );

  const removeFromLocalMenu = useCallback((menuItemId: number) => {
    setLocalMenuItems((prev) => prev.filter((i) => i.id !== menuItemId));
  }, []);

  const clear = useCallback(async () => {
    setLocalMenuItems([]);
    await api.clearDailyMenu();
    showMessage('Success', 'Menu cleared!');
  }, [showMessage]);

  const loadMenuDate = useCallback(async () => {
    const data = await api.getDailyMenuDate();
    setMenuDateRange({
      start_date: data.menu_date.start_date || '',
      end_date: data.menu_date.end_date || '',
    });
  }, []);

  const saveMenuAndDate = useCallback(async () => {
    await api.replaceDailyMenu(localMenuItems.map((i) => i.item_id));
    await api.setDailyMenuDate(menuDateRange);
    showMessage('Success', 'Menu and dates saved!');
  }, [localMenuItems, menuDateRange, showMessage]);

  return {
    localMenuItems,
    setLocalMenuItems,
    menuDateRange,
    setMenuDateRange,
    addToMenu,
    removeFromLocalMenu,
    clear,
    loadMenuDate,
    saveMenuAndDate,
  };
}
