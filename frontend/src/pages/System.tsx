import React from 'react'
import { Box, Grid, Card, CardContent, Typography, Button, Stack, Divider } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import api from '@/services/api'
import { debug } from '@/types'

const COMPONENT_NAME = 'System'

const endpoints = [
  '/health',
  '/api/debug/system/status',
  '/api/debug/redis/status',
  '/api/debug/services/status',
  '/api/analytics/spread',
  '/api/analytics/adf',
  '/api/analytics/indicators',
]

const SystemPage: React.FC = () => {
  debug(COMPONENT_NAME, 'Rendering system diagnostics')

  const { data: health } = useQuery({ queryKey: ['health'], queryFn: api.getHealth, refetchInterval: 5000 })
  const { data: sys } = useQuery({ queryKey: ['debugSystem'], queryFn: api.getDebugSystemStatus })
  const { data: redis } = useQuery({ queryKey: ['debugRedis'], queryFn: api.getDebugRedisStatus })
  const { data: services } = useQuery({ queryKey: ['debugServices'], queryFn: api.getDebugServicesStatus })

  return (
    <Box>
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6">Health</Typography>
              <Divider sx={{ my: 1 }} />
              <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(health, null, 2)}</pre>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6">System Status</Typography>
              <Divider sx={{ my: 1 }} />
              <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(sys, null, 2)}</pre>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6">Redis Status</Typography>
              <Divider sx={{ my: 1 }} />
              <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(redis, null, 2)}</pre>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6">Services</Typography>
              <Divider sx={{ my: 1 }} />
              <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(services, null, 2)}</pre>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6">API Endpoints</Typography>
              <Divider sx={{ my: 1 }} />
              <Stack spacing={1}>
                {endpoints.map((ep) => (
                  <Button key={ep} variant="outlined" size="small" onClick={async () => {
                    try {
                      const res = await fetch(ep.startsWith('/api') ? ep : `/api${ep}`)
                      const text = await res.text()
                      alert(`${ep} => ${res.status}\n${text.slice(0, 200)}`)
                    } catch (e: any) {
                      alert(`${ep} => ERROR: ${e.message}`)
                    }
                  }}>
                    {ep}
                  </Button>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default SystemPage
