import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Modal, Select, Space, Spin, Tabs, Tag, Typography, message, Card } from 'antd';
import { PlayCircleOutlined, SendOutlined, UndoOutlined } from '@ant-design/icons';
import { useDebouncedCallback } from 'use-debounce';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import CodeEditor from '../../components/CodeEditor/CodeEditor';
import InputParamsEditor from '../../components/InputParamsEditor/InputParamsEditor';
import { useEditorStore } from '../../store/editorStore';
import * as problemsApi from '../../api/problems';
import * as submissionsApi from '../../api/submissions';
import * as assignmentsApi from '../../api/assignments';
import * as coursesApi from '../../api/courses';
import type { Problem, TestResultItem } from '../../types';
import BackButton from '../../components/BackButton/BackButton';

const { Title, Text } = Typography;

export default function ProblemSolve() {
  const { assignmentId, problemId } = useParams<{ assignmentId: string; problemId: string }>();
  const [problem, setProblem] = useState<Problem | null>(null);
  const [loading, setLoading] = useState(true);
  const [availableLanguages, setAvailableLanguages] = useState<string[]>([]);
  const [initialTemplate, setInitialTemplate] = useState('');
  const [courseLanguages, setCourseLanguages] = useState<string[]>([]);

  // Feature: problem navigation
  const [assignmentProblems, setAssignmentProblems] = useState<string[]>([]);
  const [currentProblemIndex, setCurrentProblemIndex] = useState(-1);

  // Feature: custom test input
  const [customInputOpen, setCustomInputOpen] = useState(false);
  const [customInputJson, setCustomInputJson] = useState('{}');
  const [customRunResult, setCustomRunResult] = useState<string | null>(null);
  const [customRunError, setCustomRunError] = useState<string | null>(null);
  const [customRunLoading, setCustomRunLoading] = useState(false);

  const {
    code, language, isRunning, isSubmitting, testResults, compileError,
    setCode, setLanguage, setRunning, setSubmitting, setTestResults, setCompileError,
  } = useEditorStore();

  // Current language's function parameters for custom input editor
  const currentSignature = problem?.signatures?.find((s) => s.language === language);
  const currentParams = currentSignature?.parameters_json || [];

  // Draggable split between editor and results panel
  const splitContainerRef = useRef<HTMLDivElement>(null);
  const isDraggingRef = useRef(false);
  const [editorFlex, setEditorFlex] = useState(3);
  const [resultsFlex, setResultsFlex] = useState(1);

  const handleSplitMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    isDraggingRef.current = true;
    document.body.style.cursor = 'row-resize';
    document.body.style.userSelect = 'none';

    const handleMove = (ev: MouseEvent) => {
      if (!isDraggingRef.current || !splitContainerRef.current) return;
      const rect = splitContainerRef.current.getBoundingClientRect();
      const y = ev.clientY - rect.top;
      const ratio = Math.max(0.15, Math.min(0.85, y / rect.height));
      const editor = Math.round(ratio * 10);
      setEditorFlex(editor);
      setResultsFlex(10 - editor);
    };

    const handleUp = () => {
      isDraggingRef.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      document.removeEventListener('mousemove', handleMove);
      document.removeEventListener('mouseup', handleUp);
    };

    document.addEventListener('mousemove', handleMove);
    document.addEventListener('mouseup', handleUp);
  };

  // Load problem
  useEffect(() => {
    if (!problemId) return;
    setLoading(true);
    problemsApi.getProblem(problemId)
      .then((res) => {
        setProblem(res.data);
      })
      .catch((err) => message.error(err?.message || '加载题目失败'))
      .finally(() => setLoading(false));
  }, [problemId]);

  // Reset editor & results state when assignment/problem changes (stale state guard for global store)
  useEffect(() => {
    setTestResults([]);
    setCompileError(null);
    setCustomInputJson('{}');
    setCustomRunResult(null);
    setCustomRunError(null);
  }, [assignmentId, problemId]);

  // Load draft on mount and language change, fallback to code template
  useEffect(() => {
    if (!problemId || !assignmentId || !language) return;
    if (!initialTemplate) return; // wait for template to be ready
    submissionsApi.getDraft(problemId, { assignment_id: assignmentId, language })
      .then((res) => {
        if (res.data.code) {
          setCode(res.data.code);
        } else {
          setCode(initialTemplate);
        }
      })
      .catch(() => setCode(initialTemplate));
  }, [problemId, assignmentId, language, initialTemplate]);

  // Fetch assignment problems and course languages for language filtering
  useEffect(() => {
    if (!assignmentId) return;
    assignmentsApi.getAssignment(assignmentId)
      .then((res) => {
        const problems = res.data.problems || [];
        const problemIds = problems
          .sort((a, b) => a.order - b.order)
          .map((p) => p.problem_id);
        setAssignmentProblems(problemIds);
        const idx = problemIds.indexOf(problemId || '');
        setCurrentProblemIndex(idx);

        // Fetch course to get supported languages
        coursesApi.getCourse(res.data.course_id)
          .then((courseRes) => {
            setCourseLanguages(courseRes.data.languages || []);
          })
          .catch(() => {});
      })
      .catch(() => {});
  }, [assignmentId, problemId]);

  // Compute available languages filtered by course languages
  useEffect(() => {
    if (!problem) return;
    const langs = problem.signatures?.map((s) => s.language) || [];
    const filtered = courseLanguages.length > 0
      ? langs.filter((l) => courseLanguages.includes(l))
      : langs;
    setAvailableLanguages(filtered);

    if (filtered.length > 0) {
      if (!filtered.includes(language)) {
        const newLang = filtered[0];
        setLanguage(newLang);
      }
      // Always set the code template for the current/first language
      const currentLang = filtered.includes(language) ? language : filtered[0];
      const sig = problem.signatures?.find((s) => s.language === currentLang);
      if (sig) {
        setInitialTemplate(sig.code_template);
      }
    }
  }, [problem, courseLanguages]);

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
    setCustomInputJson('{}');
    const sig = problem?.signatures?.find((s) => s.language === lang);
    if (sig) {
      setInitialTemplate(sig.code_template);
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

  const navigate = useNavigate();

  const handlePrevProblem = () => {
    if (currentProblemIndex > 0) {
      navigate(`/solve/${assignmentId}/${assignmentProblems[currentProblemIndex - 1]}`);
    }
  };

  const handleNextProblem = () => {
    if (currentProblemIndex < assignmentProblems.length - 1) {
      navigate(`/solve/${assignmentId}/${assignmentProblems[currentProblemIndex + 1]}`);
    }
  };

  const handleCustomRun = async () => {
    if (!problemId || !assignmentId) return;
    setCustomRunLoading(true);
    setCustomRunResult(null);
    setCustomRunError(null);
    try {
      let parsedInput: Record<string, unknown>;
      try {
        parsedInput = JSON.parse(customInputJson);
      } catch {
        message.error('自定义输入必须是有效的 JSON');
        setCustomRunLoading(false);
        return;
      }
      const res = await problemsApi.runCustomCode(problemId, {
        language,
        code,
        assignment_id: assignmentId,
        custom_input: parsedInput,
      });
      if (res.data.error) {
        setCustomRunError(res.data.error);
      } else {
        setCustomRunResult(res.data.output);
      }
    } catch (err: any) {
      message.error(err?.message || '自定义运行失败');
    } finally {
      setCustomRunLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!problemId || !assignmentId) return;
    setSubmitting(true);
    try {
      // Save draft first — the debounced auto-save may not have fired yet.
      // Without this, returning to the problem later shows the template instead of the code.
      await submissionsApi.saveDraft({
        problem_id: problemId,
        assignment_id: assignmentId,
        language,
        code,
      });

      const res = await submissionsApi.submitCode({
        assignment_id: assignmentId,
        problem_id: problemId,
        language,
        code,
      });
      const submissionId = res.data.submission_id;
      setSubmitting(false);
      navigate(`/solve/${assignmentId}/${problemId}/submission/${submissionId}`);
    } catch (err: any) {
      message.error(err?.message || '提交失败');
      setSubmitting(false);
    }
  };

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  if (!problem) return <div className="empty-state">题目不存在</div>;

  const statusColors: Record<string, string> = {
    accepted: 'success',
    wrong_answer: 'error',
    time_limit_exceeded: 'warning',
    memory_limit_exceeded: 'warning',
    runtime_error: 'error',
    compilation_error: 'error',
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
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: '#fafafa' }}>
      {/* ── Navigation bar (only nav buttons) ── */}
      <div className="solve-topbar">
        <BackButton path={assignmentId ? `/assignments/${assignmentId}` : '/'} />
        <Space size={8}>
          <Button
            size="small"
            disabled={currentProblemIndex <= 0}
            onClick={handlePrevProblem}
            style={{ minWidth: 80 }}
          >
            ← 上一题
          </Button>
          <Button
            size="small"
            disabled={currentProblemIndex >= assignmentProblems.length - 1}
            onClick={handleNextProblem}
            style={{ minWidth: 80 }}
          >
            下一题 →
          </Button>
        </Space>
        <Button
          type="link"
          size="small"
          onClick={() => navigate(`/submissions/${assignmentId}/${problemId}`)}
        >
          提交历史
        </Button>
      </div>

      {/* ── Problem info header ── */}
      <div className="solve-problem-header">
        <div className="solve-problem-title-row">
          <span className="solve-problem-title">{problem?.title}</span>
          <Tag
            color={problem.difficulty === 'easy' ? 'green' : problem.difficulty === 'medium' ? 'warning' : 'red'}
            style={{ borderRadius: 12, padding: '0 10px', fontSize: 12, lineHeight: '22px', margin: 0 }}
          >
            {problem.difficulty === 'easy' ? '简单' : problem.difficulty === 'medium' ? '中等' : '困难'}
          </Tag>
        </div>
        <div className="solve-problem-meta">
          <span>时间限制: {problem.time_limit}ms</span>
          <span className="solve-meta-divider">|</span>
          <span>内存限制: {problem.memory_limit}MB</span>
        </div>
      </div>

      {/* ── Main content ── */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Left: problem description */}
        <div className="solve-panel-description">
          <div className="markdown-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{problem.description}</ReactMarkdown>
          </div>

          {problem.test_cases && problem.test_cases.length > 0 && (
            <div style={{ marginTop: 28, paddingTop: 4 }}>
              <Title level={5} style={{ marginBottom: 14, fontSize: 15, fontWeight: 600, color: '#171717' }}>示例</Title>
              {problem.test_cases.filter((tc) => tc.is_public).map((tc, idx) => (
                <Card
                  key={tc.id}
                  size="small"
                  style={{ marginBottom: 12, borderRadius: 8, border: '1px solid #e8e8e8' }}
                  styles={{ body: { padding: '14px 16px' } }}
                >
                  <div style={{ marginBottom: 8 }}>
                    <Text strong style={{ fontSize: 13, color: '#262626' }}>示例 {idx + 1}:</Text>
                  </div>
                  <div style={{ background: '#f8f9fa', borderRadius: 6, padding: '10px 14px', border: '1px solid #eee' }}>
                    <div style={{ marginBottom: 10 }}>
                      <Text type="secondary" style={{ fontSize: 11, fontFamily: 'ui-monospace, monospace', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>输入</Text>
                      <pre className="solve-example-code">{JSON.stringify(tc.input_params_json, null, 2)}</pre>
                    </div>
                    <div>
                      <Text type="secondary" style={{ fontSize: 11, fontFamily: 'ui-monospace, monospace', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>输出</Text>
                      <pre className="solve-example-code">{typeof tc.expected_output_json === 'string' ? tc.expected_output_json : JSON.stringify(tc.expected_output_json, null, 2)}</pre>
                    </div>
                  </div>
                  {tc.description && (
                    <div style={{ marginTop: 8, padding: '0 2px' }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>{tc.description}</Text>
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Right: editor + results */}
        <div className="solve-panel-editor">
          {/* Language selector + reset */}
          <div style={{ padding: '8px 16px', borderBottom: '1px solid #ebebeb', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Select
              value={language}
              onChange={handleLanguageChange}
              style={{ width: 120 }}
              options={availableLanguages.map((l) => ({ label: l.charAt(0).toUpperCase() + l.slice(1), value: l }))}
            />
            <Button icon={<UndoOutlined />} onClick={handleReset} size="small">重置代码</Button>
          </div>

          {/* Resizable split: editor + results */}
          <div ref={splitContainerRef} style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'hidden' }}>
            {/* Editor */}
            <div style={{ flex: editorFlex, minHeight: 0 }}>
              <CodeEditor value={code} language={language} onChange={handleCodeChange} height="100%" />
            </div>

            {/* Drag handle */}
            <div
              onMouseDown={handleSplitMouseDown}
              style={{
                flex: '0 0 6px',
                cursor: 'row-resize',
                background: '#f0f0f0',
                borderTop: '1px solid #e0e0e0',
                borderBottom: '1px solid #e0e0e0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <div style={{ width: 24, height: 2, borderRadius: 1, background: '#bbb' }} />
            </div>

            {/* Results panel */}
            <div style={{ flex: resultsFlex, overflow: 'auto', padding: 12, background: '#ffffff' }}>
            <Tabs
              size="small"
              items={[
                {
                  key: 'results',
                  label: '测试结果',
                  children: (
                    <div>
                      {compileError ? (
                        <pre className="mono" style={{ color: '#ee0000', whiteSpace: 'pre-wrap' }}>{compileError}</pre>
                      ) : testResults.length > 0 ? (() => {
                        const total = testResults.length;
                        const passed = testResults.filter(r => r.status === 'accepted').length;
                        const firstError = testResults.find(r => r.status !== 'accepted');
                        const isAccepted = passed === total;

                        return (
                          <div>
                            {/* 总体状态 */}
                            <div style={{
                              display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12,
                              padding: 12, borderRadius: 6,
                              background: isAccepted ? '#f6ffed' : '#fff2f0',
                              border: `1px solid ${isAccepted ? '#b7eb8f' : '#ffccc7'}`,
                            }}>
                              <span style={{
                                fontSize: 20, fontWeight: 600,
                                color: isAccepted ? '#52c41a' : '#ff4d4f',
                              }}>
                                {isAccepted ? '✓ 通过' : statusLabels[firstError?.status || ''] || firstError?.status}
                              </span>
                            </div>

                            {/* 通过数/总数 */}
                            <div style={{ marginBottom: 8, color: '#595959' }}>
                              通过 <Text strong>{passed}</Text>/{total} 个测试用例
                            </div>

                            {/* 错误详情（首次失败的用例 — WA） */}
                            {firstError && firstError.status === 'wrong_answer' && (
                              <div style={{ marginTop: 12, padding: 8, background: '#fafafa', borderRadius: 4, fontSize: 13 }}>
                                <div style={{ fontWeight: 500, marginBottom: 6 }}>
                                  用例 {firstError.test_case_order + 1}
                                </div>
                                {firstError.input != null && (
                                  <div style={{ marginBottom: 2 }}>
                                    <Text type="secondary" style={{ fontSize: 12 }}>输入: </Text>
                                    <code style={{ fontSize: 12 }}>{JSON.stringify(firstError.input)}</code>
                                  </div>
                                )}
                                <div style={{ marginBottom: 2 }}>
                                  <Text type="secondary" style={{ fontSize: 12 }}>输出: </Text>
                                  <code style={{ fontSize: 12, color: '#cf1322' }}>{JSON.stringify(firstError.actual)}</code>
                                </div>
                                <div style={{ marginBottom: 2 }}>
                                  <Text type="secondary" style={{ fontSize: 12 }}>预期: </Text>
                                  <code style={{ fontSize: 12, color: '#52c41a' }}>{JSON.stringify(firstError.expected)}</code>
                                </div>
                              </div>
                            )}

                            {/* 运行错误详情 */}
                            {firstError && firstError.status === 'runtime_error' && firstError.actual && (
                              <pre className="mono" style={{
                                marginTop: 8, padding: 8, borderRadius: 4,
                                background: '#fff2f0', border: '1px solid #ffccc7',
                                color: '#cf1322', whiteSpace: 'pre-wrap', fontSize: 12,
                              }}>用例 {firstError.test_case_order + 1} 运行错误:
{typeof firstError.actual === 'string' ? firstError.actual : JSON.stringify(firstError.actual)}</pre>
                            )}

                            {/* TLE / MLE */}
                            {firstError && (firstError.status === 'time_limit_exceeded' || firstError.status === 'memory_limit_exceeded') && (
                              <div style={{ marginTop: 8, color: '#d48806' }}>
                                用例 {firstError.test_case_order + 1} {firstError.status === 'time_limit_exceeded' ? '超出时间限制' : '超出内存限制'}
                              </div>
                            )}
                          </div>
                        );
                      })() : (
                        <Text type="secondary">点击"运行测试"查看结果</Text>
                      )}
                    </div>
                  ),
                },
                {
                  key: 'custom',
                  label: '自定义输入',
                  children: (
                    <div>
                      {customRunError && (
                        <pre className="mono" style={{ color: '#ee0000', whiteSpace: 'pre-wrap' }}>{customRunError}</pre>
                      )}
                      {customRunResult && (
                        <pre className="mono" style={{ background: '#f5f5f5', padding: 8, borderRadius: 4, whiteSpace: 'pre-wrap' }}>
                          {customRunResult}
                        </pre>
                      )}
                      {!customRunResult && !customRunError && (
                        <Text type="secondary">点击底部"自定义运行"按钮运行自定义测试</Text>
                      )}
                    </div>
                  ),
                },
              ]}
            />
          </div>
          </div>

          {/* Bottom action bar */}
          <div style={{ padding: '8px 16px', borderTop: '1px solid #ebebeb', display: 'flex', justifyContent: 'space-between', background: '#ffffff' }}>
            <Space>
              <Button icon={<PlayCircleOutlined />} onClick={handleRun} loading={isRunning}>
                运行测试
              </Button>
              <Button onClick={() => setCustomInputOpen(true)}>
                自定义运行
              </Button>
            </Space>
            <Button type="primary" icon={<SendOutlined />} onClick={handleSubmit} loading={isSubmitting}>
              提交
            </Button>
          </div>
        </div>
      </div>

      {/* Custom test input modal */}
      <Modal
        title="自定义测试输入"
        open={customInputOpen}
        onCancel={() => setCustomInputOpen(false)}
        footer={null}
      >
        <InputParamsEditor
          value={customInputJson}
          onChange={(v) => setCustomInputJson(v)}
          parameters={currentParams}
        />
        <div style={{ marginTop: 12, marginBottom: 12 }}>
          <Button type="primary" onClick={handleCustomRun} loading={customRunLoading}>
            运行
          </Button>
        </div>
        {(customRunResult !== null || customRunError !== null) && (
          <div>
            <div style={{ marginBottom: 4 }}>
              <Text strong>{customRunError ? '错误' : '输出'}:</Text>
            </div>
            <pre
              style={{
                background: '#f5f5f5',
                padding: 8,
                borderRadius: 4,
                fontFamily: 'monospace',
                whiteSpace: 'pre-wrap',
                color: customRunError ? '#ee0000' : undefined,
              }}
            >
              {customRunError || customRunResult}
            </pre>
          </div>
        )}
      </Modal>
    </div>
  );
}
