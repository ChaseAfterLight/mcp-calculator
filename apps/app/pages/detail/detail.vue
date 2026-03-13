<template>
  <view class="container">
    <view class="header" v-if="species">
      <view class="title-section">
        <text class="zh-name">{{ species.chinese_name }}</text>
        <text class="en-name">{{ species.latin_name }}</text>
      </view>
      <view class="rarity">
        <text v-for="n in (species.rarity || 3)" :key="n" class="star">★</text>
      </view>
    </view>

    <!-- Image Preview -->
    <view class="image-section" v-if="species && species.image_url">
      <image class="cover-image" :src="species.image_url" mode="aspectFill" @click="previewImage"></image>
    </view>
    
    <view class="content-section" v-if="species">
      <!-- Tags -->
      <view class="tags-row">
        <text class="tag category-tag">{{ getCategoryName(species.category) }}</text>
        <text class="tag protection-tag" v-if="species.protection_level">{{ species.protection_level }}</text>
      </view>

      <!-- Basic Info -->
      <view class="info-group">
        <view class="info-item" v-if="species.habitat">
          <text class="label">栖息地</text>
          <text class="val">{{ species.habitat }}</text>
        </view>
        <view class="info-item" v-if="species.observation_season">
          <text class="label">观察季节</text>
          <text class="val">{{ species.observation_season }}</text>
        </view>
        <view class="info-item" v-if="species.created_at">
          <text class="label">发现时间</text>
          <text class="val">{{ formatDate(species.created_at) }}</text>
        </view>
      </view>

      <!-- Features -->
      <view class="section">
        <text class="section-title">显著特征</text>
        <view class="features-box">
          <text class="feature" v-for="(feat, fIdx) in species.features" :key="fIdx">{{ feat }}</text>
        </view>
      </view>

      <!-- Fun Fact -->
      <view class="section" v-if="species.fun_fact">
        <text class="section-title">趣味知识</text>
        <view class="fact-box">
          <text class="fact-icon">💡</text>
          <text class="fact-text">{{ species.fun_fact }}</text>
        </view>
      </view>

      <view class="section" v-if="species.card_image_url">
        <text class="section-title">生成卡片</text>
        <view class="card-preview-box" @click="previewCardImage">
          <image class="card-preview-image" :src="species.card_image_url" mode="widthFix"></image>
        </view>
        <view class="inline-action" @click="previewCardImage">查看生成卡片</view>
      </view>

      <view class="section" v-if="species.author || species.license || species.faves_count">
        <text class="section-title">图片来源</text>
        <view class="info-group source-group">
          <view class="info-item" v-if="species.author">
            <text class="label">作者</text>
            <text class="val source-val">{{ species.author }}</text>
          </view>
          <view class="info-item" v-if="species.license">
            <text class="label">许可证</text>
            <text class="val source-val">{{ formatLicense(species.license) }}</text>
          </view>
          <view class="info-item" v-if="species.faves_count">
            <text class="label">收藏数</text>
            <text class="val">{{ species.faves_count }}</text>
          </view>
          <view class="info-item" v-if="species.source_page_url">
            <text class="label">来源页面</text>
            <text class="val source-link" @click="openSourcePage">{{ species.source_page_url }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- Actions -->
    <view class="bottom-actions" v-if="species">
      <view class="btn primary-btn" @click="toShare">分享 / 发送邮件</view>
      <view class="btn secondary-btn" @click="regenerateCard">重新生成卡片</view>
    </view>

    <view v-if="!species && !loading" class="empty-state">
      <text>加载失败或物种不存在</text>
    </view>
  </view>
</template>

<script>
const API_BASE = 'http://127.0.0.1:8000/api';
const SERVER_BASE = API_BASE.replace(/\/api$/, '');

export default {
  data() {
    return {
      species: null,
      loading: true,
      cardId: ''
    }
  },
  onLoad(options) {
    if (options.card_id) {
      this.cardId = decodeURIComponent(options.card_id);
      this.loadDetail();
      return;
    }

    if (options.data) {
      try {
        this.species = this.normalizeSpecies(JSON.parse(decodeURIComponent(options.data)));
        this.cardId = this.species.card_id || '';
      } catch (e) {
        console.error(e);
      }
    }

    this.loading = false;
  },
  methods: {
    async loadDetail() {
      try {
        const response = await uni.request({
          url: `${API_BASE}/species/${encodeURIComponent(this.cardId)}`,
          method: 'GET'
        });
        const res = Array.isArray(response) ? response[1] : response;
        if (res?.data?.success) {
          this.species = this.normalizeSpecies(res.data.data || {});
        } else {
          this.species = null;
        }
      } catch (e) {
        console.error(e);
        this.species = null;
      } finally {
        this.loading = false;
      }
    },
    normalizeSpecies(raw) {
      const species = raw || {};
      const displayImagePath = species.source_image_path || species.image_path || '';
      return {
        ...species,
        features: Array.isArray(species.features) ? species.features : [],
        image_url: this.toImageUrl(displayImagePath || species.image_url || ''),
        card_image_url: this.toImageUrl(species.card_image_path || species.image_path || ''),
        created_at: species.created_at || species.generated_at || ''
      };
    },
    getCategoryName(val) {
      const map = { plant: '植物 🌿', animal: '动物 🐾', mineral: '矿物 💎' };
      return map[val] || val;
    },
    formatDate(dateStr) {
      if (!dateStr) return '未知';
      return new Date(dateStr).toLocaleString();
    },
    formatLicense(license) {
      const map = {
        'cc-by': 'CC BY',
        'cc-by-nc': 'CC BY-NC',
        'cc-by-sa': 'CC BY-SA',
        'cc-by-nd': 'CC BY-ND',
        'cc0': 'CC0'
      };
      return map[String(license).toLowerCase()] || license;
    },
    previewImage() {
      if (this.species && this.species.image_url) {
        uni.previewImage({ urls: [this.species.image_url] });
      }
    },
    previewCardImage() {
      if (this.species && this.species.card_image_url) {
        uni.previewImage({ urls: [this.species.card_image_url] });
      }
    },
    openSourcePage() {
      if (!this.species?.source_page_url) return;
      // eslint-disable-next-line no-undef
      if (typeof plus !== 'undefined' && plus.runtime?.openURL) {
        plus.runtime.openURL(this.species.source_page_url);
        return;
      }
      uni.setClipboardData({
        data: this.species.source_page_url,
        success: () => uni.showToast({ title: '链接已复制', icon: 'none' })
      });
    },
    toShare() {
      uni.navigateTo({
        url: `/pages/share/share?card_id=${this.cardId}&chinese_name=${encodeURIComponent(this.species.chinese_name)}`
      });
    },
    async regenerateCard() {
      uni.showLoading({ title: '重新生成中...' });
      try {
        const response = await uni.request({
          url: `${API_BASE}/species/generate-card`,
          method: 'POST',
          data: {
            card_id: this.cardId,
            chinese_name: this.species.chinese_name,
            latin_name: this.species.latin_name,
            features: this.species.features || ['未知'],
            category: this.species.category || "plant",
            habitat: this.species.habitat || "",
            observation_season: this.species.observation_season || "",
            protection_level: this.species.protection_level || "",
            fun_fact: this.species.fun_fact || "",
            rarity: this.species.rarity || 3
          }
        });
        const res = Array.isArray(response) ? response[1] : response;
        uni.hideLoading();
        if (res && res.data && res.data.success) {
          await this.loadDetail();
          uni.showToast({ title: '卡片已更新', icon: 'success' });
        } else {
          uni.showToast({ title: '生成失败', icon: 'none' });
        }
      } catch (e) {
        uni.hideLoading();
        uni.showToast({ title: '网络错误', icon: 'none' });
      }
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
.container { padding-bottom: 90px; }

.header {
  background: white;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}
.title-section { display: flex; flex-direction: column; }
.zh-name { font-size: 24px; font-weight: bold; color: #111827; }
.en-name { font-size: 14px; color: #6B7280; font-style: italic; margin-top: 4px; }
.star { color: #FBBF24; font-size: 16px; margin-left: 2px; }

.image-section {
  width: 100%;
  height: 250px;
  background: #E5E7EB;
}
.cover-image {
  width: 100%;
  height: 100%;
}

.content-section {
  padding: 20px;
}
.tags-row {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}
.tag {
  font-size: 12px; padding: 4px 12px; border-radius: 8px; font-weight: 500;
}
.category-tag { background: #Eef2ff; color: #4F46E5; }
.protection-tag { background: #Fef2f2; color: #DC2626; }

.info-group {
  background: white; border-radius: 12px; padding: 15px; margin-bottom: 20px;
}
.source-group {
  padding: 0;
  margin-bottom: 0;
}
.info-item {
  display: flex; justify-content: space-between; margin-bottom: 10px;
  gap: 12px;
}
.info-item:last-child { margin-bottom: 0; }
.label { color: #6B7280; font-size: 14px; }
.val { color: #111827; font-size: 14px; font-weight: 500; }
.source-val {
  flex: 1;
  text-align: right;
  word-break: break-all;
}
.source-link {
  flex: 1;
  text-align: right;
  color: #2563EB;
  word-break: break-all;
}

.section {
  background: white; border-radius: 12px; padding: 15px; margin-bottom: 20px;
}
.section-title { font-size: 16px; font-weight: bold; margin-bottom: 12px; display: block; }
.features-box { display: flex; flex-wrap: wrap; gap: 8px; }
.feature { background: #F3F4F6; color: #4B5563; padding: 6px 12px; border-radius: 20px; font-size: 13px; }

.fact-box {
  background: #Fffbeb; padding: 12px; border-radius: 12px; display: flex; align-items: flex-start;
}
.fact-icon { margin-right: 8px; }
.fact-text { font-size: 14px; color: #92400e; line-height: 1.5; }
.card-preview-box {
  background: #F9FAFB;
  border-radius: 12px;
  overflow: hidden;
}
.card-preview-image {
  width: 100%;
  display: block;
}
.inline-action {
  margin-top: 12px;
  text-align: center;
  color: #059669;
  font-size: 14px;
  font-weight: 600;
}

.bottom-actions {
  position: fixed; bottom: 0; left: 0; right: 0;
  background: white; padding: 15px 20px;
  display: flex; gap: 15px;
  box-shadow: 0 -4px 10px rgba(0,0,0,0.05);
  padding-bottom: env(safe-area-inset-bottom);
}
.btn {
  flex: 1; text-align: center; padding: 12px; border-radius: 12px; font-weight: 600; font-size: 15px;
}
.primary-btn { background: #059669; color: white; }
.secondary-btn { background: #F3F4F6; color: #374151; }

.empty-state { padding: 50px; text-align: center; color: #9CA3AF; }
</style>
