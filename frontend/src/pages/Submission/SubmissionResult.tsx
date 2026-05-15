import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Space, Spin, Tag, Typography, message } from 'antd';
import { ArrowLeftOutlined, CheckCircleFilled, CloseCircleFilled, WarningFilled } from '@ant-design/icons';
import * as submissionsApi from '../../api/submissions';
import CodeEditor from '../../components/CodeEditor/CodeEditor';
import type { SubmissionDetail } from '../../types';

const { Text, Title } = Typography;

const STATUS_LABEL: Record<string, string> = {
  accepted: '通过',
  wrong_answer: '解答错误',
  time_limit_exceeded: '超出时间限制',
  memory_limit_exceeded: '超出内存限制',
  runtime_error: '运行错误',
  compilation_error: '编译错误',
  pending: '等待评测',
  judging: '评测中',
};

const STATUS_ICON: Record<string, React.ReactNode> = {
  accepted: <CheckCircleFilled style={{ color: '#52c41a', fontSize: 28 }} />,
  wrong_answer: <CloseCircleFilled style={{ color: '#ff4d4f', fontSize: 28 }} />,
  time_limit_exceeded: <WarningFilled style={{ color: '#faad14', fontSize: 28 }} />,
  memory_limit_exceeded: <WarningFilled style={{ color: '#faad14', fontSize: 28 }} />,
  runtime_error: <CloseCircleFilled style={{ color: '#ff4d4f', fontSize: 28 }} />,
  compilation_error: <CloseCircleFilled style={{ color: '#ff4d4f', fontSize: 28 }} />,
};

const STATUS_BG: Record<string, string> = {
  accepted: '#f6ffed',
  wrong_answer: '#fff2f0',
  time_limit_exceeded: '#fffbe6',
  memory_limit_exceeded: '#fffbe6',
  runtime_error: '#fff2f0',
  compilation_error: '#fff2f0',
};

const STATUS_BORDER: Record<string, string> = {
  accepted: '#b7eb8f',
  wrong_answer: '#ffccc7',
  time_limit_exceeded: '#ffe58f',
  memory_limit_exceeded: '#ffe58f',
  runtime_error: '#ffccc7',
  compilation_error: '#ffccc7',
};

