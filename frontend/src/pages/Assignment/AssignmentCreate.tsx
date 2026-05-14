import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button, Card, DatePicker, Form, Input, Select, Typography, message } from 'antd';
import * as assignmentsApi from '../../api/assignments';
import * as problemsApi from '../../api/problems';
import type { Problem } from '../../types';

const { Title } = Typography;
const { TextArea } = Input;
const { RangePicker } = DatePicker;

export default function AssignmentCreate() {
  const [loading, setLoading] = useState(false);
  const [problems, setProblems] = useState<Problem[]>([]);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const courseId = searchParams.get('courseId') || '';

  useEffect(() => {
    problemsApi.getProblems({ page: 1, page_size: 200 })
      .then((res) => setProblems(res.data.items))
      .catch(() => {});
  }, []);

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      const [start, end] = values.time_range;
      await assignmentsApi.createAssignment({
        course_id: courseId,
        title: values.title,
        description: values.description,
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        problem_ids: values.problem_ids,
      });
      message.success('作业发布成功');
      navigate(`/courses/${courseId}`);
    } catch (err: any) {
      message.error(err?.message || '发布失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Title level={4}>发布作业</Title>
      <Card style={{ maxWidth: 700 }}>
        <Form layout="vertical" onFinish={onFinish}>
          <Form.Item name="title" label="作业标题" rules={[{ required: true }]}>
            <Input placeholder="如: 第一次编程作业" />
          </Form.Item>
          <Form.Item name="description" label="作业说明">
            <TextArea rows={3} />
          </Form.Item>
          <Form.Item name="time_range" label="起止时间" rules={[{ required: true }]}>
            <RangePicker showTime style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="problem_ids" label="选择题目" rules={[{ required: true, message: '至少选择一道题目' }]}>
            <Select
              mode="multiple"
              placeholder="选择题目"
              options={problems.map((p) => ({ label: `${p.title} (${p.difficulty})`, value: p.id }))}
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>发布</Button>
            <Button style={{ marginLeft: 8 }} onClick={() => navigate(-1)}>取消</Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
