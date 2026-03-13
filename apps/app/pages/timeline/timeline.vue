<template>
  <view class="container">
    <view class="header">
      <view class="title">发现时间线</view>
      <view class="subtitle">你在这条路上走了多远</view>
    </view>

    <view v-if="loading" class="empty">加载中...</view>
    
    <view class="timeline" v-else-if="items.length > 0">
      <view class="timeline-item" v-for="(item, index) in items" :key="index">
        <view class="timeline-dot"></view>
        <view class="timeline-content" @click="goDetail(item)">
          <view class="time">{{ formatDate(item.created_date || item.created_at) }}</view>
          <view class="content-card">
             <view class="left">
               <text class="item-name">{{ item.chinese_name }}</text>
               <text class="item-desc">{{ item.features ? item.features.join(' ') : '无特征说明' }}</text>
             </view>
             <image class="thumb" :src="toImageUrl(item.image_path)" mode="aspectFill"></image>
          </view>
        </view>
      </view>
    </view>
    
    <view v-else class="empty">暂无发现记录</view>
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
    async loadTimeline() {
      try {
        const response = await uni.request({
          url: `${API_BASE}/species/search`,
          data: { keyword: 'a', limit: 50 }
        });
        const res = Array.isArray(response) ? response[1] : response;
        if (res?.data?.success) {
           const list = res.data.data.results || [];
           // sort by time desc
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
    formatDate(dateStr) {
      if (!dateStr) return '未知时间';
      const d = new Date(dateStr);
      return `${d.getMonth()+1}月${d.getDate()}日 ${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}`;
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
page { background: #FFFFFF; }
.container { padding-bottom: 30px; }
.header { padding: 30px 20px 20px; }
.title { font-size: 24px; font-weight: bold; color: #111827; }
.subtitle { font-size: 14px; color: #6B7280; margin-top: 5px; }

.timeline { padding: 20px; position: relative; }
.timeline::before {
  content: ''; position: absolute; left: 29px; top: 20px; bottom: 20px;
  width: 2px; background: #E5E7EB; border-radius: 2px;
}
.timeline-item { position: relative; padding-left: 30px; margin-bottom: 25px; }
.timeline-dot {
  position: absolute; left: 5px; top: 4px; width: 10px; height: 10px;
  background: #059669; border-radius: 50%; box-shadow: 0 0 0 4px #Edfaf3;
}
.time { font-size: 13px; color: #6B7280; font-weight: 500; margin-bottom: 8px; }
.content-card {
  background: #F9FAFB; padding: 15px; border-radius: 12px;
  display: flex; align-items: center; justify-content: space-between;
}
.left { flex: 1; margin-right: 15px; }
.item-name { font-size: 16px; font-weight: bold; color: #111827; display: block; margin-bottom: 4px; }
.item-desc { font-size: 12px; color: #6B7280; display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; overflow: hidden; }
.thumb { width: 50px; height: 50px; border-radius: 8px; background: #E5E7EB; flex-shrink: 0; }

.empty { padding: 50px; text-align: center; color: #9CA3AF; }
</style>
