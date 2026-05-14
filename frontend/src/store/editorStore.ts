import { create } from 'zustand';
import type { TestResultItem } from '../types';

interface EditorState {
  code: string;
  language: string;
  isRunning: boolean;
  isSubmitting: boolean;
  testResults: TestResultItem[];
  compileError: string | null;
  setCode: (code: string) => void;
  setLanguage: (lang: string) => void;
  setRunning: (v: boolean) => void;
  setSubmitting: (v: boolean) => void;
  setTestResults: (results: TestResultItem[]) => void;
  setCompileError: (error: string | null) => void;
  reset: () => void;
}

export const useEditorStore = create<EditorState>((set) => ({
  code: '',
  language: 'python',
  isRunning: false,
  isSubmitting: false,
  testResults: [],
  compileError: null,

  setCode: (code) => set({ code }),
  setLanguage: (language) => set({ language }),
  setRunning: (isRunning) => set({ isRunning }),
  setSubmitting: (isSubmitting) => set({ isSubmitting }),
  setTestResults: (testResults) => set({ testResults, compileError: null }),
  setCompileError: (compileError) => set({ compileError, testResults: [] }),
  reset: () => set({ code: '', testResults: [], compileError: null, isRunning: false, isSubmitting: false }),
}));
