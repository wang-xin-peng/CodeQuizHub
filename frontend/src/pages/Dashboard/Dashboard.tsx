import { useEffect, useState } from 'react';
import { Card, Col, Row, Statistic, Typography } from 'antd';
import { BookOutlined, CodeOutlined, FileTextOutlined } from '@ant-design/icons';
import { useAuthStore } from '../../store/authStore';
import * as coursesApi from '../../api/courses';

const { Title } = Typography;

export default function Dashboard() {
  const { user } = useAuthStore();
  const [courseCount, setCourseCount] = useState(0);

  useEffect(() => {
    coursesApi.getCourses({ page: 1, page_size: 1 }).then((res) => {
      setCourseCount(res.data.total);
    }).catch(() => {});
  }, []);

  return (
    <div>
      <Title level={4}>
        欢迎, {user?.nickname || user?.username}
      </Title>
      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic title="我的课程" value={courseCount} prefix={<BookOutlined />} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="角色" value={user?.role === 'teacher' ? '教师' : user?.role === 'admin' ? '管理员' : '学生'} prefix={<CodeOutlined />} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="状态" value={user?.is_active ? '正常' : '禁用'} prefix={<FileTextOutlined />} />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
