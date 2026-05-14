import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Form, Input, Select, Typography, message } from 'antd';
import * as coursesApi from '../../api/courses';

const { Title } = Typography;
const { TextArea } = Input;

const languageOptions = [
  { label: 'Python', value: 'python' },
  { label: 'Java', value: 'java' },
  { label: 'C', value: 'c' },
  { label: 'C++', value: 'cpp' },
];

export default function CourseCreate() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values: { name: string; description?: string; languages: string[] }) => {
    setLoading(true);
    try {
      await coursesApi.createCourse(values);
      message.success('课程创建成功');
      navigate('/courses');
    } catch (err: any) {
      message.error(err?.message || '创建失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Title level={4}>创建课程</Title>
      <Card style={{ maxWidth: 600 }}>
        <Form layout="vertical" onFinish={onFinish}>
          <Form.Item name="name" label="课程名称" rules={[{ required: true, message: '请输入课程名称' }]}>
            <Input placeholder="如: Python 程序设计" />
          </Form.Item>
          <Form.Item name="description" label="课程描述">
            <TextArea rows={3} placeholder="课程简介" />
          </Form.Item>
          <Form.Item name="languages" label="支持语言" rules={[{ required: true, message: '至少选择一种语言' }]}>
            <Select mode="multiple" options={languageOptions} placeholder="选择编程语言" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              创建
            </Button>
            <Button style={{ marginLeft: 8 }} onClick={() => navigate('/courses')}>
              取消
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
