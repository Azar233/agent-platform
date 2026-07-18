import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'
import {
  useVisionPetStore,
  VISION_PET_DEFAULT_SIZE,
  VISION_PET_PREFERENCES_KEY,
} from '@/stores/visionPet'

describe('visionPet preferences', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('persists visibility and normalized size preferences', () => {
    const store = useVisionPetStore()
    store.setVisible(false)
    store.setSizePercent(118)

    expect(JSON.parse(localStorage.getItem(VISION_PET_PREFERENCES_KEY))).toEqual({
      visible: false,
      sizePercent: 120,
    })

    setActivePinia(createPinia())
    const restoredStore = useVisionPetStore()
    expect(restoredStore.visible).toBe(false)
    expect(restoredStore.sizePercent).toBe(120)
  })

  it('resets preferences without mixing them into task state resets', () => {
    const store = useVisionPetStore()
    store.setVisible(false)
    store.setSizePercent(130)
    store.reset()

    expect(store.visible).toBe(false)
    expect(store.sizePercent).toBe(130)

    store.resetPreferences()
    expect(store.visible).toBe(true)
    expect(store.sizePercent).toBe(VISION_PET_DEFAULT_SIZE)
  })
})
