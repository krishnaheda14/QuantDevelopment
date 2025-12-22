import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Chip,
  useTheme,
  useMediaQuery,
} from '@mui/material'
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  TrendingUp as TrendingUpIcon,
  ShowChart as ShowChartIcon,
  Science as ScienceIcon,
  PlayArrow as PlayArrowIcon,
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  CompareArrows as CompareArrowsIcon,
  AutoGraph as AutoGraphIcon,
  Opacity as WaterDropIcon,
  GridView as GridViewIcon,
  TableChart as TableChartIcon,
  Insights as InsightsIcon,
} from '@mui/icons-material'
import { debug } from '@/types'
import { useStore } from '@/store'
import ConnectionStatus from '@/components/ConnectionStatus'

const DRAWER_WIDTH = 280

interface NavItem {
  title: string
  path: string
  icon: React.ReactElement
}

const navItems: NavItem[] = [
  { title: 'Dashboard', path: '/dashboard', icon: <DashboardIcon /> },
  { title: 'Spread Analysis', path: '/spread', icon: <TrendingUpIcon /> },
  { title: 'Strategy Signals', path: '/signals', icon: <ShowChartIcon /> },
  { title: 'Statistical Tests', path: '/statistical', icon: <ScienceIcon /> },
  { title: 'Backtesting', path: '/backtest', icon: <PlayArrowIcon /> },
  { title: 'Alerts', path: '/alerts', icon: <NotificationsIcon /> },
  { title: 'API Debug', path: '/apidebug', icon: <SettingsIcon /> },
  { title: 'Quick Compare', path: '/compare', icon: <CompareArrowsIcon /> },
  { title: 'Kalman & Robust', path: '/kalman', icon: <AutoGraphIcon /> },
  { title: 'Liquidity', path: '/liquidity', icon: <WaterDropIcon /> },
  { title: 'Microstructure', path: '/microstructure', icon: <GridViewIcon /> },
  { title: 'Correlation', path: '/correlation', icon: <InsightsIcon /> },
  { title: 'Time Series Table', path: '/timeseries', icon: <TableChartIcon /> },
]

export default function Layout() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const { isConnected, alerts } = useStore()

  const handleDrawerToggle = () => {
    debug('Layout', 'Drawer toggle', { currentState: mobileOpen })
    setMobileOpen(!mobileOpen)
  }

  const handleNavigation = (path: string) => {
    debug('Layout', 'Navigating', { from: location.pathname, to: path })
    navigate(path)
    if (isMobile) {
      setMobileOpen(false)
    }
  }

  const drawer = (
    <Box>
      <Toolbar
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          px: 2,
          background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 40,
              height: 40,
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #00ff88 0%, #00cc6a 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 'bold',
              fontSize: '1.2rem',
              color: '#000',
            }}
          >
            G
          </Box>
          <Typography variant="h6" noWrap component="div" fontWeight={700}>
            GEMSCAP
          </Typography>
        </Box>
      </Toolbar>

      <Box sx={{ px: 2, py: 2 }}>
        <ConnectionStatus />
      </Box>

      <Divider sx={{ borderColor: 'rgba(255,255,255,0.1)' }} />

      <List sx={{ px: 1, py: 1 }}>
        {navItems.map((item) => {
          const isActive = location.pathname === item.path
          const showAlertBadge = item.path === '/alerts' && alerts.length > 0

          return (
            <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                selected={isActive}
                onClick={() => handleNavigation(item.path)}
                sx={{
                  borderRadius: 2,
                  '&.Mui-selected': {
                    backgroundColor: 'rgba(0, 255, 136, 0.1)',
                    borderLeft: '3px solid',
                    borderColor: 'primary.main',
                    '&:hover': {
                      backgroundColor: 'rgba(0, 255, 136, 0.15)',
                    },
                  },
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                  },
                }}
              >
                <ListItemIcon sx={{ color: isActive ? 'primary.main' : 'inherit', minWidth: 40 }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.title}
                  primaryTypographyProps={{
                    fontSize: '0.9rem',
                    fontWeight: isActive ? 600 : 400,
                  }}
                />
                {showAlertBadge && (
                  <Chip
                    label={alerts.length}
                    size="small"
                    color="error"
                    sx={{ height: 20, fontSize: '0.7rem' }}
                  />
                )}
              </ListItemButton>
            </ListItem>
          )
        })}
      </List>
    </Box>
  )

  debug('Layout', 'Rendering layout', {
    pathname: location.pathname,
    isMobile,
    isConnected,
  })

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { md: `${DRAWER_WIDTH}px` },
          backgroundColor: 'background.paper',
          backgroundImage: 'none',
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {navItems.find((item) => item.path === location.pathname)?.title || 'GEMSCAP Quant'}
          </Typography>
          <Chip
            label={isConnected ? 'LIVE' : 'DISCONNECTED'}
            color={isConnected ? 'success' : 'error'}
            size="small"
            icon={
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  backgroundColor: isConnected ? '#00ff88' : '#ff4444',
                  animation: isConnected ? 'pulse 2s infinite' : 'none',
                }}
              />
            }
          />
        </Toolbar>
      </AppBar>

      <Box
        component="nav"
        sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}
        aria-label="navigation"
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better mobile performance
          }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: DRAWER_WIDTH,
              backgroundColor: 'background.paper',
            },
          }}
        >
          {drawer}
        </Drawer>

        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: DRAWER_WIDTH,
              backgroundColor: 'background.paper',
              borderRight: '1px solid rgba(255,255,255,0.1)',
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          minHeight: '100vh',
          backgroundColor: 'background.default',
        }}
      >
        <Toolbar /> {/* Spacer for fixed AppBar */}
        <Outlet />
      </Box>
    </Box>
  )
}
