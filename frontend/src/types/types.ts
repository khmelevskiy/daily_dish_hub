export interface Item {
  id: number;
  name: string;
  price: number;
  description?: string | null;
  category_id?: number | null;
  category_title?: string | null;
  unit_id?: number | null;
  unit_name?: string | null;
  image_id?: number | null;
  image_filename?: string | null;
  image_url?: string | null;
}

export interface Category {
  id: number;
  title: string;
  sort_order: number;
}

export interface Unit {
  id: number;
  name: string;
  sort_order: number;
}

export interface AppImage {
  id: number;
  original_filename: string;
  url: string;
  filename: string;
  file_size: number;
  mime_type: string;
  uploaded_at: string;
}

export interface User {
  id: number;
  username: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  last_login?: string;
}

export interface LocalMenuItem {
  id: number;
  item_id: number;
  item: Item;
}

export interface DailyMenuItemResponse {
  id: number;
  item_id: number;
  daily_menu_id: number;
  item: Item;
}

export interface DailyMenuResponse {
  id: number;
  created_at: string;
  items: DailyMenuItemResponse[];
}

export interface MenuDateInfo {
  start_date: string;
  end_date: string;
  current_date: string;
}

export interface MenuDateResponse {
  menu_date: MenuDateInfo;
}

export interface SuccessResponse<T = unknown> {
  message: string;
  data?: T;
}

export interface ItemListResponse {
  items: Item[];
  total: number;
}

export interface CategoryListResponse {
  categories: Category[];
  total: number;
}

export interface UnitListResponse {
  units: Unit[];
  total: number;
}

export interface ImageListResponse {
  images: AppImage[];
  total: number;
}
