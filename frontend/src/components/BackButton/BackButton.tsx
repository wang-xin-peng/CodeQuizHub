import { Button } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

interface BackButtonProps {
  path?: string;  // optional: specific path to navigate to
}

export default function BackButton({ path }: BackButtonProps) {
  const navigate = useNavigate();

  return (
    <Button
      type="text"
      icon={<ArrowLeftOutlined />}
      onClick={() => (path ? navigate(path) : navigate(-1))}
      style={{ marginBottom: 0, padding: 0 }}
    >
      返回
    </Button>
  );
}
