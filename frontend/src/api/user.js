import request from '@/utils/request'

export const getUserList = (params) => request.get('/user/list', { params })
export const getRoles = () => request.get('/user/roles')
export const updateProfile = (data) => request.put('/user/profile', data)
export const uploadAvatar = (data) => request.post('/user/avatar', data, {
  headers: { 'Content-Type': 'multipart/form-data' },
})
export const changePassword = (data) => request.put('/user/password', data)
