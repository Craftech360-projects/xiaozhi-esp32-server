<script lang="ts" setup>
import type { ChatSession } from '@/api/chat-history/types'
import { computed, onMounted, ref } from 'vue'
import { getChatSessions } from '@/api/chat-history/chat-history'

defineOptions({
  name: 'ChatHistory',
})

// 接收props
interface Props {
  agentId?: string
}

const props = withDefaults(defineProps<Props>(), {
  agentId: 'default'
})

// 获取屏幕边界到安全区域距离
let safeAreaInsets: any
let systemInfo: any

// #ifdef MP-WEIXIN
systemInfo = uni.getWindowInfo()
safeAreaInsets = systemInfo.safeArea
  ? {
      top: systemInfo.safeArea.top,
      right: systemInfo.windowWidth - systemInfo.safeArea.right,
      bottom: systemInfo.windowHeight - systemInfo.safeArea.bottom,
      left: systemInfo.safeArea.left,
    }
  : null
// #endif

// #ifndef MP-WEIXIN
systemInfo = uni.getSystemInfoSync()
safeAreaInsets = systemInfo.safeAreaInsets
// #endif

// 聊天会话数据
const sessionList = ref<ChatSession[]>([])
const loading = ref(false)
const loadingMore = ref(false)
const hasMore = ref(true)
const currentPage = ref(1)
const pageSize = 10

// 使用传入的智能体ID
const currentAgentId = computed(() => {
  return props.agentId
})

// 加载聊天会话列表
async function loadChatSessions(page = 1, isRefresh = false) {
  try {
    console.log('获取聊天会话列表', { page, isRefresh })

    // 检查是否有当前选中的智能体
    if (!currentAgentId.value) {
      console.warn('没有选中的智能体')
      sessionList.value = []
      return
    }

    if (page === 1) {
      loading.value = true
    }
    else {
      loadingMore.value = true
    }

    const response = await getChatSessions(currentAgentId.value, {
      page,
      limit: pageSize,
    })

    // Debug logging for frontend timestamps
    if (response.list && response.list.length > 0) {
      const firstSession = response.list[0]
      console.log('🔥 SIDEBAR TIMESTAMP DEBUG:', {
        sessionId: firstSession.sessionId,
        sessionCreatedAt: firstSession.createdAt,
        type: typeof firstSession.createdAt,
        formatted: formatTime(firstSession.createdAt)
      })
    }

    if (page === 1) {
      sessionList.value = response.list || []
    }
    else {
      sessionList.value.push(...(response.list || []))
    }

    // 更新分页信息
    hasMore.value = (response.list?.length || 0) === pageSize
    currentPage.value = page
  }
  catch (error) {
    console.error('获取聊天会话列表失败:', error)
    if (page === 1) {
      sessionList.value = []
    }
  }
  finally {
    loading.value = false
    loadingMore.value = false
  }
}

// 暴露给父组件的刷新方法
async function refresh() {
  currentPage.value = 1
  hasMore.value = true
  await loadChatSessions(1, true)
}

// 暴露给父组件的加载更多方法
async function loadMore() {
  if (!hasMore.value || loadingMore.value) {
    return
  }
  await loadChatSessions(currentPage.value + 1)
}

// Format time to match chat detail display format (HH:MM) - EXACT COPY
function formatTime(timeStr: string) {
  const date = new Date(timeStr)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

// 进入聊天详情
function goToChatDetail(session: ChatSession) {
  uni.navigateTo({
    url: `/pages/chat-history/detail?sessionId=${session.sessionId}&agentId=${currentAgentId.value}`,
  })
}

onMounted(async () => {
  // 智能体已简化为默认

  loadChatSessions(1)
})

// 暴露方法给父组件
defineExpose({
  refresh,
  loadMore,
})
</script>

<template>
  <view class="chat-history-container" style="background: #f5f7fb; min-height: 100%;">
    <!-- 加载状态 -->
    <view v-if="loading && sessionList.length === 0" class="loading-container">
      <wd-loading color="#336cff" />
      <text class="loading-text">
        加载中...
      </text>
    </view>

    <!-- 会话列表 -->
    <view v-else-if="sessionList.length > 0" class="session-container">
      <!-- 聊天会话列表 -->
      <view class="session-list">
        <view
          v-for="session in sessionList"
          :key="session.sessionId"
          class="session-item"
          @click="goToChatDetail(session)"
        >
          <view class="session-card">
            <view class="session-info">
              <view class="session-header">
                <text class="session-title">
                  对话记录 {{ session.sessionId.substring(0, 8) }}...
                </text>
                <text class="session-time">
                  {{ formatTime(session.createdAt) }}
                </text>
              </view>
              <view class="session-meta">
                <text class="chat-count">
                  共 {{ session.chatCount }} 条对话
                </text>
              </view>
            </view>
            <wd-icon name="arrow-right" custom-class="arrow-icon" />
          </view>
        </view>
      </view>

      <!-- 加载更多状态 -->
      <view v-if="loadingMore" class="loading-more">
        <wd-loading color="#336cff" size="24" />
        <text class="loading-more-text">
          加载中...
        </text>
      </view>

      <!-- 没有更多数据 -->
      <view v-else-if="!hasMore && sessionList.length > 0" class="no-more">
        <text class="no-more-text">
          没有更多数据了
        </text>
      </view>
    </view>

    <!-- 空状态 -->
    <view v-else-if="!loading" class="empty-state">
      <wd-icon name="chat" custom-class="empty-icon" />
      <text class="empty-text">
        暂无聊天记录
      </text>
      <text class="empty-desc">
        与智能体的对话记录会显示在这里
      </text>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.chat-history-container {
  position: relative;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100rpx 40rpx;
}

.loading-text {
  margin-top: 20rpx;
  font-size: 28rpx;
  color: #666666;
}

.loading-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 30rpx;
  gap: 16rpx;

  .loading-more-text {
    font-size: 26rpx;
    color: #666666;
  }
}

.no-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 30rpx;

  .no-more-text {
    font-size: 26rpx;
    color: #999999;
  }
}

.navbar-section {
  background: #ffffff;
}

.status-bar {
  background: #ffffff;
  width: 100%;
}

.session-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
  padding: 20rpx;
  box-sizing: border-box;
}

.session-item {
  background: #fbfbfb;
  border-radius: 20rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
  border: 1rpx solid #eeeeee;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s ease;

  &:active {
    background: #f8f9fa;
  }
}

.session-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx;

  .session-info {
    flex: 1;

    .session-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12rpx;

      .session-title {
        font-size: 32rpx;
        font-weight: 600;
        color: #232338;
        max-width: 70%;
        word-break: break-all;
      }

      .session-time {
        font-size: 24rpx;
        color: #9d9ea3;
      }
    }

    .session-meta {
      .chat-count {
        font-size: 28rpx;
        color: #65686f;
      }
    }
  }

  :deep(.arrow-icon) {
    font-size: 24rpx;
    color: #c7c7cc;
    margin-left: 16rpx;
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100rpx 40rpx;
  text-align: center;

  :deep(.empty-icon) {
    font-size: 120rpx;
    color: #d9d9d9;
    margin-bottom: 32rpx;
  }

  .empty-text {
    font-size: 32rpx;
    color: #666666;
    margin-bottom: 16rpx;
    font-weight: 500;
  }

  .empty-desc {
    font-size: 26rpx;
    color: #999999;
    line-height: 1.5;
  }
}
</style>
