import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { Button, Select, Space, Spin, Tabs, Tag, Typography, message } from 'antd';
import { PlayCircleOutlined, SendOutlined, UndoOutlined } from '@ant-design/icons';
import { useDebouncedCallback } from 'use-debounce';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import CodeEditor from '../../components/CodeEditor/CodeEditor';
import { useEditorStore } from '../../store/editorStore';
import * as problemsApi from '../../api/problems';
import * as submissionsApi from '../../api/submissions';
import type { Problem, TestResultItem } from '../../types';

const { Title, Text } = Typography;

export default function ProblemSolve() {
  const { assignmentId, problemId } = useParams<{ assignmentId: string; problemId: string }>();
  const [problem, setProblem] = useState<Problem | null>(null);
  const [loading, setLoading] = useState(true);
  const [availableLanguages, setAvailableLanguages] = useState<string[]>([]);
  const [initialTemplate, setInitialTemplate] = useState('');

  const {
    code, language, isRunning, isSubmitting, testResults, compileError,
    setCode, setLanguage, setRunning, setSubmitting, setTestResults, setCompileError,
  } = useEditorStore();

  // Load problem
  useEffect(() => {
    if (!problemId) return;
    setLoading(true);
    problemsApi.getProblem(problemId)
      .then((res) => {
        const p = res.data;
        setProblem(p);
        const langs = p.signatures?.map((s) => s.language) || [];
        setAvailableLanguages(langs);
        if (langs.length > 0) {
          setLanguage(langs[0]);
          const sig = p.signatures?.find((s) => s.language === langs[0]);
          if (sig) {
            setInitialTemplate(sig.code_template);
            setCode(sig.code_template);
          }
        }
      })
      .catch((err) => message.error(err?.message || '加载题目失败'))
      .finally(() => setLoading(false));
  }, [problemId]);

  // Load draft on mount and language change
  useEffect(() => {
    if (!problemId || !assignmentId || !language) return;
    submissionsApi.getDraft(problemId, { assignment_id: assignmentId, language })
      .then((res) => {
        if (res.data.code) {
          setCode(res.data.code);
        }
      })
      .catch(() => {});
  }, [problemId, assignmentId, language]);

  // Auto-save draft (debounced 3s)
  const debouncedSave = useDebouncedCallback((codeVal: string) => {
    if (!problemId || !assignmentId) return;
    submissionsApi.saveDraft({
      problem_id: problemId,
      assignment_id: assignmentId,
      language,
      code: codeVal,
    }).catch(() => {});
  }, 3000);

  const handleCodeChange = useCallback((val: string) => {
    setCode(val);
    debouncedSave(val);
  }, [language, problemId, assignmentId]);

  const handleLanguageChange = (lang: string) => {
    setLanguage(lang);
    const sig = problem?.signatures?.find((s) => s.language === lang);
    if (sig) {
      setInitialTemplate(sig.code_template);
      // Load draft for this language - if none, use template
      if (problemId && assignmentId) {
        submissionsApi.getDraft(problemId, { assignment_id: assignmentId, language: lang })
          .then((res) => {
            setCode(res.data.code || sig.code_template);
          })
          .catch(() => setCode(sig.code_template));
      } else {
        setCode(sig.code_template);
      }
    }
  };

  const handleReset = () => {
    setCode(initialTemplate);
    message.info('代码已重置');
  };

  const handleRun = async () => {
    if (!problemId || !assignmentId) return;
    setRunning(true);
    try {
      const res = await submissionsApi.runCode(problemId, {
        language,
        code,
        assignment_id: assignmentId,
      });
      if (res.data.compile_error) {
        setCompileError(res.data.compile_error);
      } else {
        setTestResults(res.data.results as TestResultItem[]);
      }
    } catch (err: any) {
      message.error(err?.message || '运行失败');
    } finally {
      setRunning(false);
    }
  };

  const handleSubmit = async () => {
    if (!problemId || !assignmentId) return;
    setSubmitting(true);
    try {
      const res = await submissionsApi.submitCode({
        assignment_id: assignmentId,
        problem_id: problemId,
        language,
        code,
      });
      message.success('提交成功，正在评测...');
      // Poll for result
      const submissionId = res.data.submission_id;
      pollResult(submissionId);
    } catch (err: any) {
      message.error(err?.message || '提交失败');
      setSubmitting(false);
    }
  };

  const pollResult = async (submissionId: string) => {
    const maxAttempts = 30;
    for (let i = 0; i < maxAttempts; i++) {
      await new Promise((r) => setTimeout(r, 2000));
      try {
        const res = await submissionsApi.getSubmission(submissionId);
        const s = res.data;
        if (s.status !== 'pending' && s.status !== 'judging') {
          setTestResults(s.results);
          if (s.status === 'accepted') {
            message.success(`通过! 得分: ${s.score}`);
          } else {
            message.warning(`结果: ${s.status}`);
          }
          setSubmitting(false);
          return;
        }
      } catch {
        break;
      }
    }
    setSubmitting(false);
    message.info('评测超时，请手动刷新查看结果');
  };

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  if (!problem) return <div>题目不存在</div>;

  const statusColors: Record<string, string> = {
    accepted: 'green',
    wrong_answer: 'red',
    time_limit_exceeded: 'orange',
    memory_limit_exceeded: 'orange',
    runtime_error: 'red',
    compilation_error: 'red',
  };
  const statusLabels: Record<string, string> = {
    accepted: 'AC',
    wrong_answer: 'WA',
    time_limit_exceeded: 'TLE',
    memory_limit_exceeded: 'MLE',
    runtime_error: 'RE',
    compilation_error: 'CE',
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top bar */}
      <div style={{ padding: '8px 16px', background: '#001529', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Space>
          <Title level={5} style={{ color: '#fff', margin: 0 }}>{problem.title}</Title>
          <Tag color={problem.difficulty === 'easy' ? 'green' : problem.difficulty === 'medium' ? 'orange' : 'red'}>
            {problem.difficulty === 'easy' ? '简单' : problem.difficulty === 'medium' ? '中等' : '困难'}
          </Tag>
        </Space>
        <Space>
          <Text style={{ color: '#ccc' }}>时间: {problem.time_limit}ms</Text>
          <Text style={{ color: '#ccc' }}>内存: {problem.memory_limit}MB</Text>
        </Space>
      </div>

      {/* Main content */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Left panel: problem description */}
        <div style={{ width: '40%', overflow: 'auto', padding: 16, borderRight: '1px solid #e8e8e8' }}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{problem.description}</ReactMarkdown>

          {problem.test_cases && problem.test_cases.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <Title level={5}>示例</Title>
              {problem.test_cases.filter((tc) => tc.is_public).map((tc, idx) => (
                <Card key={tc.id} size="small" style={{ marginBottom: 8 }}>
                  <Text strong>示例 {idx + 1}:</Text>
                  <pre style={{ background: '#f5f5f5', padding: 8, borderRadius: 4, marginTop: 4 }}>
                    输入: {JSON.stringify(tc.input_params_json, null, 2)}{'\n'}
                    输出: {JSON.stringify(tc.expected_output_json)}
                  </pre>
                  {tc.description && <Text type="secondary">{tc.description}</Text>}
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Right panel: editor + results */}
        <div style={{ width: '60%', display: 'flex', flexDirection: 'column' }}>
          {/* Language selector + reset */}
          <div style={{ padding: '8px 16px', borderBottom: '1px solid #e8e8e8', display: 'flex', justifyContent: 'space-between' }}>
            <Select
              value={language}
              onChange={handleLanguageChange}
              style={{ width: 120 }}
              options={availableLanguages.map((l) => ({ label: l.charAt(0).toUpperCase() + l.slice(1), value: l }))}
            />
            <Button icon={<UndoOutlined />} onClick={handleReset} size="small">重置代码</Button>
          </div>

          {/* Editor */}
          <div style={{ flex: 1, minHeight: 0 }}>
            <CodeEditor value={code} language={language} onChange={handleCodeChange} height="100%" />
          </div>

          {/* Results panel */}
          <div style={{ height: 200, overflow: 'auto', borderTop: '1px solid #e8e8e8', padding: 12 }}>
            <Tabs
              size="small"
              items={[
                {
                  key: 'results',
                  label: '测试结果',
                  children: (
                    <div>
                      {compileError && (
                        <pre style={{ color: 'red', whiteSpace: 'pre-wrap' }}>{compileError}</pre>
                      )}
                      {testResults.map((r, idx) => (
                        <div key={idx} style={{ marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
                          <Tag color={statusColors[r.status] || 'default'}>
                            {statusLabels[r.status] || r.status}
                          </Tag>
                          <Text>用例 {r.test_case_order + 1}</Text>
                          {r.time_used != null && <Text type="secondary">{r.time_used}ms</Text>}
                          {r.is_public && r.actual != null && (
                            <Text type="secondary">输出: {JSON.stringify(r.actual)}</Text>
                          )}
                        </div>
                      ))}
                      {!compileError && testResults.length === 0 && (
                        <Text type="secondary">点击"运行测试"查看结果</Text>
                      )}
                    </div>
                  ),
                },
              ]}
            />
          </div>

          {/* Bottom action bar */}
          <div style={{ padding: '8px 16px', borderTop: '1px solid #e8e8e8', display: 'flex', justifyContent: 'space-between' }}>
            <Button icon={<PlayCircleOutlined />} onClick={handleRun} loading={isRunning}>
              运行测试
            </Button>
            <Button type="primary" icon={<SendOutlined />} onClick={handleSubmit} loading={isSubmitting}>
              提交
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Simple Card component inline (to avoid importing from antd where it's used minimally in the markdown section)
function Card({ children, size, style }: { children: React.ReactNode; size?: string; style?: React.CSSProperties }) {
  return <div style={{ border: '1px solid #e8e8e8', borderRadius: 4, padding: size === 'small' ? 8 : 16, ...style }}>{children}</div>;
}
