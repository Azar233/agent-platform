import request from '@/utils/request'

export function getPricesApi(datasetVersionId, q = '') {
  return request.get('/prices', {
    params: {
      dataset_version_id: datasetVersionId,
      ...(q ? { q } : {}),
    },
  })
}

export function getPriceApi(datasetVersionId, productId) {
  return request.get(`/prices/${productId}`, {
    params: { dataset_version_id: datasetVersionId },
  })
}

export function updatePriceApi(datasetVersionId, productId, data) {
  return request.put(`/prices/${productId}`, data, {
    params: { dataset_version_id: datasetVersionId },
  })
}

export function deletePriceApi(datasetVersionId, productId) {
  return request.delete(`/prices/${productId}`, {
    params: { dataset_version_id: datasetVersionId },
  })
}
