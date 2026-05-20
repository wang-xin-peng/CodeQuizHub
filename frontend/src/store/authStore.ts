import { create } from 'zustand';
import type { User } from '../types';
import * as authApi from '../api/auth';

const ACCOUNTS_KEY = 'auth_accounts';
const ACTIVE_ID_KEY = 'active_account_id';

interface StoredAccount {
  userId: string;
  email: string;
  token: string;
  user: User;
}

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  accounts: StoredAccount[];
  /** Login - adds to multi-account store. Keeps active token/user in simple keys. */
  login: (email: string, password: string) => Promise<void>;
  /** Logout - removes only the currently active account (keeps others intact). */
  logout: () => void;
  /** Switch to another logged-in account. */
  switchAccount: (userId: string) => void;
  /** Remove a specific account from the store. */
  removeAccount: (userId: string) => void;
  loadUser: () => void;
  setUser: (user: User) => void;
}

function loadAccounts(): StoredAccount[] {
  try {
    const raw = localStorage.getItem(ACCOUNTS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveAccounts(accounts: StoredAccount[]) {
  localStorage.setItem(ACCOUNTS_KEY, JSON.stringify(accounts));
}

function setActiveCredentials(token: string, user: User) {
  localStorage.setItem('token', token);
  localStorage.setItem('user', JSON.stringify(user));
  localStorage.setItem(ACTIVE_ID_KEY, user.id);
}

function clearActiveCredentials() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  localStorage.removeItem(ACTIVE_ID_KEY);
}

function findOrMigrateLegacyAccount(): StoredAccount | null {
  const token = localStorage.getItem('token');
  const rawUser = localStorage.getItem('user');
  if (!token || !rawUser) return null;
  try {
    const user = JSON.parse(rawUser) as User;
    return { userId: user.id, email: user.email, token, user };
  } catch {
    return null;
  }
}

export const useAuthStore = create<AuthState>((set, get) => {
  // Migration: if legacy account exists but no accounts array, migrate it
  let initialAccounts = loadAccounts();
  if (initialAccounts.length === 0) {
    const legacy = findOrMigrateLegacyAccount();
    if (legacy) {
      initialAccounts = [legacy];
      saveAccounts(initialAccounts);
    }
  }

  const activeId = localStorage.getItem(ACTIVE_ID_KEY);
  const activeAccount = activeId
    ? initialAccounts.find((a) => a.userId === activeId)
    : initialAccounts[initialAccounts.length - 1] || null;

  // Ensure the active account's token/user is always in the simple keys
  const initialUser: User | null = (() => {
    if (activeAccount) {
      setActiveCredentials(activeAccount.token, activeAccount.user);
      return activeAccount.user;
    }
    const stored = localStorage.getItem('user');
    return stored ? JSON.parse(stored) : null;
  })();
  const initialToken = activeAccount?.token || localStorage.getItem('token');

  return {
    user: initialUser,
    token: initialToken,
    loading: false,
    accounts: initialAccounts,

    login: async (email: string, password: string) => {
      set({ loading: true });
      try {
        const res = await authApi.login({ email, password });
        const { access_token, user } = res.data;

        const account: StoredAccount = {
          userId: user.id,
          email: user.email,
          token: access_token,
          user,
        };

        // Update accounts list: add or replace
        const accounts = get().accounts.filter((a) => a.userId !== user.id);
        accounts.push(account);
        saveAccounts(accounts);

        // Set as active
        setActiveCredentials(access_token, user);
        set({ user, token: access_token, accounts, loading: false });
      } catch (error) {
        set({ loading: false });
        throw error;
      }
    },

    logout: () => {
      const { user, accounts } = get();
      if (!user) return;

      // Remove current account from accounts list
      const filtered = accounts.filter((a) => a.userId !== user.id);
      saveAccounts(filtered);

      // If there are remaining accounts, activate the most recent one
      if (filtered.length > 0) {
        const next = filtered[filtered.length - 1];
        setActiveCredentials(next.token, next.user);
        set({ user: next.user, token: next.token, accounts: filtered });
      } else {
        clearActiveCredentials();
        set({ user: null, token: null, accounts: [] });
      }
    },

    switchAccount: (userId: string) => {
      const { accounts } = get();
      const account = accounts.find((a) => a.userId === userId);
      if (!account) return;

      setActiveCredentials(account.token, account.user);
      set({ user: account.user, token: account.token });
    },

    removeAccount: (userId: string) => {
      const { user, accounts } = get();
      const filtered = accounts.filter((a) => a.userId !== userId);
      saveAccounts(filtered);

      if (user?.id === userId) {
        // Switching away from the account being removed
        if (filtered.length > 0) {
          const next = filtered[filtered.length - 1];
          setActiveCredentials(next.token, next.user);
          set({ user: next.user, token: next.token, accounts: filtered });
        } else {
          clearActiveCredentials();
          set({ user: null, token: null, accounts: [] });
        }
      } else {
        set({ accounts: filtered });
      }
    },

    loadUser: () => {
      const accounts = loadAccounts();
      const activeId = localStorage.getItem(ACTIVE_ID_KEY);
      const activeAccount = activeId
        ? accounts.find((a) => a.userId === activeId)
        : accounts[accounts.length - 1] || null;

      if (activeAccount) {
        setActiveCredentials(activeAccount.token, activeAccount.user);
        set({ user: activeAccount.user, token: activeAccount.token, accounts });
      } else {
        const stored = localStorage.getItem('user');
        const token = localStorage.getItem('token');
        if (stored && token) {
          set({ user: JSON.parse(stored), token, accounts });
        }
      }
    },

    setUser: (user: User) => {
      const { accounts } = get();
      localStorage.setItem('user', JSON.stringify(user));
      // Also update in accounts list
      const updated = accounts.map((a) =>
        a.userId === user.id ? { ...a, user } : a
      );
      saveAccounts(updated);
      set({ user, accounts: updated });
    },
  };
});