export default function SubmissionResult() {
  const { assignmentId, problemId, submissionId } = useParams<{
    assignmentId: string;
    problemId: string;
    submissionId: string;
  }>();
  const navigate = useNavigate();
  const [submission, setSubmission] = useState<SubmissionDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!submissionId) return;
    let cancelled = false;
    let attempts = 0;

    const poll = async () => {
      while (!cancelled && attempts < 30) {
        try {
          const res = await submissionsApi.getSubmission(submissionId);
          if (cancelled) return;
          setSubmission(res.data);
          setLoading(false);
          if (res.data.status !== 'pending' && res.data.status !== 'judging') {
            return; // done
          }
        } catch {
          if (cancelled) return;
        }
        attempts++;
        await new Promise((r) => setTimeout(r, 2000));
      }
      if (!cancelled) {
        message.info('评测超时，请手动刷新');
        setLoading(false);
      }
    };

    poll();
    return () => { cancelled = true; };
  }, [submissionId]);

  const s = submission;
  const isPending = s && (s.status === 'pending' || s.status === 'judging');
  const isDone = s && s.status !== 'pending' && s.status !== 'judging';
  const isAccepted = s?.status === 'accepted';
  const total = s?.results?.length || 0;
  const passed = s?.results?.filter((r) => r.status === 'accepted').length || 0;
  const firstError = s?.results?.find((r) => r.status !== 'accepted');

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: '#fafafa' }}>
      {/* Top bar */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '12px 24px', borderBottom: '1px solid #ebebeb', background: '#fff',
      }}>
        <Space>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate(`/solve/${assignmentId}/${problemId}`)}
          >
            返回题目
          </Button>
        </Space>
        <Button
          type="link"
          onClick={() => navigate(`/submissions/${assignmentId}/${problemId}`)}
        >
          提交历史
        </Button>
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflow: 'auto', padding: 24, maxWidth: 800, margin: '0 auto', width: '100%' }}>
        {loading && (
          <div style={{ textAlign: 'center', paddingTop: 80 }}>
            <Spin size="large" />
            <div style={{ marginTop: 16, color: '#595959' }}>正在获取评测结果...</div>
          </div>
        )}

        {isPending && (
          <div style={{ textAlign: 'center', paddingTop: 80 }}>
            <Spin size="large" />
            <div style={{ marginTop: 16, fontSize: 18, fontWeight: 500, color: '#595959' }}>评测中</div>
            <div style={{ marginTop: 8, color: '#8c8c8c' }}>正在运行测试用例...</div>
          </div>
        )}

        {isDone && (
          <>
            {/* Verdict banner */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: 16,
              padding: '20px 24px', marginBottom: 20,
              borderRadius: 8,
              background: STATUS_BG[s!.status] || '#fff',
              border: `1px solid ${STATUS_BORDER[s!.status] || '#d9d9d9'}`,
            }}>
              {STATUS_ICON[s!.status]}
              <div>
                <div style={{ fontSize: 22, fontWeight: 600, color: isAccepted ? '#52c41a' : '#ff4d4f' }}>
                  {STATUS_LABEL[s!.status] || s!.status}
                </div>
                <div style={{ marginTop: 4, color: '#595959', fontSize: 14 }}>
                  通过 {passed}/{total} 个测试用例
                  {s!.time_used != null && ` · ${s!.time_used}ms`}
                  {s!.memory_used != null && ` · ${s!.memory_used}KB`}
                </div>
              </div>
            </div>

            {/* Error details */}
            {s!.error_message && (
              <pre className="mono" style={{
                marginBottom: 20, padding: 12, borderRadius: 6,
                background: '#fff2f0', border: '1px solid #ffccc7',
                color: '#cf1322', whiteSpace: 'pre-wrap', fontSize: 13,
              }}>{s!.error_message}</pre>
            )}

            {/* Wrong answer: first failure */}
            {firstError && firstError.status === 'wrong_answer' && (
              <div style={{
                marginBottom: 20, padding: 16, borderRadius: 6,
                background: '#fff', border: '1px solid #ebebeb',
              }}>
                <div style={{ fontWeight: 500, marginBottom: 10 }}>
                  用例 {firstError.test_case_order + 1}
                </div>
                {firstError.input != null && (
                  <div style={{ marginBottom: 6 }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>输入: </Text>
                    <code style={{ fontSize: 12 }}>{JSON.stringify(firstError.input)}</code>
                  </div>
                )}
                <div style={{ marginBottom: 6 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>输出: </Text>
                  <code style={{ fontSize: 12, color: '#cf1322' }}>{JSON.stringify(firstError.actual)}</code>
                </div>
                <div style={{ marginBottom: 6 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>预期: </Text>
                  <code style={{ fontSize: 12, color: '#52c41a' }}>{JSON.stringify(firstError.expected)}</code>
                </div>
              </div>
            )}

            {/* Runtime error: first failure */}
            {firstError && firstError.status === 'runtime_error' && firstError.actual && (
              <pre className="mono" style={{
                marginBottom: 20, padding: 12, borderRadius: 6,
                background: '#fff2f0', border: '1px solid #ffccc7',
                color: '#cf1322', whiteSpace: 'pre-wrap', fontSize: 12,
              }}>
                用例 {firstError.test_case_order + 1} 运行错误:
{typeof firstError.actual === 'string' ? firstError.actual : JSON.stringify(firstError.actual)}
              </pre>
            )}

            {/* TLE / MLE */}
            {firstError && (firstError.status === 'time_limit_exceeded' || firstError.status === 'memory_limit_exceeded') && (
              <div style={{
                marginBottom: 20, padding: 12, borderRadius: 6,
                background: '#fffbe6', border: '1px solid #ffe58f', color: '#d48806',
              }}>
                用例 {firstError.test_case_order + 1} {firstError.status === 'time_limit_exceeded' ? '超出时间限制' : '超出内存限制'}
              </div>
            )}

            {/* Submitted code */}
            <div style={{ marginTop: 8 }}>
              <Title level={5} style={{ marginBottom: 8 }}>提交的代码</Title>
              <div style={{ border: '1px solid #ebebeb', borderRadius: 6, overflow: 'hidden' }}>
                <CodeEditor
                  value={s!.code || ''}
                  language={s!.language || 'python'}
                  onChange={() => {}}
                  readOnly
                  height="300px"
                />
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
