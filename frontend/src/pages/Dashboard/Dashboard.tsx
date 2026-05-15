import { useEffect, useState } from 'react';
import { Card, Col, Row, Statistic, Typography } from 'antd';
import { BookOutlined, UserOutlined, CheckCircleOutlined } from '@ant-design/icons';
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
      <Title level={4} style={{ marginBottom: 24 }}>
        欢迎回来, {user?.nickname || user?.username}
      </Title>
      <Row gutter={[24, 24]}>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="我的课程"
              value={courseCount}
              prefix={<BookOutlined style={{ color: '#4d4d4d' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="角色"
              value={
                user?.role === 'teacher'
                  ? '教师'
                  : user?.role === 'admin'
                    ? '管理员'
                    : '学生'
              }
              prefix={<UserOutlined style={{ color: '#4d4d4d' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="状态"
              value={user?.is_active ? '正常' : '禁用'}
              prefix={<CheckCircleOutlined style={{ color: user?.is_active ? '#0070f3' : '#ee0000' }} />}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
