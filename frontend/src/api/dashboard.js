import request from '@/utils/request'

export const getStatistics = (days = 30) => request.get('/dashboard/statistics', { params: { days } })
export const getTrend = (days = 30) => request.get('/dashboard/trend', { params: { days } })
export const getClassDistribution = (days = 30) => request.get('/dashboard/class-dist', { params: { days } })
export const getSceneDistribution = (days = 30) => request.get('/dashboard/scene-dist', { params: { days } })
export const getTypeDistribution = (days = 30) => request.get('/dashboard/type-dist', { params: { days } })
