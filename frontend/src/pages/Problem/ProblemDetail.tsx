import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Button, Card, Descriptions, Divider, Input, Space, Spin, Tag,
  Typography, Tabs, message,
} from 'antd';
import { ArrowLeftOutlined, EditOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import * as problemsApi from '../../api/problems';
import type { Problem, FunctionSignature, TestCase } from '../../types';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

const LANGUAGE_LABELS: Record<string, string> = {
  python: 'Python',
  java: 'Java',
  c: 'C',
  cpp: 'C++',
};

const DIFFICULTY_META: Record<string, { color: string; label: string }> = {
  easy: { color: 'green', label: '简单' },
  medium: { color: 'orange', label: '中等' },
  hard: { color: 'red', label: '困难' },
};

const COMPARE_MODE_LABELS: Record<string, string> = {
  exact: '精确匹配',
  unordered: '无序匹配',
  float: '浮点精度匹配',
  custom: '自定义',
};

function SignatureTab({ sig }: { sig: FunctionSignature }) {
  return (
    <div>
      <Descriptions column={2} size="small" style={{ marginBottom: 12 }}>
        <Descriptions.Item label="函数名">{sig.function_name}</Descriptions.Item>
        <Descriptions.Item label="返回类型">{sig.return_type}</Descriptions.Item>
        <Descriptions.Item label="参数" span={2}>
          {sig.parameters_json?.length > 0 ? (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={{ border: '1px solid #d9d9d9', padding: '4px 8px', background: '#fafafa' }}>参数名</th>
                  <th style={{ border: '1px solid #d9d9d9', padding: '4px 8px', background: '#fafafa' }}>类型</th>
                  <th style={{ border: '1px solid #d9d9d9', padding: '4px 8px', background: '#fafafa' }}>说明</th>
                </tr>
              </thead>
              <tbody>
                {sig.parameters_json.map((p, idx) => (
                  <tr key={idx}>
                    <td style={{ border: '1px solid #d9d9d9', padding: '4px 8px' }}><Text code>{p.name}</Text></td>
                    <td style={{ border: '1px solid #d9d9d9', padding: '4px 8px' }}><Text code>{p.type}</Text></td>
                    <td style={{ border: '1px solid #d9d9d9', padding: '4px 8px' }}>{p.description || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <Text type="secondary">无参数</Text>
          )}
        </Descriptions.Item>
      </Descriptions>

      <Text strong>代码模板：</Text>
      <TextArea value={sig.code_template} readOnly rows={6} style={{ fontFamily: 'monospace', fontSize: 13, marginTop: 4 }} />

      {sig.prelude_code && (
        <>
          <Text strong style={{ display: 'block', marginTop: 8 }}>Prelude 代码：</Text>
          <TextArea value={sig.prelude_code} readOnly rows={4} style={{ fontFamily: 'monospace', fontSize: 13, marginTop: 4 }} />
        </>
      )}
    </div>
  );
}

function TestCaseCard({ tc, index }: { tc: TestCase; index: number }) {
  const inputStr = JSON.stringify(tc.input_params_json, null, 2);
  const outputStr = JSON.stringify(tc.expected_output_json, null, 2);

  return (
    <Card
      size="small"
      title={`用例 ${index + 1}`}
      style={{ marginBottom: 8 }}
      extra={tc.is_public ? <Tag color="blue">公开</Tag> : <Tag>隐藏</Tag>}
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        <div>
          <Text strong>输入：</Text>
          <TextArea value={inputStr} readOnly rows={2} style={{ fontFamily: 'monospace', fontSize: 13, marginTop: 2 }} />
        </div>
        <div>
          <Text strong>期望输出：</Text>
          <TextArea value={outputStr} readOnly rows={2} style={{ fontFamily: 'monospace', fontSize: 13, marginTop: 2 }} />
        </div>
        {tc.description && (
          <Text type="secondary">说明：{tc.description}</Text>
        )}
      </Space>
    </Card>
  );
}

export default function ProblemDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [problem, setProblem] = useState<Problem | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    problemsApi.getProblem(id)
      .then((res) => setProblem(res.data))
      .catch((err) => {
        message.error(err?.message || '加载题目失败');
        navigate('/problems');
      })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  }

  if (!problem) {
    return null;
  }

  const diffMeta = DIFFICULTY_META[problem.difficulty] || { color: 'default', label: problem.difficulty };
  const sigTabs = problem.signatures?.map((sig) => ({
    key: sig.language,
    label: LANGUAGE_LABELS[sig.language] || sig.language,
    children: <SignatureTab sig={sig} />,
  })) || [];

  const publicCases = problem.test_cases?.filter((tc) => tc.is_public) || [];
  const hiddenCases = problem.test_cases?.filter((tc) => !tc.is_public) || [];

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/problems')}>返回</Button>
          <Title level={4} style={{ margin: 0 }}>{problem.title}</Title>
          <Tag color={diffMeta.color}>{diffMeta.label}</Tag>
        </Space>
        <Button type="primary" icon={<EditOutlined />} onClick={() => navigate(`/problems/${id}/edit`)}>
          编辑题目
        </Button>
      </div>

      {/* Basic Info */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Descriptions column={4} size="small">
          <Descriptions.Item label="时间限制">{problem.time_limit}ms</Descriptions.Item>
          <Descriptions.Item label="内存限制">{problem.memory_limit}MB</Descriptions.Item>
          <Descriptions.Item label="比对模式">{COMPARE_MODE_LABELS[problem.compare_mode] || problem.compare_mode}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{new Date(problem.created_at).toLocaleString('zh-CN')}</Descriptions.Item>
        </Descriptions>
        <div style={{ marginTop: 8 }}>
          {problem.tags?.map((tag) => <Tag key={tag}>{tag}</Tag>)}
        </div>
      </Card>

      {/* Description */}
      <Card title="题目描述" size="small" style={{ marginBottom: 16 }}>
        <div className="markdown-body">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{problem.description}</ReactMarkdown>
        </div>
      </Card>

      {/* Function Signatures */}
      <Card title="函数签名" size="small" style={{ marginBottom: 16 }}>
        {sigTabs.length > 0 ? (
          <Tabs items={sigTabs} />
        ) : (
          <Text type="secondary">暂无函数签名</Text>
        )}
      </Card>

      {/* Test Cases */}
      <Card title="测试用例" size="small" style={{ marginBottom: 16 }}>
        {publicCases.length > 0 && (
          <>
            <Text strong style={{ display: 'block', marginBottom: 8 }}>公开用例</Text>
            {publicCases.map((tc, idx) => (
              <TestCaseCard key={tc.id || idx} tc={tc} index={tc.order || idx} />
            ))}
          </>
        )}
        {hiddenCases.length > 0 && (
          <>
            <Divider />
            <Text strong style={{ display: 'block', marginBottom: 8 }}>隐藏用例 ({hiddenCases.length} 个)</Text>
            {hiddenCases.map((tc, idx) => (
              <TestCaseCard key={tc.id || idx} tc={tc} index={tc.order || idx} />
            ))}
          </>
        )}
        {problem.test_cases?.length === 0 && (
          <Text type="secondary">暂无测试用例</Text>
        )}
      </Card>
    </div>
  );
}
