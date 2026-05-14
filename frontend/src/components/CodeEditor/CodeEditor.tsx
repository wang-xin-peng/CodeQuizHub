import Editor from '@monaco-editor/react';

interface Props {
  value: string;
  language: string;
  onChange: (value: string) => void;
  readOnly?: boolean;
  height?: string;
}

const languageMap: Record<string, string> = {
  python: 'python',
  java: 'java',
  c: 'c',
  cpp: 'cpp',
};

export default function CodeEditor({ value, language, onChange, readOnly = false, height = '400px' }: Props) {
  const monacoLanguage = languageMap[language] || 'python';

  return (
    <Editor
      height={height}
      language={monacoLanguage}
      value={value}
      onChange={(val) => onChange(val || '')}
      theme="vs-dark"
      options={{
        readOnly,
        fontSize: 14,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        automaticLayout: true,
        tabSize: 4,
        wordWrap: 'on',
      }}
    />
  );
}
