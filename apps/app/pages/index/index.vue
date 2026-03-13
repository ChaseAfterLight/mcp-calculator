<template>
  <view class="container">
    <!-- Header: Overview -->
    <view class="header">
      <view class="welcome">
        <text class="title">大自然图鉴</text>
        <text class="subtitle">记录你的每次探索</text>
      </view>
      <view class="stats" v-if="userStats" @click="goStats">
        <view class="stat-card">
          <text class="stat-num">{{ userStats.total_score || 0 }}</text>
          <text class="stat-label">总积分</text>
        </view>
        <view class="stat-card">
          <text class="stat-num">{{ userStats.discoveries || 0 }}</text>
          <text class="stat-label">已发现</text>
        </view>
      </view>
    </view>

    <!-- Quick Links -->
    <view class="quick-links">
      <!-- <view class="link-item" @click="switchTab('/pages/register/register')">
        <view class="icon bg-green">➕</view>
        <text>新建记录</text>
      </view> -->
      <view class="link-item" @click="switchTab('/pages/library/library')">
        <view class="icon bg-blue">📚</view>
        <text>图鉴库</text>
      </view>
      <view class="link-item" @click="switchTab('/pages/stats/stats')">
        <view class="icon bg-yellow">🏆</view>
        <text>我的成就</text>
      </view>
      <view class="link-item" @click="goTimeline">
        <view class="icon bg-purple">🕒</view>
        <text>时间线</text>
      </view>
    </view>

    <!-- Recent Discoveries -->
    <view class="section-container">
      <view class="section-header">
        <text class="section-title">最近发现</text>
        <text class="see-all" @click="switchTab('/pages/library/library')">查看全部 ></text>
      </view>
      
      <view class="recent-list" v-if="recentList.length > 0">
        <!-- Horizontal scroll or just a grid. Let's do horizontal scroll for modern feel -->
        <scroll-view scroll-x class="recent-scroll">
          <view class="recent-card" v-for="(item, index) in recentList.slice(0, 5)" :key="index" @click="goDetail(item)">
            <image class="recent-img" :src="toImageUrl(item.image_path)" mode="aspectFill"></image>
            <view class="recent-info">
              <text class="recent-name">{{ item.chinese_name }}</text>
              <text class="recent-cat">{{ getCategoryName(item.category) }}</text>
            </view>
          </view>
        </scroll-view>
      </view>
      
      <view class="empty-state" v-else>
        <text>暂无发现，去探索世界吧！</text>
      </view>
    </view>
  </view>
</template>

<script>
const API_BASE = 'http://127.0.0.1:8000/api';
const SERVER_BASE = API_BASE.replace(/\/api$/, '');

export default {
  data() {
    return {
      userId: 'default',
      userStats: null,
      recentList: []
    }
  },
  onShow() {
    this.fetchUserStats();
    this.loadRecent();
  },
  methods: {
    async fetchUserStats() {
      try {
        const response = await uni.request({
          url: `${API_BASE}/users/${this.userId}/stats`,
          method: 'GET'
        });
        const res = Array.isArray(response) ? response[1] : response;
        if (res && res.data && res.data.success) {
          this.userStats = res.data.data;
        }
      } catch (e) {
        console.error('Failed to fetch stats:', e);
      }
    },
    async loadRecent() {
      try {
        const response = await uni.request({
          url: `${API_BASE}/species/search`,
          method: 'GET',
          data: { keyword: 'a', limit: 5 }
        });
        const res = Array.isArray(response) ? response[1] : response;
        if (res && res.data && res.data.success) {
          this.recentList = res.data.data.results || [];
        }
      } catch (e) {}
    },
    switchTab(url) {
      uni.switchTab({ url });
    },
    goStats() { this.switchTab('/pages/stats/stats'); },
    goTimeline() { uni.navigateTo({ url: '/pages/timeline/timeline' }); },
    goDetail(item) {
      if (!item || !item.card_id) return;
      uni.navigateTo({
        url: `/pages/detail/detail?card_id=${encodeURIComponent(item.card_id)}`
      });
    },
    getCategoryName(val) {
      const map = { plant: '植物', animal: '动物', mineral: '矿物' };
      return map[val] || val;
    },
    toImageUrl(imagePath) {
      if (!imagePath) return '';
      if (/^https?:\/\//.test(imagePath)) return imagePath;
      const normalized = String(imagePath).replace(/\\/g, '/').replace(/^\/+/, '');
      return `${SERVER_BASE}/${normalized}`;
    }
  }
}
</script>

<style lang="scss">
page { background-color: #F3F4F6; }
.container { padding-bottom: 20px; }

/* Header */
.header {
  background: white;
  padding: 40px 20px 20px;
  border-bottom-left-radius: 20px;
  border-bottom-right-radius: 20px;
  box-shadow: 0 4px 10px rgba(0,0,0,0.03);
  margin-bottom: 20px;
}
.title { font-size: 26px; font-weight: 800; display: block; color: #111827; }
.subtitle { font-size: 14px; color: #6B7280; margin-top: 4px; display: block; }
.stats {
  display: flex; gap: 15px; margin-top: 20px;
}
.stat-card {
  flex: 1; background: #Edfaf3; padding: 15px; border-radius: 16px;
  display: flex; flex-direction: column;
}
.stat-num { font-size: 24px; font-weight: bold; color: #059669; }
.stat-label { font-size: 12px; color: #374151; opacity: 0.8; margin-top: 4px; }

/* Quick Links */
.quick-links {
  display: flex; justify-content: space-around; padding: 0 10px; margin-bottom: 30px;
}
.link-item {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
}
.icon {
  width: 50px; height: 50px; border-radius: 16px; display: flex; align-items: center;
  justify-content: center; font-size: 24px;
}
.bg-green { background: #Edfaf3; }
.bg-blue { background: #Eef2ff; }
.bg-yellow { background: #Fffbeb; }
.bg-purple { background: #F3e8ff; }
.link-item text { font-size: 12px; color: #374151; font-weight: 500; }

/* Section */
.section-container { padding: 0 20px; }
.section-header {
  display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 15px;
}
.section-title { font-size: 18px; font-weight: bold; color: #111827; }
.see-all { font-size: 13px; color: #6B7280; font-weight: 500; }

.recent-scroll { width: 100%; white-space: nowrap; padding-bottom: 10px; }
.recent-card {
  display: inline-block; width: 140px; margin-right: 15px;
  background: white; border-radius: 16px; overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.03); vertical-align: top;
}
.recent-img { width: 140px; height: 140px; background: #E5E7EB; }
.recent-info { padding: 10px; }
.recent-name { font-size: 15px; font-weight: bold; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.recent-cat { font-size: 11px; color: #6B7280; margin-top: 4px; display: block; }

.empty-state { padding: 40px 0; text-align: center; color: #9CA3AF; font-size: 14px; }
</style>
