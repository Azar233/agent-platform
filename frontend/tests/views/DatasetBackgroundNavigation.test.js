import { flushPromises, shallowMount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import DatasetManagementPage from '@/views/DatasetManagementPage.vue'
import {
  discardDatasetProductStageApi,
  getDatasetOperationStatusApi,
  getDatasetVersionsApi,
} from '@/api/datasets'

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {} }),
}))

vi.mock('@/api/history', () => ({
  getScenes: vi.fn().mockResolvedValue({ scenes: [] }),
}))

vi.mock('@/api/handoffs', () => ({
  getAgentHandoffApi: vi.fn(),
  updateAgentHandoffApi: vi.fn(),
}))

vi.mock('@/api/datasets', () => ({
  archiveDatasetVersionApi: vi.fn(),
  commitDatasetProductTaskApi: vi.fn(),
  createDatasetVersionApi: vi.fn(),
  deleteDatasetProductTaskApi: vi.fn(),
  deleteDatasetVersionTaskApi: vi.fn(),
  deriveDatasetVersionTaskApi: vi.fn(),
  discardDatasetProductStageApi: vi.fn().mockResolvedValue(undefined),
  freezeDatasetVersionApi: vi.fn(),
  getDatasetOperationStatusApi: vi.fn(),
  getDatasetVersionApi: vi.fn(),
  getDatasetVersionsApi: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  importAvailableModelApi: vi.fn(),
  importBaselineDatasetApi: vi.fn(),
  stageDatasetProductImagesApi: vi.fn(),
  updateDatasetVersionApi: vi.fn(),
  validateDatasetVersionApi: vi.fn(),
}))

vi.mock('@/utils/visionPet', () => ({
  beginVisionPetTask: vi.fn(() => ({
    update: vi.fn(),
    finish: vi.fn(),
  })),
  getBackendErrorMessage: vi.fn((_error, fallback) => fallback),
}))

describe('DatasetManagementPage background operations', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.clearAllMocks()
    getDatasetVersionsApi.mockResolvedValue({ items: [], total: 0 })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('keeps polling an add-samples task after the dataset page unmounts', async () => {
    getDatasetOperationStatusApi.mockResolvedValue({
      task_id: 'task-add-samples',
      operation: 'add_samples',
      status: 'completed',
      progress: 100,
      message: '样本已添加',
      result: { dataset: { id: 9 } },
    })

    const wrapper = shallowMount(DatasetManagementPage, {
      global: {
        directives: { loading: () => {} },
        stubs: { 'el-table-column': true },
      },
    })
    await flushPromises()

    wrapper.vm.productDataset = { id: 9 }
    wrapper.vm.annotationStage = { staging_token: 'stage-in-use' }
    const operation = wrapper.vm.runDatasetOperation('添加商品', 'add_samples', () =>
      Promise.resolve({
        task_id: 'task-add-samples',
        operation: 'add_samples',
        status: 'running',
        progress: 20,
        message: '正在写入样本',
      }),
    )
    await flushPromises()

    wrapper.unmount()

    expect(discardDatasetProductStageApi).not.toHaveBeenCalled()

    await vi.advanceTimersByTimeAsync(180)
    await flushPromises()
    await vi.advanceTimersByTimeAsync(450)

    await expect(operation).resolves.toEqual({ dataset: { id: 9 } })
    expect(getDatasetOperationStatusApi).toHaveBeenCalledWith('task-add-samples')
    expect(discardDatasetProductStageApi).not.toHaveBeenCalled()
  })
})
