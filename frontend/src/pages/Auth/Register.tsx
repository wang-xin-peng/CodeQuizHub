import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Form, Input, Button, Card, message, Radio, Typography } from 'antd';
import { LockOutlined, MailOutlined, UserOutlined } from '@ant-design/icons';
import * as authApi from '../../api/auth';
import BackButton from '../../components/BackButton/BackButton';

const { Title, Text } = Typography;

export default function Register() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values: { username: string; email: string; password: string; role: string }) => {
    setLoading(true);
    try {
      await authApi.register({
        username: values.username,
        email: values.email,
        password: values.password,
        role: values.role as 'teacher' | 'student',
      });
      message.success('注册成功，请登录');
      navigate('/login');
    } catch (err: any) {
      message.error(err?.message || '注册失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#fafafa',
      }}
    >
      <Card style={{ width: 420 }}>
        <BackButton path="/login" />
        <Title level={3} style={{ textAlign: 'center', marginBottom: 32, letterSpacing: '-0.96px' }}>
          注册 CodeQuizHub
        </Title>
        <Form onFinish={onFinish} size="large" initialValues={{ role: 'student' }}>
          <Form.Item
            name="username"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, max: 50, message: '3-50个字符' },
            ]}
          >
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>
          <Form.Item
            name="email"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '邮箱格式不正确' },
            ]}
          >
            <Input prefix={<MailOutlined />} placeholder="邮箱" />
          </Form.Item>
          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 8, message: '至少8个字符' },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码（至少8位）"
            />
          </Form.Item>
          <Form.Item name="role" label="角色">
            <Radio.Group>
              <Radio value="student">学生</Radio>
              <Radio value="teacher">教师</Radio>
            </Radio.Group>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              注册
            </Button>
          </Form.Item>
          <div style={{ textAlign: 'center' }}>
            <Text type="secondary">已有账号？</Text>
            <Link to="/login">去登录</Link>
          </div>
        </Form>
      </Card>
    </div>
  );
}
