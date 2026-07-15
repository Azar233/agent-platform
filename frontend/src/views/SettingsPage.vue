<template>
  <div class="settings-page">
    <header class="page-header">
      <div>
        <span class="vp-kicker">Account</span>
        <h1>账号设置</h1>
        <p>维护个人联系方式与登录密码。用户名和角色由管理员统一管理。</p>
      </div>
    </header>

    <section class="settings-grid">
      <article class="settings-card profile-card">
        <header><div class="card-icon"><el-icon><User /></el-icon></div><div><h2>个人资料</h2><p>用于账号识别与业务通知</p></div></header>
        <el-form ref="profileFormRef" :model="profileForm" :rules="profileRules" label-position="top">
          <div class="form-grid">
            <el-form-item label="用户名"><el-input v-model="profileForm.username" disabled /></el-form-item>
            <el-form-item label="账号角色"><el-input :model-value="roleText" disabled /></el-form-item>
            <el-form-item label="邮箱" prop="email"><el-input v-model.trim="profileForm.email" placeholder="name@example.com" /></el-form-item>
            <el-form-item label="手机号" prop="phone"><el-input v-model.trim="profileForm.phone" placeholder="选填" maxlength="20" /></el-form-item>
            <el-form-item label="注册时间"><el-input :model-value="formatDate(profileForm.created_at)" disabled /></el-form-item>
            <el-form-item label="最近登录"><el-input :model-value="formatDate(profileForm.last_login_at)" disabled /></el-form-item>
          </div>
          <div class="form-actions"><el-button type="primary" :loading="profileLoading" @click="saveProfile">保存个人资料</el-button></div>
        </el-form>
      </article>

      <article class="settings-card password-card">
        <header><div class="card-icon security"><el-icon><Lock /></el-icon></div><div><h2>登录安全</h2><p>定期更新密码可降低账号风险</p></div></header>
        <el-alert title="修改成功后当前登录不会退出，新密码将在下次登录时生效。" type="info" :closable="false" show-icon />
        <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-position="top">
          <el-form-item label="当前密码" prop="old_password"><el-input v-model="passwordForm.old_password" type="password" show-password autocomplete="current-password" /></el-form-item>
          <el-form-item label="新密码" prop="new_password"><el-input v-model="passwordForm.new_password" type="password" show-password autocomplete="new-password" /></el-form-item>
          <el-form-item label="确认新密码" prop="confirm_password"><el-input v-model="passwordForm.confirm_password" type="password" show-password autocomplete="new-password" /></el-form-item>
          <div class="form-actions"><el-button type="primary" :loading="passwordLoading" @click="savePassword">更新登录密码</el-button></div>
        </el-form>
      </article>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { Lock, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getUserInfoApi } from '@/api/auth'
import { changePassword as changePasswordApi, updateProfile as updateProfileApi } from '@/api/user'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const profileFormRef = ref()
const passwordFormRef = ref()
const profileLoading = ref(false)
const passwordLoading = ref(false)
const profileForm = reactive({ username: '', email: '', phone: '', roles: [], created_at: null, last_login_at: null })
const passwordForm = reactive({ old_password: '', new_password: '', confirm_password: '' })
const roleText = computed(() => profileForm.roles?.length ? profileForm.roles.join('、') : '普通用户')
const profileRules = {
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }, { type: 'email', message: '邮箱格式不正确', trigger: ['blur', 'change'] }],
  phone: [{ pattern: /^$|^[+\d][\d\s-]{5,19}$/, message: '手机号格式不正确', trigger: 'blur' }],
}
const passwordRules = {
  old_password: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' }, { min: 6, max: 100, message: '密码长度为 6-100 个字符', trigger: 'blur' },
    { validator: (_rule, value, callback) => value === passwordForm.old_password ? callback(new Error('新密码不能与当前密码相同')) : callback(), trigger: 'blur' },
  ],
  confirm_password: [{ required: true, message: '请再次输入新密码', trigger: 'blur' }, { validator: (_rule, value, callback) => value !== passwordForm.new_password ? callback(new Error('两次输入的新密码不一致')) : callback(), trigger: ['blur', 'change'] }],
}

function formatDate(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(value))
}

function fillProfile(user) {
  Object.assign(profileForm, { username: user.username || '', email: user.email || '', phone: user.phone || '', roles: user.roles || [], created_at: user.created_at, last_login_at: user.last_login_at })
}

async function loadProfile() {
  try {
    const user = await getUserInfoApi()
    fillProfile(user)
    userStore.setUser(user)
  } catch { ElMessage.error('个人资料加载失败') }
}

async function saveProfile() {
  if (!await profileFormRef.value.validate().catch(() => false)) return
  profileLoading.value = true
  try {
    const data = await updateProfileApi({ email: profileForm.email, phone: profileForm.phone })
    fillProfile({ ...profileForm, ...data.user })
    userStore.setUser({ ...userStore.user, ...data.user })
    ElMessage.success('个人资料已更新')
  } finally { profileLoading.value = false }
}

async function savePassword() {
  if (!await passwordFormRef.value.validate().catch(() => false)) return
  passwordLoading.value = true
  try {
    await changePasswordApi({ old_password: passwordForm.old_password, new_password: passwordForm.new_password })
    Object.assign(passwordForm, { old_password: '', new_password: '', confirm_password: '' })
    passwordFormRef.value.clearValidate()
    ElMessage.success('密码修改成功')
  } finally { passwordLoading.value = false }
}

onMounted(loadProfile)
</script>

<style lang="scss" scoped>
.settings-page { min-height: 100%; padding: 32px; display: flex; flex-direction: column; gap: 18px; }.page-header { padding: 30px 32px; border: 1px solid $border-color; border-radius: $border-radius-lg; background: $surface-color; box-shadow: $shadow-sm; }.page-header h1 { margin: 8px 0 0; color: $text-primary; font-size: 38px; font-weight: 600; letter-spacing: -.045em; }.page-header p { margin: 9px 0 0; color: $text-secondary; }
.settings-grid { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(340px, .75fr); gap: 16px; align-items: start; }.settings-card { padding: 26px; border: 1px solid $border-color; border-radius: $border-radius-md; background: $surface-color; box-shadow: $shadow-sm; }.settings-card > header { margin-bottom: 24px; display: flex; align-items: center; gap: 13px; }.settings-card h2 { margin: 0; color: $text-primary; font-size: 19px; font-weight: 600; }.settings-card header p { margin: 4px 0 0; color: $text-secondary; font-size: 12px; }.card-icon { width: 42px; height: 42px; display: grid; place-items: center; border-radius: 13px; color: $primary-color; background: $primary-soft; font-size: 19px; }.card-icon.security { color: #8944ab; background: rgba(175,82,222,.12); }.form-grid { display: grid; grid-template-columns: repeat(2, 1fr); column-gap: 16px; }.form-actions { padding-top: 4px; display: flex; justify-content: flex-end; }.password-card .el-alert { margin-bottom: 20px; }
@media (max-width: 1000px) { .settings-grid { grid-template-columns: 1fr; } }
@media (max-width: 700px) { .settings-page { padding: 12px; }.page-header, .settings-card { padding: 24px; }.form-grid { grid-template-columns: 1fr; } }
</style>
