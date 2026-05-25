import { useState, useEffect } from 'react';
import { Input, InputNumber, Switch, Typography, Button } from 'antd';

const { TextArea } = Input;

export interface ParamDef {
  name: string;
  type: string;
  description?: string;
}

/**
 * Determine the best input widget based on type string.
 */
function getWidgetType(type?: string): 'number' | 'string' | 'boolean' | 'json' {
  if (!type) return 'json';
  // Pointer (*), array ([]), and template (<>) types are complex — use JSON editor
  if (type.includes('*') || type.includes('[') || type.includes('<') || type.includes('>')) {
    return 'json';
  }
  const t = type.toLowerCase().replace(/[^a-z0-9_]/g, '');
  if (['int', 'integer', 'int32', 'int64', 'float', 'double', 'float32', 'float64', 'number', 'long', 'short', 'byte'].includes(t)) {
    return 'number';
  }
  if (['str', 'string', 'text', 'char'].includes(t)) {
    return 'string';
  }
  if (['bool', 'boolean'].includes(t)) {
    return 'boolean';
  }
  return 'json';
}

function tryParseJson(text: string): Record<string, unknown> | null {
  try {
    const parsed = JSON.parse(text);
    if (typeof parsed === 'object' && parsed !== null && !Array.isArray(parsed)) {
      return parsed as Record<string, unknown>;
    }
    return null;
  } catch {
    return null;
  }
}

// ─── Single-parameter field ──────────────────────────────────────────

function ParamField({
  type,
  value,
  onChange,
}: {
  type?: string;
  value: unknown;
  onChange: (v: unknown) => void;
}) {
  const widget = getWidgetType(type);

  if (widget === 'number') {
    return (
      <InputNumber
        value={value as number | undefined}
        onChange={(v) => onChange(v ?? 0)}
        style={{ width: '100%' }}
        placeholder={`输入 ${type} 类型值`}
      />
    );
  }

  if (widget === 'string') {
    return (
      <Input
        value={value as string | undefined}
        onChange={(e) => onChange(e.target.value)}
        placeholder={`输入 ${type} 类型值`}
        style={{ width: '100%' }}
      />
    );
  }

  if (widget === 'boolean') {
    return <Switch checked={!!value} onChange={(v) => onChange(v)} />;
  }

  // JSON fallback for complex types (List, Dict, etc.)
  const [localText, setLocalText] = useState(() =>
    value !== undefined ? JSON.stringify(value, null, 2) : '',
  );
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    if (value !== undefined) {
      setLocalText(JSON.stringify(value, null, 2));
      setLocalError(null);
    }
  }, [value]);

  const handleBlur = () => {
    try {
      if (localText.trim() === '') {
        onChange(undefined);
        setLocalError(null);
        return;
      }
      const parsed = JSON.parse(localText);
      setLocalError(null);
      onChange(parsed);
    } catch {
      setLocalError('JSON 格式无效');
    }
  };

  return (
    <div>
      <TextArea
        rows={4}
        value={localText}
        onChange={(e) => setLocalText(e.target.value)}
        onBlur={handleBlur}
        placeholder={`输入 ${type} 类型的值（JSON）`}
        style={{ width: '100%' }}
        status={localError ? 'error' : undefined}
      />
      {localError && (
        <Typography.Text type="danger" style={{ fontSize: 12 }}>
          {localError}
        </Typography.Text>
      )}
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────

interface InputParamsEditorProps {
  value?: string;
  onChange?: (value: string) => void;
  parameters?: ParamDef[];
  placeholder?: string;
}

export default function InputParamsEditor({
  value,
  onChange,
  parameters,
  placeholder: customPlaceholder,
}: InputParamsEditorProps) {
  const hasParams = parameters && parameters.length > 0;
  const jsonPlaceholder = customPlaceholder || '{"nums": [2, 7, 11, 15], "target": 9}';

  // ── JSON fallback mode ──
  if (!hasParams) {
    // Format the JSON nicely
    const formatJson = () => {
      if (!value) return;
      try {
        const parsed = JSON.parse(value);
        onChange?.(JSON.stringify(parsed, null, 2));
      } catch {
        // ignore
      }
    };

    return (
      <div style={{ width: '100%' }}>
        <TextArea
          rows={4}
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          placeholder={jsonPlaceholder}
          style={{ width: '100%' }}
        />
        <Button type="link" size="small" onClick={formatJson} style={{ padding: 0, marginTop: 4 }}>
          格式化 JSON
        </Button>
      </div>
    );
  }

  // ── Parameter mode ──
  const parsed = value && value.trim() ? tryParseJson(value) : {};
  const obj = parsed || {};

  const handleParamChange = (paramName: string, paramValue: unknown) => {
    const newObj = { ...obj, [paramName]: paramValue };
    onChange?.(JSON.stringify(newObj));
  };

  return (
    <div style={{ width: '100%' }}>
      {parameters.map((param) => (
        <div key={param.name} style={{ marginBottom: 12 }}>
          <div style={{ marginBottom: 4, fontSize: 13, fontWeight: 500 }}>
            {param.name}{' '}
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              ({param.type})
              {param.description ? ` - ${param.description}` : ''}
            </Typography.Text>
          </div>
          <ParamField
            type={param.type}
            value={obj[param.name]}
            onChange={(v) => handleParamChange(param.name, v)}
          />
        </div>
      ))}
      {/* Show raw JSON toggle for debugging */}
      {value && value !== '{}' && (
        <details style={{ marginTop: 8 }}>
          <summary style={{ cursor: 'pointer', fontSize: 12, color: '#888' }}>查看原始 JSON</summary>
          <pre style={{ fontSize: 11, marginTop: 4, padding: 8, background: '#f5f5f5', borderRadius: 4, overflow: 'auto' }}>
            {value}
          </pre>
        </details>
      )}
    </div>
  );
}
