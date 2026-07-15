import request from '@/utils/request'

export const getUserList = (params) => request.get('/user/list', { params })
export const getRoles = () => request.get('/user/roles')
export const updateProfile = (data) => request.put('/user/profile', data)
export const changePassword = (data) => request.put('/user/password', data)
