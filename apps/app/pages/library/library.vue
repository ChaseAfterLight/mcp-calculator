<template>
  <view class="container">
    <view class="tabs">
      <view class="tab" :class="{active: currentTab === 'all'}" @click="switchTab('all')">全部</view>
      <view class="tab" :class="{active: currentTab === 'plant'}" @click="switchTab('plant')">植物</view>
      <view class="tab" :class="{active: currentTab === 'animal'}" @click="switchTab('animal')">动物</view>
      <view class="tab" :class="{active: currentTab === 'mineral'}" @click="switchTab('mineral')">矿物</view>
    </view>

    <!-- Search Section -->
    <view class="search-section">
      <view class="search-box">
        <text class="icon-search">🔍</text>
        <input class="search-input" v-model="searchQuery" placeholder="搜索图鉴..." @confirm="loadLibrary"/>
      </view>
    </view>

    <!-- List -->
    <view class="list">
       <view class="species-card" v-for="(item, index) in filteredList" :key="index" @click="goDetail(item)">
         <image class="card-img" :src="item.image_url" mode="aspectFill"></image>
         <view class="card-info">
           <text class="zh-name">{{ item.chinese_name }}</text>
           <text class="en-name">{{ item.latin_name }}</text>
           <view class="tags">
             <text class="tag">{{ getCategoryName(item.category) }}</text>
             <text class="rarity">{{ item.rarity }}★</text>
           </view>
         </view>
       </view>
       <view v-if="filteredList.length === 0" class="empty-state">
         <text>没有任何发现</text>
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
      const map = { plant: '植物', animal: '动物', mineral: '矿物' };
      return map[val] || val;
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
            image_url: this.toImageUrl(item.image_path)
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
page { background: #F3F4F6; }
.tabs {
  background: white; display: flex; padding: 0 10px;
  position: sticky; top: 0; z-index: 10;
}
.tab {
  flex: 1; text-align: center; padding: 15px 0; font-size: 15px;
  color: #6B7280; position: relative;
}
.tab.active {
  color: #059669; font-weight: bold;
}
.tab.active::after {
  content: ''; position: absolute; bottom: 0; left: 30%; right: 30%;
  height: 3px; background: #059669; border-radius: 3px;
}

.search-section { padding: 15px; }
.search-box {
  background: white; border-radius: 12px; padding: 10px 15px;
  display: flex; align-items: center;
}
.search-input { flex: 1; font-size: 14px; margin-left: 10px; }

.list { padding: 0 15px 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
.species-card {
  background: white; border-radius: 16px; overflow: hidden;
  box-shadow: 0 2px 10px rgba(0,0,0,0.03); display: flex; flex-direction: column;
}
.card-img { width: 100%; height: 120px; background: #E5E7EB; }
.card-info { padding: 12px; }
.zh-name { font-size: 15px; font-weight: bold; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;}
.en-name { font-size: 12px; color: #9CA3AF; margin-bottom: 8px; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;}
.tags { display: flex; justify-content: space-between; align-items: center; }
.tag { font-size: 10px; background: #F3F4F6; padding: 2px 6px; border-radius: 4px; }
.rarity { font-size: 12px; color: #FBBF24; font-weight: bold; }

.empty-state { grid-column: 1 / span 2; padding: 50px; text-align: center; color: #9CA3AF; }
</style>
