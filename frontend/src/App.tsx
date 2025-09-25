import React, { useState, useEffect, useCallback, useRef } from 'react';
import './App.css';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import LoginForm from './components/auth/LoginForm';
import ManageMenu from './components/menu/ManageMenu';
import AddItem from './components/items/AddItem';
import ManageItems from './components/items/ManageItems';
import CategoryManager from './components/categories/CategoryManager';
import UnitManager from './components/units/UnitManager';
import ImageManager from './components/images/ImageManager';
import ModalRoot from './components/modals/ModalRoot';
import { Item, Category, Unit, AppImage, User } from './types/types';
import {
  groupItemsByCategory,
  filterItems as filterItemsUtil,
  filterMenuItems as filterMenuItemsUtil,
  filterProducts as filterProductsUtil,
} from './utils/itemUtils';
import useAuth from './hooks/useAuth';
import useModal from './hooks/useModal';
import useImages from './hooks/useImages';
import useMenuHook from './hooks/useMenu';
import useCategoriesHook from './hooks/useCategories';
import useUnitsHook from './hooks/useUnits';
import * as api from './services/api';
import type { ApiError } from './services/api';

function App() {
  const { isAuthenticated, currentUser, isLoading, loginError, login, logout, checkAuth } = useAuth();

  const [activeTab, setActiveTab] = useState('manage-menu');

  const [availableItems, setAvailableItems] = useState<Item[]>([]);
  const { images, setImages, loadImages, upload: uploadImageSvc, remove: removeImageSvc } = useImages();
  const [loading, setLoading] = useState(true);
  const {
    localMenuItems,
    setLocalMenuItems,
    menuDateRange,
    setMenuDateRange,
    addToMenu: addToMenuHook,
    removeFromLocalMenu: removeFromLocalMenuHook,
    clear: clearMenuHook,
    loadMenuDate: loadMenuDateHook,
    saveMenuAndDate: saveMenuAndDateHook,
  } = useMenuHook({ showMessage: (t, m) => showModal(t, m) });
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [selectedImage, setSelectedImage] = useState<number | null>(null);
  const { modalContent, setModalContent, showModal, closeModal } = useModal();
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [searchFilter, setSearchFilter] = useState<string>('');
  const [menuCategoryFilter, setMenuCategoryFilter] = useState<string>('');
  const [menuSearchFilter, setMenuSearchFilter] = useState<string>('');

  const formatApiError = (error: unknown, fallback: string): string => {
    if (!error) return fallback;
    if (typeof error === 'string') return error;

    const formatDetailArray = (value: unknown): string | undefined => {
      if (!Array.isArray(value)) return undefined;
      return value
        .map((entry) => {
          if (entry && typeof entry === 'object') {
            const record = entry as Record<string, unknown>;
            const loc = Array.isArray(record.loc) ? record.loc.join('.') : record.loc;
            const msg = typeof record.msg === 'string' ? record.msg : String(record);
            return loc ? `${loc}: ${msg}` : msg;
          }
          return String(entry);
        })
        .join(', ');
    };

    if (error instanceof Error) {
      return error.message;
    }

    if (error && typeof error === 'object') {
      const record = error as Partial<ApiError> & Record<string, unknown>;
      const detailCandidate = record.detail ?? record.message;
      if (typeof detailCandidate === 'string' && detailCandidate.trim()) {
        return detailCandidate;
      }
      const arrayMessage = formatDetailArray(detailCandidate);
      if (arrayMessage) {
        return arrayMessage;
      }
    }

    return fallback;
  };
  const [productCategoryFilter, setProductCategoryFilter] = useState<string>('');
  const [productSearchFilter, setProductSearchFilter] = useState<string>('');
  const {
    categories,
    setCategories,
    loadCategories,
    orphanedItems,
    loadOrphaned,
    selectedOrphanedItems,
    toggleOrphanedItemSelection: toggleOrphanedItemSelectionHook,
    selectAllOrphanedItems: selectAllOrphanedItemsHook,
    clearOrphanedSelection: clearOrphanedSelectionHook,
    createCategory: createCategoryHook,
    updateCategory: updateCategoryHook,
    deleteCategoryAction: deleteCategoryActionHook,
    moveCategoryUp: moveCategoryUpHook,
    moveCategoryDown: moveCategoryDownHook,
    moveItemsToCategory: moveItemsToCategoryHook,
  } = useCategoriesHook({
    showMessage: (t, m) => showModal(t, m),
    setModalContent,
  });
  const {
    units,
    setUnits,
    loadUnits,
    noUnitItems,
    loadNoUnit,
    selectedNoUnitItems,
    toggleNoUnitItemSelection: toggleNoUnitItemSelectionHook,
    selectAllNoUnitItems: selectAllNoUnitItemsHook,
    clearNoUnitSelection: clearNoUnitSelectionHook,
    createUnit: createUnitHook,
    updateUnit: updateUnitHook,
    deleteUnitAction: deleteUnitActionHook,
    moveUnitUp: moveUnitUpHook,
    moveUnitDown: moveUnitDownHook,
    moveItemsToUnit: moveItemsToUnitHook,
  } = useUnitsHook({ showMessage: (t, m) => showModal(t, m), setModalContent });

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const galleryInputRef = useRef<HTMLInputElement | null>(null);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const uploadedImage = await uploadImageSvc(file);
      // Reload images from server to sync
      await loadImages();
      setSelectedImage(uploadedImage.id);
      alert('Image uploaded successfully!');
    } catch (error) {
      console.error('Error uploading image:', error);
      alert('Image upload error');
    }
  };

  const handleGalleryUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const uploadedImage = await uploadImageSvc(file);
      // Reload images from server to sync
      await loadImages();
      setSelectedImage(uploadedImage.id);
      alert('Image uploaded successfully!');
    } catch (error) {
      console.error('Error uploading image:', error);
      alert('Image upload error');
    }
  };

  const deleteImage = async (imageId: number) => {
    if (!window.confirm('Are you sure you want to delete this image?')) {
      return;
    }

    try {
      await removeImageSvc(imageId);
      // Reload images from server to sync
      await loadImages();
      if (selectedImage === imageId) {
        setSelectedImage(null);
      }
    } catch (error) {
      console.error('Error deleting image:', error);
      alert('Error deleting image');
    }
  };

  const loadData = useCallback(async () => {
    try {
      setLoading(true);

      // Load data depending on active tab
      if (activeTab === 'manage-menu') {
        const [menuData, availableData, categoriesData, unitsData] = await Promise.all([
          api.getDailyMenu(),
          api.getItems(),
          api.getCategories(),
          api.getUnits(),
        ]);

        setAvailableItems(availableData || []);
        setCategories(categoriesData || []);
        setUnits(unitsData || []);

        // Load local menu
        const localItems = [];
        for (const menuItem of menuData.items || []) {
          localItems.push({
            id: menuItem.id,
            item_id: menuItem.item_id,
            item: menuItem.item,
          });
        }
        setLocalMenuItems(localItems);

        // Load menu date
        await loadMenuDateHook();
      } else if (activeTab === 'add-item') {
        const [categoriesData, unitsData] = await Promise.all([api.getCategories(), api.getUnits()]);
        setCategories(categoriesData || []);
        setUnits(unitsData || []);
        // Load images for add item gallery
        await loadImages();
      } else if (activeTab === 'manage-items') {
        const [itemsData, categoriesData] = await Promise.all([api.getItems(), api.getCategories()]);
        setAvailableItems(itemsData || []);
        setCategories(categoriesData || []);
      } else if (activeTab === 'manage-categories') {
        const [categoriesData, itemsData] = await Promise.all([api.getCategories(), api.getItems()]);
        setCategories(categoriesData || []);
        setAvailableItems(itemsData || []);
        // Load orphaned items via hook
        await loadOrphaned();
      } else if (activeTab === 'manage-units') {
        const [unitsData, itemsData] = await Promise.all([api.getUnits(), api.getItems()]);
        setUnits(unitsData || []);
        setAvailableItems(itemsData || []);
        // Load no-unit items via hook
        await loadNoUnit();
      } else if (activeTab === 'manage-images') {
        await loadImages();
      }
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Menu handlers are provided by useMenuHook (addToMenuHook, removeFromLocalMenuHook, clearMenuHook)

  // Add item helpers
  const handleCategorySelection = (categoryId: number) => {
    setSelectedCategory(categoryId);
  };

  // Auto select first category when entering tab
  useEffect(() => {
    if (activeTab === 'add-item' && categories.length > 0 && selectedCategory === null) {
      setSelectedCategory(categories[0].id);
    }
  }, [activeTab, categories, selectedCategory]);

  const selectImage = (imageId: number) => {
    setSelectedImage(imageId);
  };

  const clearSelectedImage = () => {
    setSelectedImage(null);
  };

  const createItem = async (formData: Record<string, FormDataEntryValue>) => {
    const nameValue = formData['name'];
    const priceValue = formData['price'];
    const descriptionValue = formData['description'];
    const unitValue = formData['unit_id'];

    const requestData: Record<string, unknown> = {
      category_id: selectedCategory,
      name: typeof nameValue === 'string' ? nameValue : '',
      price: typeof priceValue === 'string' ? parseFloat(priceValue) || 0 : 0,
      description:
        typeof descriptionValue === 'string' && descriptionValue.trim().length > 0
          ? descriptionValue
          : null,
      unit_id:
        typeof unitValue === 'string' && unitValue.trim().length > 0
          ? parseInt(unitValue, 10)
          : null,
      image_id: selectedImage,
    };

    try {
      await api.createItem(requestData);
      showModal('Success', 'Item created!');
      setSelectedCategory(null);
      setSelectedImage(null);
      loadData();
    } catch (error) {
      const message = formatApiError(error, 'Error creating item');
      showModal('Error', `Error: ${message}`);
    }
  };

  // Item handlers
  const editItem = async (itemId: number) => {
    try {
      // Load item and images together
      const [item, imagesData] = await Promise.all([api.getItem(itemId), api.getImages()]);

      setSelectedImage(item.image_id || null);
      setImages(imagesData);
      setModalContent({ type: 'edit-item', data: item });
    } catch (error) {
      showModal('Error', 'Error loading item data: ' + (error as Error).message);
    }
  };

  const updateItem = async (itemId: number, formData: Record<string, unknown>) => {
    try {
      await api.updateItem(itemId, formData);
      showModal('Success', 'Item updated!');
      setModalContent(null);
      loadData();
    } catch (error) {
      const message = formatApiError(error, 'Error updating item');
      showModal('Error', message);
    }
  };

  const deleteItem = async (itemId: number) => {
    if (!window.confirm('Are you sure you want to delete this item?')) {
      return;
    }

    try {
      await api.deleteItem(itemId);
      showModal('Success', 'Item deleted!');
      loadData();
    } catch (error) {
      const message = formatApiError(error, 'Error deleting item');
      showModal('Error', message);
    }
  };

  // Category helpers
  const showAddCategoryModal = () => {
    setModalContent({ type: 'add-category' });
  };

  const editCategory = (categoryId: number, currentTitle: string) => {
    setModalContent({
      type: 'edit-category',
      data: { id: categoryId, title: currentTitle },
    });
  };

  const deleteCategory = (categoryId: number, categoryTitle: string) => {
    setModalContent({
      type: 'delete-category',
      data: { id: categoryId, title: categoryTitle },
    });
  };

  // Unit helpers
  const showAddUnitModal = () => {
    setModalContent({ type: 'add-unit' });
  };

  const editUnit = (unitId: number, currentName: string) => {
    setModalContent({
      type: 'edit-unit',
      data: { id: unitId, name: currentName },
    });
  };

  const deleteUnit = (unitId: number, unitName: string) => {
    setModalContent({
      type: 'delete-unit',
      data: { id: unitId, name: unitName },
    });
  };

  // Helper functions moved to utils/itemUtils

  // Check authorization on load
  useEffect(() => {
    checkAuth();
  }, []);

  // Login component moved to components/auth/LoginForm

  if (isLoading) {
    return <div className="loading">Checking authentication...</div>;
  }

  if (!isAuthenticated) {
    return <LoginForm onLogin={login} loginError={loginError} onSuccess={() => loadData()} />;
  }

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="app-container">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <div className="main-content">
        <Header currentUser={currentUser} onLogout={logout} />

        {/* Tab 1: Manage menu */}
        {activeTab === 'manage-menu' && (
          <ManageMenu
            categories={categories}
            availableItems={availableItems}
            localMenuItems={localMenuItems}
            menuDateRange={menuDateRange}
            menuCategoryFilter={menuCategoryFilter}
            setMenuCategoryFilter={setMenuCategoryFilter}
            menuSearchFilter={menuSearchFilter}
            setMenuSearchFilter={setMenuSearchFilter}
            categoryFilter={categoryFilter}
            setCategoryFilter={setCategoryFilter}
            searchFilter={searchFilter}
            setSearchFilter={setSearchFilter}
            setMenuDateRange={setMenuDateRange}
            groupItemsByCategory={(items) => groupItemsByCategory(items, categories)}
            filterMenuItems={(items) => filterMenuItemsUtil(items, menuCategoryFilter, menuSearchFilter)}
            filterItems={(items) => filterItemsUtil(items, categoryFilter, searchFilter)}
            addToMenu={addToMenuHook}
            removeFromLocalMenu={removeFromLocalMenuHook}
            saveMenuAndDate={saveMenuAndDateHook}
            clearDailyMenu={clearMenuHook}
          />
        )}

        {/* Tab 2: Add item */}
        {activeTab === 'add-item' && (
          <AddItem
            categories={categories}
            units={units}
            images={images}
            selectedCategory={selectedCategory}
            handleCategorySelection={handleCategorySelection}
            selectedImage={selectedImage}
            selectImage={selectImage}
            clearSelectedImage={clearSelectedImage}
            createItem={createItem}
            fileInputRef={fileInputRef}
            galleryInputRef={galleryInputRef}
            handleFileUpload={handleFileUpload}
            handleGalleryUpload={handleGalleryUpload}
          />
        )}

        {/* Tab 3: Manage items */}
        {activeTab === 'manage-items' && (
          <ManageItems
            items={availableItems}
            categories={categories}
            productCategoryFilter={productCategoryFilter}
            setProductCategoryFilter={setProductCategoryFilter}
            productSearchFilter={productSearchFilter}
            setProductSearchFilter={setProductSearchFilter}
            filterProducts={(items) => filterProductsUtil(items, productCategoryFilter, productSearchFilter)}
            editItem={editItem}
            deleteItem={deleteItem}
          />
        )}

        {/* Tab 4: Manage categories */}
        {activeTab === 'manage-categories' && (
          <CategoryManager
            categories={categories}
            availableItems={availableItems}
            orphanedItems={orphanedItems}
            selectedOrphanedItems={selectedOrphanedItems}
            showAddCategoryModal={showAddCategoryModal}
            editCategory={editCategory}
            deleteCategory={deleteCategory}
            moveCategoryUp={moveCategoryUpHook}
            moveCategoryDown={moveCategoryDownHook}
            selectAllOrphanedItems={selectAllOrphanedItemsHook}
            clearOrphanedSelection={clearOrphanedSelectionHook}
            toggleOrphanedItemSelection={toggleOrphanedItemSelectionHook}
            moveItemsToCategory={moveItemsToCategoryHook}
          />
        )}

        {/* Tab 5: Manage units */}
        {activeTab === 'manage-units' && (
          <UnitManager
            units={units}
            noUnitItems={noUnitItems}
            availableItems={availableItems}
            selectedNoUnitItems={selectedNoUnitItems}
            showAddUnitModal={showAddUnitModal}
            editUnit={editUnit}
            deleteUnit={deleteUnit}
            moveUnitUp={moveUnitUpHook}
            moveUnitDown={moveUnitDownHook}
            selectAllNoUnitItems={selectAllNoUnitItemsHook}
            clearNoUnitSelection={clearNoUnitSelectionHook}
            toggleNoUnitItemSelection={toggleNoUnitItemSelectionHook}
            moveItemsToUnit={moveItemsToUnitHook}
          />
        )}

        {/* Tab 6: Manage images */}
        {activeTab === 'manage-images' && (
          <ImageManager
            images={images}
            galleryInputRef={galleryInputRef}
            handleGalleryUpload={handleGalleryUpload}
            deleteImage={deleteImage}
          />
        )}

        {/* Modals */}
        <ModalRoot
          modalContent={modalContent}
          closeModal={closeModal}
          createCategory={createCategoryHook}
          updateCategory={updateCategoryHook}
          deleteCategoryAction={deleteCategoryActionHook}
          createUnit={createUnitHook}
          updateUnit={updateUnitHook}
          deleteUnitAction={deleteUnitActionHook}
          updateItem={updateItem}
          categories={categories}
          units={units}
          images={images}
          selectedImage={selectedImage}
          setSelectedImage={setSelectedImage}
        />
      </div>
    </div>
  );
}

export default App;
