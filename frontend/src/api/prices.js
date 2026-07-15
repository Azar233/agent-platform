import request from '@/utils/request'

/**
 * 获取所有商品价格
 * @param {string} [q] 搜索关键字（商品中文名或条码）
 */
export function getPricesApi(q) {
  return request.get('/prices', { params: q ? { q } : undefined })
}

/**
 * 获取单个商品价格
 * @param {number} categoryId
 */
export function getPriceApi(categoryId) {
  return request.get(`/prices/${categoryId}`)
}

/**
 * 创建单个商品价格
 * @param {Object} data
 */
export function createPriceApi(data) {
  return request.post('/prices', data)
}

/**
 * 更新单个商品价格
 * @param {number} categoryId
 * @param {Object} data
 */
export function updatePriceApi(categoryId, data) {
  return request.put(`/prices/${categoryId}`, data)
}

/**
 * 删除单个商品价格
 * @param {number} categoryId
 */
export function deletePriceApi(categoryId) {
  return request.delete(`/prices/${categoryId}`)
}

/**
 * 批量删除商品价格
 * @param {number[]} categoryIds
 */
export function batchDeletePricesApi(categoryIds) {
  return request.post('/prices/batch-delete', categoryIds)
}
