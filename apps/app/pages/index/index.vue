<template>
  <view class="device-container">
    <!-- Top Hardware Section: Lens and LEDs -->
    <view class="device-top">
      <view class="lens-bezel">
        <view class="main-lens">
          <view class="lens-glare"></view>
        </view>
      </view>
      <view class="status-lights">
        <view class="led led-red"></view>
        <view class="led led-yellow"></view>
        <view class="led led-green"></view>
      </view>
    </view>

    <!-- Header: LCD Screen Overview -->
    <view class="screen-bezel">
      <view class="lcd-screen">
        <view class="scanline"></view>
        <view class="welcome-text">
          <text class="glitch-title">生态终端 v1.0</text>
          <text class="sys-status">系统在线 // 正在连接数据库...</text>
        </view>
        
        <view class="stats-grid" v-if="userStats" @click="goStats">
          <view class="data-block">
            <text class="lcd-label">研究积分</text>
            <text class="lcd-num">{{ String(userStats.total_score || 0).padStart(4, '0') }}</text>
          </view>
          <view class="data-block">
            <text class="lcd-label">已录入</text>
            <text class="lcd-num">{{ String(userStats.discoveries || 0).padStart(3, '0') }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- Mid Section: Hardware Buttons -->
    <view class="control-panel">
      <!-- 游戏机十字键 (十字方向键) -->
      <view class="d-pad" @click="goTimeline">
        <view class="d-pad-vertical"></view>
        <view class="d-pad-horizontal"></view>
        <view class="d-pad-center">
            <view class="d-pad-dent"></view>
        </view>
      </view>
      
      <!-- A / B 圆形按键 -->
      <view class="action-buttons">
        <view class="action-btn-wrapper">
          <view class="round-btn btn-b" @click="switchTab('/pages/stats/stats')"></view>
          <text class="btn-label">成就</text>
        </view>
        <view class="action-btn-wrapper hint-up">
          <view class="round-btn btn-a" @click="switchTab('/pages/library/library')"></view>
          <text class="btn-label">图鉴库</text>
        </view>
      </view>
    </view>

    <!-- Recent Discoveries: Scan Results -->
    <view class="database-section">
      <view class="db-header">
        <text class="db-title">▶ 最近扫描记录</text>
        <text class="db-more" @click="switchTab('/pages/library/library')">[查看全部]</text>
      </view>
      
      <view class="scan-list" v-if="recentList.length > 0">
        <scroll-view scroll-x class="scan-scroll">
          <view class="scan-photo" v-for="(item, index) in recentList.slice(0, 5)" :key="index" @click="goDetail(item)">
            <image class="scan-img" :src="toImageUrl(item.source_image_path || item.image_path)" mode="aspectFill"></image>
            <view class="scan-overlay">
              <text class="scan-name">{{ item.chinese_name }}</text>
            </view>
          </view>
        </scroll-view>
      </view>
      
      <view class="empty-state" v-else>
        <text class="blinking-cursor">未发现任何数据_</text>
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
        console.error('获取状态失败:', e);
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
    // Used for the Type Badge UI
    getCategoryName(val) {
      const map = { plant: '草本', animal: '野生', mineral: '岩地' };
      return map[val] || val || '未知';
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
/* 整体设备外壳：正红配色致敬经典，使用深色阴影增加厚重感 */
page { 
  background-color: #A9262C; 
  /* 移除了导致中文字体发虚的 Courier New，恢复系统默认的高清无衬线黑体 */
}

.device-container { 
  padding-bottom: 20px; 
  background-color: #D32F2F;
  min-height: 100vh;
  box-shadow: inset 0 0 20px rgba(0,0,0,0.3);
}

/* 顶部：指示灯和主镜头 */
.device-top {
  display: flex;
  align-items: center;
  padding: 20px 20px 10px;
  background: linear-gradient(180deg, #E53935 0%, #D32F2F 100%);
  border-bottom: 3px solid #B71C1C;
}

.lens-bezel {
  width: 70px;
  height: 70px;
  background-color: #E0E0E0;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 4px 6px rgba(0,0,0,0.3), inset 0 -2px 5px rgba(0,0,0,0.2);
  border: 2px solid #9E9E9E;
}

.main-lens {
  width: 50px;
  height: 50px;
  background: radial-gradient(circle at 30% 30%, #4FC3F7, #0288D1 60%, #01579B);
  border-radius: 50%;
  position: relative;
  box-shadow: inset 0 0 10px rgba(0,0,0,0.8);
}

.lens-glare {
  position: absolute;
  top: 8px;
  left: 8px;
  width: 15px;
  height: 15px;
  background-color: rgba(255, 255, 255, 0.6);
  border-radius: 50%;
}

.status-lights {
  display: flex;
  gap: 10px;
  margin-left: 20px;
  align-self: flex-start;
  margin-top: 10px;
}

.led {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0,0,0,0.3), inset 0 -2px 4px rgba(0,0,0,0.3);
  border: 1px solid #000;
}
.led-red { background: radial-gradient(circle at 30% 30%, #EF5350, #C62828); }
.led-yellow { background: radial-gradient(circle at 30% 30%, #FFEE58, #F9A825); }
.led-green { background: radial-gradient(circle at 30% 30%, #66BB6A, #2E7D32); }

/* 主屏幕区域：复古黑白LCD绿屏 */
.screen-bezel {
  background-color: #E0E0E0;
  margin: 20px;
  padding: 15px;
  border-radius: 12px 12px 12px 40px; 
  box-shadow: 0 5px 10px rgba(0,0,0,0.2);
  border: 2px solid #757575;
}

.lcd-screen {
  background-color: #9BBC0F;
  border-radius: 8px;
  padding: 15px;
  box-shadow: inset 0 0 10px rgba(0,0,0,0.3);
  position: relative;
  overflow: hidden;
}

.scanline {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.04) 50%); /* 调低透明度提升清晰度 */
  background-size: 100% 4px;
  pointer-events: none;
}

.welcome-text { margin-bottom: 20px; position: relative; z-index: 1; }
.glitch-title { font-size: 20px; font-weight: bold; color: #0F380F; display: block; letter-spacing: 1px; }
.sys-status { font-size: 10px; color: #306230; margin-top: 2px; display: block; }

.stats-grid {
  display: flex; gap: 15px; position: relative; z-index: 1;
}
.data-block {
  flex: 1; border: 2px dashed #306230; padding: 10px;
}
.lcd-label { font-size: 11px; font-weight: bold; color: #306230; display: block; margin-bottom: 5px; }
.lcd-num { font-size: 24px; font-weight: bold; color: #0F380F; }

/* 硬件按钮区 */
.control-panel {
  display: flex; justify-content: space-around; align-items: center; padding: 10px 30px 30px;
}

/* 经典十字键 (D-Pad) */
.d-pad {
  position: relative;
  width: 90px;
  height: 90px;
}
.d-pad-vertical {
  position: absolute;
  top: 0; left: 30px;
  width: 30px; height: 90px;
  background: #212121;
  border-radius: 4px;
  box-shadow: -2px 0 0 #424242, 2px 0 0 #424242;
}
.d-pad-horizontal {
  position: absolute;
  top: 30px; left: 0;
  width: 90px; height: 30px;
  background: #212121;
  border-radius: 4px;
  box-shadow: 0 -2px 0 #424242, 0 2px 0 #424242;
}
.d-pad-center {
  position: absolute;
  top: 30px; left: 30px;
  width: 30px; height: 30px;
  background: #212121;
  display: flex; justify-content: center; align-items: center;
}
.d-pad-dent {
  width: 16px; height: 16px;
  border-radius: 50%;
  background: rgba(0,0,0,0.3);
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.5);
}
.d-pad:active {
  transform: scale(0.96);
}

/* A/B 按钮区 */
.action-buttons {
  display: flex; gap: 15px; position: relative; top: 10px;
}
.action-btn-wrapper {
  display: flex; flex-direction: column; align-items: center;
}
.hint-up {
  position: relative; top: -20px;
}
.round-btn {
  width: 44px; height: 44px; border-radius: 50%;
  box-shadow: 0 4px 0 #111, 0 6px 10px rgba(0,0,0,0.5);
  border: 2px solid #212121;
  margin-bottom: 8px;
}
.round-btn:active {
  transform: translateY(4px); box-shadow: 0 0 0 #000, 0 2px 5px rgba(0,0,0,0.5);
}
.btn-a { background: #212121; } /* 黑色按钮 */
.btn-b { background: #1E88E5; } /* 蓝色按钮 */

.btn-label { font-size: 12px; font-weight: bold; color: rgba(255,255,255,0.9); }

/* 数据库列表：图鉴条目 */
.database-section {
  background: #E0E0E0;
  margin: 0 20px; padding: 15px; border-radius: 12px;
  box-shadow: inset 0 2px 5px rgba(0,0,0,0.2), 0 4px 10px rgba(0,0,0,0.3);
  border: 2px solid #757575;
}

.db-header {
  display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 15px;
  border-bottom: 2px solid #9E9E9E; padding-bottom: 5px;
}
.db-title { font-size: 14px; font-weight: bold; color: #212121; }
.db-more { font-size: 12px; color: #616161; font-weight: bold; }

.scan-scroll { width: 100%; white-space: nowrap; padding-bottom: 5px; }
.scan-photo {
  display: inline-block;
  width: 130px;
  height: 110px;
  margin-right: 15px;
  position: relative;
  overflow: hidden;
  vertical-align: top;
  border: 2px solid #424242;
  border-radius: 10px;
  box-shadow: 2px 2px 0 #424242;
  background: #000;
}
.scan-img {
  width: 100%;
  height: 100%;
  display: block;
  opacity: 0.92;
}
.scan-overlay {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 8px 10px;
  background: linear-gradient(to top, rgba(15, 56, 15, 0.88), rgba(15, 56, 15, 0));
  pointer-events: none;
}
.scan-name {
  display: block;
  font-size: 13px;
  font-weight: bold;
  color: #fff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-state { padding: 30px 0; text-align: center; color: #757575; font-size: 12px; font-weight: bold; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
.blinking-cursor::after { content: '_'; animation: blink 1s step-end infinite; }
</style>
