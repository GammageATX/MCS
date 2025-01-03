// Common interfaces shared between frontend and backend
export interface User {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'user';
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

// Add more shared types as needed 