import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Dropdown, Avatar, Space, Typography, message } from 'antd';
import {
  BarChartOutlined,
  BookOutlined,
  CodeOutlined,
  DashboardOutlined,
  KeyOutlined,
  LogoutOutlined,
  SwapOutlined,
  TeamOutlined,
  UserOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../../store/authStore';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, accounts, switchAccount } = useAuthStore();

  const isTeacher = user?.role === 'teacher' || user?.role === 'admin';
  const isAdmin = user?.role === 'admin';

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    {
      key: '/courses',
      icon: <BookOutlined />,
      label: '课程管理',
    },
    ...(isTeacher
      ? [
          {
            key: '/grades',
            icon: <BarChartOutlined />,
            label: '成绩管理',
          },
        ]
      : []),
    ...(isTeacher
      ? [
          {
            key: '/problems',
            icon: <CodeOutlined />,
            label: '题目管理',
          },
        ]
      : []),
    ...(isAdmin
      ? [
          {
            key: '/admin/users',
            icon: <TeamOutlined />,
            label: '用户管理',
          },
        ]
      : []),
  ];

  const otherAccounts = accounts.filter((a) => a.userId !== user?.id);
  const userMenuItems: any[] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人信息',
    },
    {
      key: 'password',
      icon: <KeyOutlined />,
      label: '修改密码',
    },
  ];

  // Account switching
  if (otherAccounts.length > 0) {
    userMenuItems.push({ type: 'divider' as const });
    userMenuItems.push({
      key: 'account_group',
      type: 'group' as const,
      label: '切换账号',
      children: otherAccounts.map((a) => ({
        key: `switch_${a.userId}`,
        icon: <SwapOutlined />,
        label: `${a.user.nickname || a.user.username} (${a.email})`,
      })),
    });
  }

  userMenuItems.push({ type: 'divider' as const });
  userMenuItems.push({
    key: 'logout',
    icon: <LogoutOutlined />,
    label: '退出登录',
    danger: true,
  });

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  const handleUserMenuClick = ({ key }: { key: string }) => {
    if (key === 'logout') {
      logout();
      navigate('/login');
    } else if (key === 'profile') {
      navigate('/profile');
    } else if (key === 'password') {
      navigate('/profile/password');
    } else if (key.startsWith('switch_')) {
      const userId = key.replace('switch_', '');
      switchAccount(userId);
      message.success('已切换账号');
    }
  };

  // Determine which menu item is selected
  const selectedKey = '/' + location.pathname.split('/')[1];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* ── Sidebar ── */}
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        trigger={null}
        width={220}
        style={{
          borderRight: '1px solid #ebebeb',
          background: '#ffffff',
        }}
      >
        {/* Logo area */}
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            padding: collapsed ? 0 : '0 20px',
            borderBottom: '1px solid #ebebeb',
          }}
        >
          <Text strong style={{ fontSize: collapsed ? 18 : 20, color: '#171717', letterSpacing: '-0.6px' }}>
            {collapsed ? 'CQ' : 'CodeQuizHub'}
          </Text>
        </div>

        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ border: 'none', marginTop: 8 }}
        />
      </Sider>

      <Layout>
        {/* ── Top Header ── */}
        <Header
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            height: 64,
            borderBottom: '1px solid #ebebeb',
            background: '#ffffff',
            padding: '0 24px',
          }}
        >
          {/* Collapse toggle */}
          <div
            style={{ cursor: 'pointer', fontSize: 16, color: '#888888' }}
            onClick={() => setCollapsed(!collapsed)}
          >
            {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          </div>

          {/* User menu */}
          <Dropdown
            menu={{ items: userMenuItems, onClick: handleUserMenuClick }}
            placement="bottomRight"
          >
            <Space style={{ cursor: 'pointer' }} size={10}>
              <Avatar
                size={28}
                icon={<UserOutlined />}
                style={{ background: '#f5f5f5', color: '#171717' }}
              />
              <Text style={{ color: '#171717', fontSize: 14, fontWeight: 500 }}>
                {user?.nickname || user?.username}
              </Text>
            </Space>
          </Dropdown>
        </Header>

        {/* ── Content ── */}
        <Content
          style={{
            margin: 0,
            padding: 24,
            background: '#fafafa',
            minHeight: 'calc(100vh - 64px)',
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
