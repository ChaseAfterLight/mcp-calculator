<template>
  <view class="device-wrapper">
    <!-- Header -->
    <view class="device-header">
       <view class="screen-btn" @click="goBack">
          <text>◀ 返回</text>
       </view>
       <text class="glitch-title">时光日志 // TIMELINE</text>
    </view>

    <!-- 终端风格列表区域 -->
    <view class="terminal-bezel">
      <view class="terminal-screen">
        <view class="scanline"></view>
        <view class="terminal-header">
          <text>> 系统引导中...</text>
          <text>> 正在访问历史扫描记录...</text>
        </view>

        <view v-if="loading" class="empty-term">
          <text class="blinking-cursor">读取中_</text>
        </view>
        
        <scroll-view scroll-y class="term-scroll" v-else-if="items.length > 0">
          <view class="term-timeline">
            <view class="term-item" v-for="(item, index) in items" :key="index" @click="goDetail(item)">
              <view class="term-time-col">
                <text class="t-date">{{ formatTerminalDate(item.created_date || item.created_at) }}</text>
                <view class="t-line"></view>
                <view class="t-node"></view>
              </view>
              
              <view class="term-content-col">
                <view class="doc-card">
                  <view class="doc-header">
                    <text class="doc-id">档案编号: {{ (item.card_id || '').slice(-6).toUpperCase() || 'DATA' }}</text>
                  </view>
                  <view class="doc-body">
                    <view class="doc-text">
                      <text class="doc-title">{{ item.chinese_name }}</text>
                      <text class="doc-desc">{{ Array.isArray(item.features) ? item.features.join('; ') : (item.features || 'NO_DATA') }}</text>
                    </view>
                    <view class="doc-img-box">
                      <image class="doc-img" :src="toImageUrl(item.image_path)" mode="aspectFill"></image>
                      <view class="doc-overlay"></view>
                    </view>
                  </view>
                </view>
              </view>
            </view>
          </view>
        </scroll-view>
        
        <view v-else class="empty-term">
          <text class="blinking-cursor">未找到历史记录_</text>
        </view>

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
      items: [],
      loading: true
    }
  },
  onLoad() {
    this.loadTimeline();
  },
  methods: {
    goBack() {
      uni.navigateBack();
    },
    async loadTimeline() {
      try {
        const response = await uni.request({
          url: `${API_BASE}/species/search`,
          data: { keyword: 'a', limit: 50 }
        });
        const res = Array.isArray(response) ? response[1] : response;
        if (res?.data?.success) {
           const list = res.data.data.results || [];
           list.sort((a,b) => {
             const tA = new Date(a.created_date || a.created_at || 0).getTime();
             const tB = new Date(b.created_date || b.created_at || 0).getTime();
             return tB - tA;
           });
           this.items = list;
        }
      } catch (e) {} finally {
        this.loading = false;
      }
    },
    formatTerminalDate(dateStr) {
      if (!dateStr) return '00/00';
      const d = new Date(dateStr);
      return `${String(d.getMonth()+1).padStart(2,'0')}/${String(d.getDate()).padStart(2,'0')}\n${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
    },
    toImageUrl(imagePath) {
      if (!imagePath) return '';
      if (/^https?:\/\//.test(imagePath)) return imagePath;
      const normalized = String(imagePath).replace(/\\/g, '/').replace(/^\/+/, '');
      return `${SERVER_BASE}/${normalized}`;
    },
    goDetail(item) {
      if (!item || !item.card_id) return;
      uni.navigateTo({
        url: `/pages/detail/detail?card_id=${encodeURIComponent(item.card_id)}`
      });
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
  padding: 40px 20px 20px;
  background: linear-gradient(180deg, #E53935 0%, #D32F2F 100%);
  border-bottom: 3px solid #B71C1C;
  display: flex; align-items: center; gap: 15px;
}

.screen-btn {
  background: #212121; border: 2px solid #000; padding: 4px 8px; border-radius: 4px;
  color: #FFF; font-size: 10px; font-weight: bold; box-shadow: 0 2px 0 #000;
}
.screen-btn:active { transform: translateY(2px); box-shadow: 0 0 0 #000; }

.glitch-title { font-size: 20px; font-weight: bold; color: #FFF; }

.terminal-bezel {
  background-color: #E0E0E0; margin: 20px; padding: 15px;
  border-radius: 12px; border: 2px solid #757575;
  box-shadow: inset 0 2px 5px rgba(0,0,0,0.2), 0 5px 10px rgba(0,0,0,0.3);
}

.terminal-screen {
  background-color: #051405; /* 更深的纯正黑色底，增加对比度 */
  border-radius: 8px; padding: 15px;
  box-shadow: inset 0 0 10px rgba(0,0,0,1);
  position: relative; overflow: hidden;
  height: calc(100vh - 200px);
}

.scanline {
  position: absolute; top: 0; left: 0; right: 0; bottom: 0;
  /* 减轻扫描线的透明度，避免遮挡文字 */
  background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.05) 50%);
  background-size: 100% 4px; pointer-events: none; z-index: 10;
}

.terminal-header {
  display: flex; flex-direction: column; gap: 4px;
  margin-bottom: 15px; border-bottom: 1px dashed #306230; padding-bottom: 10px;
  position: relative; z-index: 1;
}
.terminal-header text { color: #66FF00; font-size: 12px; font-weight: bold; }

.term-scroll { height: calc(100% - 40px); position: relative; z-index: 1; }

.term-timeline { display: flex; flex-direction: column; padding-bottom: 20px; }

.term-item { display: flex; margin-bottom: 20px; }

.term-time-col { 
  width: 50px; display: flex; flex-direction: column; align-items: center; position: relative;
  margin-right: 15px;
}
.t-date { color: #66FF00; font-size: 11px; font-weight: bold; text-align: center; white-space: pre-wrap; margin-bottom: 5px; }
.t-node { width: 10px; height: 10px; background: #66FF00; border-radius: 50%; box-shadow: 0 0 5px #66FF00; z-index: 2; }
.t-line { position: absolute; top: 35px; bottom: -35px; left: 50%; transform: translateX(-50%); width: 2px; background: rgba(102,255,0,0.3); z-index: 1; }

.term-content-col { flex: 1; }
.doc-card {
  border: 1px solid #306230; background: rgba(48,98,48,0.2); border-radius: 4px;
  padding: 8px; position: relative;
}
.doc-card:active { background: rgba(48,98,48,0.4); }

.doc-header { border-bottom: 1px solid #306230; padding-bottom: 4px; margin-bottom: 8px; }
.doc-id { color: #66FF00; font-size: 11px; font-weight: bold; }

.doc-body { display: flex; gap: 10px; justify-content: space-between; align-items: flex-start; }
.doc-text { flex: 1; display: flex; flex-direction: column; }
.doc-title { color: #FFF; font-size: 16px; font-weight: bold; margin-bottom: 4px; }
.doc-desc { color: rgba(255,255,255,0.8); font-size: 11px; display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; overflow: hidden; line-height: 1.4;}

.doc-img-box { width: 50px; height: 50px; border: 1px solid #306230; position: relative; background: #000; flex-shrink: 0; display: flex; align-items: center; justify-content: center; overflow: hidden; }
.doc-img { width: 100%; height: 100%; opacity: 1; }
.doc-overlay { position: absolute; top:0; left:0; width:100%; height:100%; background: linear-gradient(rgba(102,255,0,0.1), transparent); pointer-events: none;}

.empty-term { padding: 40px; text-align: center; color: #66FF00; font-weight: bold; font-size: 14px; position: relative; z-index: 1;}
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
.blinking-cursor::after { content: '_'; animation: blink 1s step-end infinite; }
</style>
