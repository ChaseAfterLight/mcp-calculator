<template>
  <view class="device-wrapper">

    <!-- 主屏幕：LCD 绿色统计区 -->
    <view class="screen-box">
      <view class="lcd-screen">
        <view class="scanline"></view>
        <view class="lcd-header">
          <text class="sys-time">系统时间: {{ currentTime }}</text>
          <text class="sys-msg">运行状态: 正常_</text>
        </view>
        
        <view v-if="stats" class="hud-stats">
          <view class="hud-item main-hud">
            <text class="hud-label">总研究点数 >></text>
            <text class="hud-value bg-value">{{ String(stats.total_score || 0).padStart(5, '0') }}</text>
          </view>
          
          <view class="hud-divider"></view>
          
          <view class="hud-sub-grid">
            <view class="hud-item">
              <text class="hud-label">物种记录</text>
              <text class="hud-value">{{ String(stats.discoveries || 0).padStart(3, '0') }}</text>
            </view>
            <view class="hud-item">
              <text class="hud-label">评级 MAX</text>
              <text class="hud-value">LV.{{ computeMaxRarity() }}</text>
            </view>
          </view>
        </view>

        <view class="empty-lcd" v-else>
          <text class="blinking-cursor">正在同步数据...</text>
        </view>
      </view>
    </view>

    <!-- 详细面板：带有物理质感的卡片 -->
    <view class="panel-section">
      <view class="panel-header">
        <text class="panel-title">同步记录 // SYSTEM_LOGS</text>
      </view>
      
      <view class="module-list" v-if="stats">
        <view class="hardware-module">
          <view class="module-icon bg-yellow">★</view>
          <view class="module-info">
             <text class="mod-name">最高稀有度发现</text>
             <text class="mod-desc">数据库收录的最高评级</text>
          </view>
          <view class="mod-data box-data">R:{{ computeMaxRarity() }}</view>
        </view>

        <view class="hardware-module">
          <view class="module-icon bg-blue">◎</view>
          <view class="module-info">
             <text class="mod-name">最后同步时间</text>
             <text class="mod-desc">最近一次有效数据扫描</text>
          </view>
          <view class="mod-data border-data">{{ computeLastDiscovery() }}</view>
        </view>
      </view>
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
      currentTime: '00:00:00'
    }
  },
  onShow() {
    this.fetchStats();
    this.updateTime();
    setInterval(this.updateTime, 1000);
  },
  methods: {
    updateTime() {
      const d = new Date();
      this.currentTime = `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}:${String(d.getSeconds()).padStart(2,'0')}`;
    },
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
    computeMaxRarity() {
      return String(this.stats?.max_rarity || 0);
    },
    computeLastDiscovery() {
      const raw = this.stats?.latest_discovery?.generated_at || this.stats?.last_discovery_at;
      if(!raw) return 'NONE';
      const maxDate = new Date(raw);
      if (Number.isNaN(maxDate.getTime())) return '近期';
      return `${maxDate.getMonth()+1}/${maxDate.getDate()}`;
    }
  }
}
</script>

<style lang="scss">
page { 
  background-color: #A9262C; 
}

.device-wrapper {
  background-color: #D32F2F;
  min-height: 100vh;
  padding-bottom: 20px;
  box-shadow: inset 0 0 20px rgba(0,0,0,0.3);
}

.device-header {
  padding: 30px 20px 10px;
  background: linear-gradient(180deg, #E53935 0%, #D32F2F 100%);
  border-bottom: 3px solid #B71C1C;
}

.header-leds { display: flex; align-items: center; gap: 15px; }
.led { width: 16px; height: 16px; border-radius: 50%; border: 2px solid #212121; box-shadow: 0 2px 4px rgba(0,0,0,0.4); }
.blue-led { background: radial-gradient(circle at 30% 30%, #4FC3F7, #0288D1); box-shadow: 0 0 8px #0288D1; }
.glitch-title { font-size: 20px; font-weight: bold; color: #FFF; text-shadow: 2px 2px 0 #212121; }

/* 屏幕区域 */
.screen-box {
  background-color: #E0E0E0;
  margin: 20px; padding: 15px;
  border-radius: 12px; 
  box-shadow: inset 0 2px 5px rgba(0,0,0,0.2), 0 5px 10px rgba(0,0,0,0.3);
  border: 2px solid #757575;
}

.lcd-screen {
  background-color: #9BBC0F;
  border-radius: 8px;
  padding: 15px;
  box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
  position: relative;
  /* 移除 overflow: hidden 以防止 iOS 渲染时文字发虚模糊，scanline 通过 inherit 限制圆角内 */
}

.scanline {
  position: absolute; top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.04) 50%);
  background-size: 100% 4px; pointer-events: none;
  border-radius: inherit;
}

.lcd-header {
  display: flex; justify-content: space-between; border-bottom: 2px dashed #306230; padding-bottom: 5px; margin-bottom: 15px;
  position: relative; z-index: 1;
}
.sys-time, .sys-msg { font-size: 10px; font-weight: bold; color: #306230; }

.hud-stats { position: relative; z-index: 1; }
.hud-item { display: flex; flex-direction: column; }
.main-hud { margin-bottom: 15px; }
.hud-label { font-size: 12px; font-weight: bold; color: #306230; margin-bottom: 5px; }
.hud-value { font-size: 20px; font-weight: 900; color: #0F380F; }
.bg-value { font-size: 32px; letter-spacing: 2px; }

.hud-divider { height: 2px; background: #306230; margin-bottom: 15px; }

.hud-sub-grid { display: flex; justify-content: space-between; }


.empty-lcd { padding: 40px 0; text-align: center; color: #0F380F; font-size: 14px; position: relative; z-index: 1; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
.blinking-cursor::after { content: '_'; animation: blink 1s step-end infinite; }

/* 面板区域 */
.panel-section {
  background: #E0E0E0;
  margin: 0 20px; padding: 15px; border-radius: 12px;
  box-shadow: inset 0 2px 5px rgba(0,0,0,0.2), 0 4px 10px rgba(0,0,0,0.3);
  border: 2px solid #757575;
}
.panel-header { border-bottom: 2px solid #9E9E9E; padding-bottom: 5px; margin-bottom: 15px; }
.panel-title { font-size: 14px; font-weight: bold; color: #212121; }

.module-list { display: flex; flex-direction: column; gap: 15px; }
.hardware-module {
  background: #FAFAFA; border: 2px solid #424242; border-radius: 8px;
  padding: 12px; display: flex; align-items: center; gap: 12px;
  box-shadow: 2px 2px 0 #424242;
}

.module-icon {
  width: 40px; height: 40px; border-radius: 8px; border: 2px solid #212121;
  display: flex; justify-content: center; align-items: center;
  font-size: 20px; font-weight: bold; color: #212121;
  box-shadow: inset 0 -2px 5px rgba(0,0,0,0.2);
}
.bg-yellow { background: #FFCA28; }
.bg-blue { background: #29B6F6; }

.module-info { flex: 1; display: flex; flex-direction: column; }
.mod-name { font-size: 14px; font-weight: 900; color: #212121; margin-bottom: 2px; }
.mod-desc { font-size: 10px; color: #616161; font-weight: bold; line-height: 1.2;}

.mod-data { font-size: 14px; font-weight: bold; color: #212121; }
.box-data { background: #E0E0E0; padding: 4px 8px; border: 2px solid #424242; box-shadow: 2px 2px 0 #424242; }
.border-data { border-bottom: 2px dashed #424242; padding-bottom: 2px; }
</style>
