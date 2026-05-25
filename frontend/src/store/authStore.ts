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
  /** Login - adds to multi-account store. Keeps active token/user in sessionStorage (per-tab). */
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

// ── helpers: auth_accounts list (shared localStorage) ──

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

// ── helpers: active credentials (per-tab sessionStorage) ──

function setActiveCredentials(token: string, user: User) {
  sessionStorage.setItem('token', token);
  sessionStorage.setItem('user', JSON.stringify(user));
  sessionStorage.setItem(ACTIVE_ID_KEY, user.id);
}

function clearActiveCredentials() {
  sessionStorage.removeItem('token');
  sessionStorage.removeItem('user');
  sessionStorage.removeItem(ACTIVE_ID_KEY);
}

/** Try to read active credentials from sessionStorage. */
function readActiveCredentials(): { token: string | null; user: User | null } {
  const token = sessionStorage.getItem('token');
  const rawUser = sessionStorage.getItem('user');
  if (token && rawUser) {
    try {
      return { token, user: JSON.parse(rawUser) as User };
    } catch {
      // ignore corrupted data
    }
  }
  return { token: null, user: null };
}

export const useAuthStore = create<AuthState>((set, get) => {
  // ── Initialization (runs once when the store is first created) ──

  let initialAccounts = loadAccounts();

  // Migration from legacy single-account (pre-multi-account format)
  if (initialAccounts.length === 0) {
    const { token, user } = readActiveCredentials();
    if (token && user) {
      initialAccounts = [{ userId: user.id, email: user.email, token, user }];
      saveAccounts(initialAccounts);
    }
  }

  // Determine the active account for THIS tab from sessionStorage
  const activeId = sessionStorage.getItem(ACTIVE_ID_KEY);
  const activeAccount = activeId
    ? initialAccounts.find((a) => a.userId === activeId)
    : initialAccounts[initialAccounts.length - 1] || null;

  // The active user/token for this tab
  const { token: sessToken, user: sessUser } = readActiveCredentials();
  const initialUser = activeAccount?.user ?? sessUser;
  const initialToken = activeAccount?.token ?? sessToken;

  // If we found an active account, ensure sessionStorage matches
  if (activeAccount) {
    setActiveCredentials(activeAccount.token, activeAccount.user);
  }

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

        // Update accounts list: add or replace (shared localStorage)
        const accounts = get().accounts.filter((a) => a.userId !== user.id);
        accounts.push(account);
        saveAccounts(accounts);

        // Set as active in THIS tab's sessionStorage only
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
      const activeId = sessionStorage.getItem(ACTIVE_ID_KEY);
      const activeAccount = activeId
        ? accounts.find((a) => a.userId === activeId)
        : accounts[accounts.length - 1] || null;

      if (activeAccount) {
        setActiveCredentials(activeAccount.token, activeAccount.user);
        set({ user: activeAccount.user, token: activeAccount.token, accounts });
      } else {
        const { token, user } = readActiveCredentials();
        if (token && user) {
          set({ user, token, accounts });
        }
      }
    },

    setUser: (user: User) => {
      const { accounts } = get();
      sessionStorage.setItem('user', JSON.stringify(user));
      // Also update in accounts list
      const updated = accounts.map((a) =>
        a.userId === user.id ? { ...a, user } : a
      );
      saveAccounts(updated);
      set({ user, accounts: updated });
    },
  };
});
