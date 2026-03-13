<template>
  <view class="device-wrapper">
    <!-- 分类标签：类似硬件档位开关 -->
    <view class="hardware-tabs">
      <view class="tab-btn" :class="{ 'tab-active': currentTab === 'all' }" @click="switchTab('all')">
        <text>全部</text>
      </view>
      <view class="tab-btn" :class="{ 'tab-active': currentTab === 'plant' }" @click="switchTab('plant')">
        <view class="led-indicator" :class="{ 'led-on': currentTab === 'plant' }"></view>
        <text>草本</text>
      </view>
      <view class="tab-btn" :class="{ 'tab-active': currentTab === 'animal' }" @click="switchTab('animal')">
        <view class="led-indicator" :class="{ 'led-on': currentTab === 'animal' }"></view>
        <text>野生</text>
      </view>
      <view class="tab-btn" :class="{ 'tab-active': currentTab === 'mineral' }" @click="switchTab('mineral')">
        <view class="led-indicator" :class="{ 'led-on': currentTab === 'mineral' }"></view>
        <text>岩地</text>
      </view>
    </view>

    <!-- 搜索区：终端输入框 -->
    <view class="terminal-search">
      <text class="prompt-char">></text>
      <input class="retro-input" v-model="searchQuery" placeholder="请输入查询指令..." placeholder-style="color: rgba(155,188,15,0.5);" @confirm="loadLibrary"/>
      <view class="search-btn" @click="loadLibrary">检索</view>
    </view>

    <!-- 列表区：复古屏幕 -->
    <view class="screen-bezel">
      <view class="lcd-list">
        <view class="scanline"></view>

        <scroll-view scroll-y class="list-scroll">
          <view class="grid-list" v-if="filteredList.length > 0">
             <view class="image-tile" v-for="(item, index) in filteredList" :key="index" @click="goDetail(item)">
               <image class="tile-img" :src="item.image_url" mode="aspectFill"></image>
               <view class="tile-overlay">
                 <text class="tile-name">{{ item.chinese_name }}</text>
               </view>
             </view>
          </view>
          
          <view v-else class="empty-state">
            <text class="blinking-cursor">404 // 找不到相关数据</text>
          </view>
        </scroll-view>

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
      currentTab: 'all',
      searchQuery: '',
      speciesList: []
    }
  },
  computed: {
    filteredList() {
      if (this.currentTab === 'all') return this.speciesList;
      return this.speciesList.filter(item => item.category === this.currentTab);
    }
  },
  onShow() {
    this.loadLibrary();
  },
  onPullDownRefresh() {
    this.loadLibrary().then(() => {
      uni.stopPullDownRefresh();
    });
  },
  methods: {
    switchTab(tab) {
      this.currentTab = tab;
    },
    getCategoryName(val) {
      const map = { plant: '草本', animal: '野生', mineral: '岩地' };
      return map[val] || val || '未知';
    },
    toImageUrl(imagePath) {
      if (!imagePath) return '';
      if (/^https?:\/\//.test(imagePath)) return imagePath;
      const normalized = String(imagePath).replace(/\\/g, '/').replace(/^\/+/, '');
      return `${SERVER_BASE}/${normalized}`;
    },
    async loadLibrary() {
      const kw = this.searchQuery.trim() || 'a'; 
      try {
        const response = await uni.request({
          url: `${API_BASE}/species/search`,
          data: { keyword: kw, limit: 50 }
        });
        const res = Array.isArray(response) ? response[1] : response;
        if (res?.data?.success) {
          const mcpRes = res.data.data.results || [];
          this.speciesList = mcpRes.map(item => ({
            ...item,
            image_url: this.toImageUrl(item.source_image_path || item.image_path)
          }));
        }
      } catch (e) {
        console.error(e);
      }
    },
    goDetail(item) {
      if (!item || !item.card_id) return;
      uni.navigateTo({
        url: `/pages/detail/detail?card_id=${encodeURIComponent(item.card_id)}`
      })
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

.glitch-title { 
  font-size: 22px; font-weight: bold; color: #FFF; 
  text-shadow: 2px 2px 0 #212121;
}

/* 物理开关选项卡 */
.hardware-tabs {
  display: flex; gap: 10px; padding: 20px;
}
.tab-btn {
  flex: 1; padding: 8px 0; background: #E0E0E0;
  border: 2px solid #424242; border-radius: 6px;
  box-shadow: 0 4px 0 #424242; text-align: center;
  font-size: 12px; font-weight: bold; color: #424242;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.tab-active {
  background: #BDBDBD;
  transform: translateY(4px); box-shadow: 0 0 0 #424242;
  color: #212121;
}
.led-indicator {
  width: 6px; height: 6px; border-radius: 50%; background: #424242; margin-bottom: 4px;
  border: 1px solid #000;
}
.led-on { background: #66BB6A; box-shadow: 0 0 5px #66BB6A; }

/* 终端搜索框 */
.terminal-search {
  margin: 0 20px 20px;
  background: #0F380F; border: 2px solid #212121; border-radius: 8px;
  padding: 10px 15px; display: flex; align-items: center;
  box-shadow: inset 0 0 10px rgba(0,0,0,0.8);
}
.prompt-char { color: #9BBC0F; font-weight: bold; margin-right: 10px; font-size: 16px; }
.retro-input { flex: 1; color: #9BBC0F; font-size: 14px; font-weight: bold; }
.search-btn {
  background: #9BBC0F; color: #0F380F; padding: 4px 10px; font-size: 12px; font-weight: bold;
  border-radius: 4px; border: 1px solid #306230;
}
.search-btn:active { background: #8BAC0F; }

/* 屏幕区域 */
.screen-bezel {
  background-color: #E0E0E0;
  margin: 0 20px; padding: 15px;
  border-radius: 12px; 
  box-shadow: inset 0 2px 5px rgba(0,0,0,0.2), 0 5px 10px rgba(0,0,0,0.3);
  border: 2px solid #757575;
}

.lcd-list {
  background-color: #9BBC0F;
  border-radius: 8px;
  padding: 10px;
  box-shadow: inset 0 0 10px rgba(0,0,0,0.3);
  position: relative;
  overflow: hidden;
  height: calc(100vh - 350px); /* 动态高度 */
}

.list-scroll { height: 100%; }

.scanline {
  position: absolute; top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.04) 50%);
  background-size: 100% 4px; pointer-events: none; z-index: 10;
}

.grid-list {
  display: grid; grid-template-columns: 1fr 1fr; gap: 10px; position: relative; z-index: 1;
}

.image-tile {
  position: relative;
  height: 140px;
  border: 2px solid #0F380F;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 2px 2px 0 #0F380F;
  background: #000;
}
.image-tile:active { transform: translate(2px, 2px); box-shadow: 0 0 0 #0F380F; }

.tile-img {
  width: 100%;
  height: 100%;
  display: block;
  opacity: 0.88;
  filter: grayscale(12%) contrast(1.05);
}

.tile-overlay {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 8px;
  background: linear-gradient(to top, rgba(15, 56, 15, 0.88), rgba(15, 56, 15, 0));
}

.tile-name {
  display: block;
  color: #fff;
  font-size: 12px;
  font-weight: 900;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-state { padding: 50px 0; text-align: center; color: #0F380F; font-size: 14px; font-weight: bold; position: relative; z-index:1; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
.blinking-cursor::after { content: '_'; animation: blink 1s step-end infinite; }
</style>
