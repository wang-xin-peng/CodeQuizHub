import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Table, Tag, Typography, Spin, message, Descriptions, Space } from 'antd';
import { EyeOutlined } from '@ant-design/icons';
import * as submissionsApi from '../../api/submissions';
import type { Submission, SubmissionDetail } from '../../types';
import BackButton from '../../components/BackButton/BackButton';

const { Title, Text } = Typography;

const statusConfig: Record<string, { color: string; label: string }> = {
  accepted: { color: 'success', label: 'AC' },
  wrong_answer: { color: 'error', label: 'WA' },
  time_limit_exceeded: { color: 'warning', label: 'TLE' },
  memory_limit_exceeded: { color: 'warning', label: 'MLE' },
  runtime_error: { color: 'error', label: 'RE' },
  compilation_error: { color: 'error', label: 'CE' },
  pending: { color: 'default', label: 'Pending' },
  judging: { color: 'processing', label: 'Judging' },
};

function getStatusConfig(status: string) {
  return statusConfig[status] || { color: 'default', label: status };
}

export default function SubmissionHistory() {
  const { assignmentId, problemId } = useParams<{ assignmentId: string; problemId?: string }>();
  const navigate = useNavigate();
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [expandedDetail, setExpandedDetail] = useState<Record<string, SubmissionDetail | null>>({});

  const fetchSubmissions = async (p = page) => {
    if (!assignmentId) return;
    setLoading(true);
    try {
      const res = await submissionsApi.getAssignmentSubmissions(assignmentId, { page: p, page_size: pageSize });
      let items = res.data.items;
      // If problemId is specified, filter client-side
      if (problemId) {
        items = items.filter((s) => s.problem_id === problemId);
      }
      setSubmissions(items);
      setTotal(res.data.total);
    } catch (err: any) {
      message.error(err?.message || '获取提交记录失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubmissions();
  }, [assignmentId, problemId, page]);

  const handleExpand = async (submissionId: string) => {
    if (expandedDetail[submissionId]) {
      // Already loaded, just toggle
      return;
    }
    try {
      const res = await submissionsApi.getSubmission(submissionId);
      setExpandedDetail((prev) => ({ ...prev, [submissionId]: res.data }));
    } catch (err: any) {
      message.error(err?.message || '获取提交详情失败');
    }
  };

  const columns = [
    {
      title: '提交时间',
      dataIndex: 'submitted_at',
      key: 'submitted_at',
      width: 180,
      render: (val: string) => new Date(val).toLocaleString(),
    },
    {
      title: '语言',
      dataIndex: 'language',
      key: 'language',
      width: 100,
      render: (lang: string) => lang?.toUpperCase(),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => {
        const cfg = getStatusConfig(status);
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      },
    },
    {
      title: '得分',
      dataIndex: 'score',
      key: 'score',
      width: 80,
      render: (score: number) => (score != null ? `${score}分` : '-'),
    },
    {
      title: '耗时',
      dataIndex: 'time_used',
      key: 'time_used',
      width: 100,
      render: (val: number | undefined) => (val != null ? `${val}ms` : '-'),
    },
    {
      title: '内存',
      dataIndex: 'memory_used',
      key: 'memory_used',
      width: 120,
      render: (val: number | undefined) => {
        if (val == null) return '-';
        return val >= 1024 ? `${(val / 1024).toFixed(2)}MB` : `${val}KB`;
      },
    },
  ];

  const expandedRowRender = (record: Submission) => {
    const detail = expandedDetail[record.id];
    if (!detail) return null;

    if (detail.status === 'compilation_error' && detail.error_message) {
      return (
        <div style={{ padding: 12 }}>
          <Text strong style={{ color: '#ff4d4f' }}>编译错误:</Text>
          <pre
            style={{
              background: '#fff2f0',
              padding: 8,
              borderRadius: 4,
              marginTop: 8,
              whiteSpace: 'pre-wrap',
              fontSize: 13,
            }}
          >
            {detail.error_message}
          </pre>
        </div>
      );
    }

    if (!detail.results || detail.results.length === 0) {
      return <div style={{ padding: 12 }}><Text type="secondary">暂无测试结果</Text></div>;
    }

    return (
      <div style={{ padding: 12 }}>
        <Descriptions size="small" column={1} style={{ marginBottom: 12 }}>
          {detail.score != null && (
            <Descriptions.Item label="得分">{detail.score}分</Descriptions.Item>
          )}
          {detail.time_used != null && (
            <Descriptions.Item label="总耗时">{detail.time_used}ms</Descriptions.Item>
          )}
          {detail.memory_used != null && (
            <Descriptions.Item label="总内存">
              {detail.memory_used >= 1024
                ? `${(detail.memory_used / 1024).toFixed(2)}MB`
                : `${detail.memory_used}KB`}
            </Descriptions.Item>
          )}
        </Descriptions>

        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ background: '#fafafa' }}>
              <th style={thStyle}>用例</th>
              <th style={thStyle}>状态</th>
              <th style={thStyle}>耗时</th>
              <th style={thStyle}>内存</th>
            </tr>
          </thead>
          <tbody>
            {detail.results.map((r, idx) => {
              const cfg = getStatusConfig(r.status);
              return (
                <tr key={idx} style={{ borderBottom: '1px solid #f0f0f0' }}>
                  <td style={tdStyle}>用例 {r.test_case_order + 1}</td>
                  <td style={tdStyle}>
                    <Tag color={cfg.color}>{cfg.label}</Tag>
                  </td>
                  <td style={tdStyle}>{r.time_used != null ? `${r.time_used}ms` : '-'}</td>
                  <td style={tdStyle}>
                    {r.memory_used != null
                      ? r.memory_used >= 1024
                        ? `${(r.memory_used / 1024).toFixed(2)}MB`
                        : `${r.memory_used}KB`
                      : '-'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    );
  };

  const thStyle: React.CSSProperties = {
    padding: '8px 12px',
    textAlign: 'left',
    fontWeight: 600,
    borderBottom: '2px solid #f0f0f0',
  };
  const tdStyle: React.CSSProperties = {
    padding: '8px 12px',
  };

  if (loading && submissions.length === 0) {
    return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  }

  return (
    <div>
      <BackButton />

      <div className="page-header">
        <Title level={4} style={{ margin: 0 }}>
          提交记录
          {problemId && <Text type="secondary" style={{ fontSize: 14, marginLeft: 8 }}>(题目筛选)</Text>}
        </Title>
        <Space>
          {problemId && assignmentId && (
            <Button type="primary" icon={<EyeOutlined />} onClick={() => navigate(`/solve/${assignmentId}/${problemId}`)}>
              返回做题
            </Button>
          )}
        </Space>
      </div>

      <Table
        dataSource={submissions}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          total,
          pageSize,
          onChange: (p) => setPage(p),
          showSizeChanger: false,
        }}
        expandable={{
          expandedRowRender,
          onExpand: (expanded, record) => {
            if (expanded) {
              handleExpand(record.id);
            }
          },
          rowExpandable: () => true,
          expandRowByClick: true,
        }}
        style={{ marginTop: 16 }}
      />
    </div>
  );
}
