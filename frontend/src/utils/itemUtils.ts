import { Item, LocalMenuItem, Category } from '../types/types';

export const groupItemsByCategory = (items: Item[], categories: Category[] = []) => {
  const grouped: Record<string, Item[]> = {};
  items.forEach((item) => {
    const cat = item.category_title || 'Uncategorized';
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push(item);
  });

  // Sort items by name inside each category
  Object.keys(grouped).forEach((category) => {
    grouped[category].sort((a, b) => a.name.localeCompare(b.name));
  });

  // If categories are provided, sort the grouped object by category sort_order
  if (categories.length > 0) {
    const sortedGrouped: Record<string, Item[]> = {};

    // Create a map of category titles to sort_order
    const categorySortMap = new Map<string, number>();
    categories.forEach((cat) => {
      categorySortMap.set(cat.title, cat.sort_order);
    });

    // Sort categories by sort_order, with Uncategorized at the end
    const sortedCategories = Object.keys(grouped).sort((a, b) => {
      if (a === 'Uncategorized') return 1;
      if (b === 'Uncategorized') return -1;

      const sortOrderA = categorySortMap.get(a) ?? 9999;
      const sortOrderB = categorySortMap.get(b) ?? 9999;

      if (sortOrderA !== sortOrderB) {
        return sortOrderA - sortOrderB;
      }

      // If sort_order is the same, sort alphabetically
      return a.localeCompare(b);
    });

    // Rebuild the grouped object in the correct order
    sortedCategories.forEach((category) => {
      sortedGrouped[category] = grouped[category];
    });

    return sortedGrouped;
  }

  return grouped;
};

export const filterItems = (items: Item[], categoryFilter: string, searchFilter: string) => {
  return items.filter((item) => {
    const matchesCategory = !categoryFilter || item.category_title === categoryFilter;
    const matchesSearch =
      !searchFilter ||
      item.name.toLowerCase().includes(searchFilter.toLowerCase()) ||
      (item.description && item.description.toLowerCase().includes(searchFilter.toLowerCase()));
    return matchesCategory && matchesSearch;
  });
};

export const filterAvailableItems = (
  items: Item[],
  categoryFilter: string,
  searchFilter: string,
  menuItems: LocalMenuItem[],
) => {
  return items.filter((item) => {
    // Exclude items that are already in the menu
    const isInMenu = menuItems.some((menuItem) => menuItem.item_id === item.id);
    if (isInMenu) return false;

    // Apply normal filters
    const matchesCategory = !categoryFilter || item.category_title === categoryFilter;
    const matchesSearch =
      !searchFilter ||
      item.name.toLowerCase().includes(searchFilter.toLowerCase()) ||
      (item.description && item.description.toLowerCase().includes(searchFilter.toLowerCase()));
    return matchesCategory && matchesSearch;
  });
};

export const filterMenuItems = (items: Item[], menuCategoryFilter: string, menuSearchFilter: string) => {
  return items.filter((item) => {
    const matchesCategory = !menuCategoryFilter || item.category_title === menuCategoryFilter;
    const matchesSearch =
      !menuSearchFilter ||
      item.name.toLowerCase().includes(menuSearchFilter.toLowerCase()) ||
      (item.description && item.description.toLowerCase().includes(menuSearchFilter.toLowerCase()));
    return matchesCategory && matchesSearch;
  });
};

export const filterProducts = (items: Item[], productCategoryFilter: string, productSearchFilter: string) => {
  return items.filter((item) => {
    const matchesCategory = !productCategoryFilter || item.category_title === productCategoryFilter;
    const matchesSearch =
      !productSearchFilter ||
      item.name.toLowerCase().includes(productSearchFilter.toLowerCase()) ||
      (item.description && item.description.toLowerCase().includes(productSearchFilter.toLowerCase()));
    return matchesCategory && matchesSearch;
  });
};
