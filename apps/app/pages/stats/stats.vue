<template>
  <view class="container">
    <view class="header">
      <view class="welcome">
        <text class="title">我的成就</text>
        <text class="subtitle">记录你的探索点滴</text>
      </view>
    </view>

    <view v-if="stats" class="stats-overview">
      <view class="overview-card primary-card">
        <text class="card-title">总探索积分</text>
        <text class="card-value">{{ stats.total_score || 0 }}</text>
      </view>
      <view class="overview-card secondary-card">
        <text class="card-title">发现物种数</text>
        <text class="card-value">{{ stats.discoveries || 0 }}</text>
      </view>
    </view>

    <view v-if="stats" class="achievements-list">
      <view class="section-title">详细统计</view>
      
      <view class="stat-list-item">
        <view class="item-icon">🌟</view>
        <view class="item-content">
          <text class="item-name">最高稀有度</text>
          <text class="item-desc">历史发现的最罕见物种级别</text>
        </view>
        <view class="item-value">{{ computeMaxRarity() }} ★</view>
      </view>

      <view class="stat-list-item">
        <view class="item-icon">📅</view>
        <view class="item-content">
          <text class="item-name">最近发现</text>
          <text class="item-desc">上一次记录新物种的时间</text>
        </view>
        <view class="item-value">{{ computeLastDiscovery() }}</view>
      </view>
    </view>

    <view class="empty" v-if="!stats">
      <text>正在加载成就数据...</text>
    </view>
  </view>
</template>

<script>
const API_BASE = 'http://127.0.0.1:8000/api';

export default {
  data() {
    return {
      userId: 'default',
      stats: null,
      recentItems: []
    }
  },
  onShow() {
    this.fetchStats();
    this.fetchRecent();
  },
  methods: {
    async fetchStats() {
      try {
        const response = await uni.request({
          url: `${API_BASE}/users/${this.userId}/stats`,
          method: 'GET'
        });
        const res = Array.isArray(response) ? response[1] : response;
        if (res?.data?.success) {
          this.stats = res.data.data;
        }
      } catch (e) {
        console.error(e);
      }
    },
    async fetchRecent() {
      try {
        const response = await uni.request({
          url: `${API_BASE}/species/search`,
          data: { keyword: 'a', limit: 50 }
        });
        const res = Array.isArray(response) ? response[1] : response;
        if (res?.data?.success) {
          this.recentItems = res.data.data.results || [];
        }
      } catch(e) {}
    },
    computeMaxRarity() {
      if(!this.recentItems.length) return '-';
      return Math.max(...this.recentItems.map(i => i.rarity || 1));
    },
    computeLastDiscovery() {
      if(!this.recentItems.length) return '-';
      // Assume the first item in recent is the latest if backend sorted, else compute
      const dates = this.recentItems.map(i => i.created_date ? new Date(i.created_date) : 0).filter(Boolean);
      if(!dates.length) return '近期';
      return new Date(Math.max(...dates)).toLocaleDateString();
    }
  }
}
</script>

<style lang="scss">
page { background-color: #F3F4F6; }
.container { padding-bottom: 20px; }

.header {
  background: linear-gradient(135deg, #059669 0%, #10B981 100%);
  padding: 40px 20px 20px;
  color: white;
}
.title { font-size: 28px; font-weight: 800; display: block; margin-bottom: 5px; }
.subtitle { font-size: 14px; opacity: 0.9; }

.stats-overview {
  display: flex; gap: 15px; padding: 20px; margin-top: -10px;
}
.overview-card {
  flex: 1; border-radius: 16px; padding: 20px; display: flex; flex-direction: column;
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
}
.primary-card { background: white; border: 2px solid #059669; }
.secondary-card { background: #059669; color: white; }

.primary-card .card-title { color: #6B7280; font-size: 14px; }
.primary-card .card-value { color: #059669; font-size: 28px; font-weight: bold; margin-top: 8px; }

.secondary-card .card-title { opacity: 0.9; font-size: 14px; }
.secondary-card .card-value { font-size: 28px; font-weight: bold; margin-top: 8px; }

.achievements-list {
  padding: 0 20px;
}
.section-title { font-size: 18px; font-weight: bold; margin-bottom: 15px; }

.stat-list-item {
  background: white; padding: 15px; border-radius: 16px;
  display: flex; align-items: center; margin-bottom: 15px;
}
.item-icon { font-size: 24px; margin-right: 15px; background: #FFFBEB; padding: 10px; border-radius: 12px; }
.item-content { flex: 1; display: flex; flex-direction: column; }
.item-name { font-size: 16px; font-weight: bold; color: #111827; }
.item-desc { font-size: 12px; color: #6B7280; margin-top: 4px; }
.item-value { font-size: 16px; font-weight: bold; color: #059669; }

.empty { padding: 50px; text-align: center; color: #9CA3AF; }
</style>
