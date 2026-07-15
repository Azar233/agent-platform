import request from '@/utils/request'

export const getTaskList = (params) => request.get('/history/tasks', { params })
export const getTaskDetail = (taskId) => request.get(`/history/tasks/${taskId}`)
export const deleteTask = (taskId) => request.delete(`/history/tasks/${taskId}`)
export const getHistorySummary = () => request.get('/history/summary')
export const getScenes = () => request.get('/history/scenes')
