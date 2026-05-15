import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { ErrorBoundary } from './components/ErrorBoundary/ErrorBoundary'
import { vercelTheme } from './theme'
import { router } from './routes'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary>
      <ConfigProvider locale={zhCN} theme={vercelTheme}>
        <RouterProvider router={router} />
      </ConfigProvider>
    </ErrorBoundary>
  </StrictMode>,
)
