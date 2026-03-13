<template>
  <view class="container">
    <!-- Header -->
    <view class="header">
      <view class="welcome">
        <text class="title">探索大自然</text>
        <text class="subtitle">记录你身边的奇妙物种</text>
      </view>
      <view class="stats" v-if="userStats">
        <view class="stat-card">
          <text class="stat-num">{{ userStats.total_score || 0 }}</text>
          <text class="stat-label">总积分</text>
        </view>
        <view class="stat-card">
          <text class="stat-num">{{ userStats.discoveries_count || 0 }}</text>
          <text class="stat-label">已发现</text>
        </view>
      </view>
      <view class="stats loading" v-else>
        <text>正在同步数据...</text>
      </view>
    </view>

    <!-- Search Section -->
    <view class="search-section">
      <view class="search-box">
        <text class="icon-search">🔍</text>
        <input 
          class="search-input" 
          v-model="searchQuery" 
          placeholder="搜索中文名或特点..." 
          @confirm="handleSearch"
        />
        <view class="search-btn" @click="handleSearch">搜索</view>
      </view>
    </view>

    <!-- Actions -->
    <view class="action-grid">
      <view class="action-btn primary" @click="openRegisterModal">
        <text class="btn-icon">📝</text>
        <text class="btn-text">记录新物种</text>
      </view>
      <view class="action-btn secondary" @click="loadRecent">
        <text class="btn-icon">🔄</text>
        <text class="btn-text">刷新图鉴</text>
      </view>
    </view>

    <!-- Species List -->
    <view class="list-container">
      <view class="section-title">我的图鉴档案</view>
      
      <view class="species-list" v-if="speciesList.length > 0">
        <view class="species-card" v-for="(item, index) in speciesList" :key="index" @click="previewCard(item)">
          <view class="card-header">
            <view class="name-box">
              <text class="zh-name">{{ item.chinese_name }}</text>
              <text class="en-name">{{ item.latin_name }}</text>
            </view>
            <view class="rarity">
              <text v-for="n in item.rarity" :key="n" class="star">★</text>
            </view>
          </view>
          
          <view class="tags-box">
            <text class="tag category-tag">{{ getCategoryName(item.category) }}</text>
            <text class="tag protection-tag" v-if="item.protection_level">{{ item.protection_level }}</text>
          </view>
          
          <view class="features-box" v-if="item.features && item.features.length">
            <text class="feature" v-for="(feat, fIdx) in item.features" :key="fIdx">{{ feat }}</text>
          </view>
          
          <view class="fact-box" v-if="item.fun_fact">
            <text class="fact-icon">💡</text>
            <text class="fact-text">{{ item.fun_fact }}</text>
          </view>

          <view class="action-row">
            <view class="card-btn secondary-btn" @click.stop="generateCard(item)">重新生成卡片</view>
            <view class="card-btn" @click.stop="previewCard(item)">查看真实卡片</view>
          </view>
        </view>
      </view>
      
      <view class="empty-state" v-else>
        <text class="empty-icon">🌱</text>
        <text class="empty-text">暂无记录，快去探索吧</text>
      </view>
    </view>

    <!-- Register Modal -->
    <view class="modal-mask" v-if="showRegister" @click="showRegister = false">
      <view class="modal-content" @click.stop="">
        <view class="modal-header">
          <text class="modal-title">馃摑 记录新物种</text>
          <text class="close-icon" @click="showRegister = false">✕</text>
        </view>
        
        <scroll-view scroll-y class="form-container">
          <view class="form-item">
            <text class="label">中文名 *</text>
            <input class="input" v-model="form.chinese_name" placeholder="请输入物种名称" />
          </view>
          <view class="form-item">
            <text class="label">学名/拉丁名 *</text>
            <input class="input" v-model="form.latin_name" placeholder="对应的学名" />
          </view>
          <view class="form-item">
            <text class="label">分类 *</text>
            <picker @change="onCategoryChange" :value="catIndex" :range="categories" range-key="label">
              <view class="picker">{{ categories[catIndex].label }}</view>
            </picker>
          </view>
          <view class="form-item">
            <text class="label">显著特征（用逗号分隔） *</text>
            <input class="input" v-model="form.featuresStr" placeholder="如：黑色条纹, 体型小..." />
          </view>
          <view class="form-item">
            <text class="label">保护级别</text>
            <input class="input" v-model="form.protection_level" placeholder="(选填) 例如：国家一级" />
          </view>
          <view class="form-item">
            <text class="label">稀有度 (1-5)</text>
            <slider style="margin: 0" min="1" max="5" :value="form.rarity" @change="e => form.rarity = e.detail.value" show-value />
          </view>
          <view class="form-item">
            <text class="label">观察季节</text>
            <input class="input" v-model="form.observation_season" placeholder="(选填) 例如：春季" />
          </view>
          <view class="form-item">
            <text class="label">趣味冷知识</text>
            <textarea class="textarea" v-model="form.fun_fact" placeholder="(选填) 记录你发现的有趣现象..." />
          </view>
        </scroll-view>

        <view class="modal-footer">
          <view class="btn submit-btn" :class="{disabled: isSubmitting}" @click="submitRegister">
            {{ isSubmitting ? '保存中...' : '确认记录' }}
          </view>
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
      userId: 'default',
      userStats: null,
      searchQuery: '',
      speciesList: [],
      showRegister: false,
      isSubmitting: false,
      categories: [
        { value: 'plant', label: '植物 🌿' },
        { value: 'animal', label: '动物 🐾' },
        { value: 'mineral', label: '矿物 💎' }
      ],
      catIndex: 0,
      form: this.getInitialForm()
    }
  },
  onLoad() {
    this.fetchUserStats();
    this.loadRecent();
  },
  methods: {
    getInitialForm() {
      return {
        chinese_name: '',
        latin_name: '',
        featuresStr: '',
        protection_level: '',
        observation_season: '',
        fun_fact: '',
        rarity: 3
      }
    },
    getCategoryName(val) {
      const match = this.categories.find(c => c.value === val);
      return match ? match.label : val;
    },
    onCategoryChange(e) {
      this.catIndex = e.detail.value;
    },
    toImageUrl(imagePath) {
      if (!imagePath) return '';
      if (/^https?:\/\//.test(imagePath)) return imagePath;
      const normalized = String(imagePath).replace(/\\/g, '/').replace(/^\/+/, '');
      return `${SERVER_BASE}/${normalized}`;
    },
    async fetchUserStats() {
      try {
        const response = await uni.request({
          url: `${API_BASE}/users/${this.userId}/stats`,
          method: 'GET'
        });
        // Handle varying uni.request promise resolutions 
        const res = Array.isArray(response) ? response[1] : response;
        if (res && res.data && res.data.success) {
          this.userStats = res.data.data;
        }
      } catch (e) {
        console.error('Failed to fetch stats:', e);
      }
    },
    async loadRecent() {
      this.handleSearch(' ');
    },
    async handleSearch(query) {
      const kw = typeof query === 'string' && query.trim() !== '' ? query : this.searchQuery;
      // We must pass a min_length=1 keyword
      const actualKw = kw.trim() || 'a'; 
      
      try {
        const response = await uni.request({
          url: `${API_BASE}/species/search`,
          method: 'GET',
          data: {
            keyword: actualKw,
            limit: 20
          }
        });
        
        const res = Array.isArray(response) ? response[1] : response;
        
        if (res && res.data && res.data.success) {
          // The API directly returns an array of species objects via data.results
          const mcpRes = res.data.data.results || [];
          // Use map instead of map(metadata) since the objects are already formed
          this.speciesList = mcpRes.map(item => ({
            ...item,
            // Add fallback attributes since the search API doesn't provide them initially
            features: item.features || [],
            rarity: item.rarity || 3,
            fun_fact: item.fun_fact || '',
            protection_level: item.protection_level || '',
            image_path: item.image_path || '',
            image_url: this.toImageUrl(item.image_path || '')
          }));
        } else if (actualKw.trim() === 'a') {
          // If the gateway rejects or fails default search
          this.speciesList = [];
        } else {
             uni.showToast({ title: '搜索失败', icon: 'none' });
        }
      } catch (e) {
        console.error('Search failed:', e);
      }
    },
    openRegisterModal() {
      this.form = this.getInitialForm();
      this.catIndex = 0;
      this.showRegister = true;
    },
    async submitRegister() {
      if (!this.form.chinese_name || !this.form.latin_name || !this.form.featuresStr) {
        uni.showToast({ title: '请填写带*的必填项', icon: 'none' });
        return;
      }
      if (this.isSubmitting) return;
      this.isSubmitting = true;

      const features = this.form.featuresStr.split(',').map(s => s.trim()).filter(Boolean);
      const payload = {
        chinese_name: this.form.chinese_name,
        latin_name: this.form.latin_name,
        features: features.length > 0 ? features : ['无明显特征'],
        category: this.categories[this.catIndex].value,
        protection_level: this.form.protection_level,
        observation_season: this.form.observation_season,
        fun_fact: this.form.fun_fact,
        rarity: this.form.rarity,
        user_id: this.userId
      };

      try {
        const response = await uni.request({
          url: `${API_BASE}/species/register`,
          method: 'POST',
          data: payload
        });
        const res = Array.isArray(response) ? response[1] : response;
        
        if (res && res.data && res.data.success) {
          uni.showToast({ title: '记录成功', icon: 'success' });
          this.showRegister = false;
          this.fetchUserStats();
          this.loadRecent();
          // generate card
          const registerResult = res.data.data || {};
          this.generateCard({
            ...payload,
            card_id: registerResult.card_id || ''
          });
        } else {
          uni.showToast({ 
            title: res?.data?.error?.message || '记录失败', 
            icon: 'none' 
          });
        }
      } catch (e) {
        uni.showToast({ title: '网络错误', icon: 'none' });
      } finally {
        this.isSubmitting = false;
      }
    },
    async generateCard(species) {
      uni.showLoading({ title: '生成卡片中...' });
      try {
        const response = await uni.request({
          url: `${API_BASE}/species/generate-card`,
          method: 'POST',
          data: {
            card_id: species.card_id || "",
            chinese_name: species.chinese_name,
            latin_name: species.latin_name,
            features: species.features || ['未知'],
            category: species.category || "plant",
            habitat: species.habitat || "",
            observation_season: species.observation_season || "",
            protection_level: species.protection_level || "",
            fun_fact: species.fun_fact || "",
            rarity: species.rarity || 3
          }
        });
        const res = Array.isArray(response) ? response[1] : response;
         uni.hideLoading();
        if (res && res.data && res.data.success) {
          const result = res.data.data || {};
          species.card_id = result.card_id || species.card_id || '';
          const imagePath = result.image_path || '';
          const imageUrl = this.toImageUrl(imagePath);
          species.image_path = imagePath;
          species.image_url = imageUrl;
          uni.showToast({ title: '卡片生成成功', icon: 'success' });
          if (imageUrl) {
            this.previewCard(species);
          } else {
            this.loadRecent();
          }
        } else {
          uni.showToast({ title: '卡片生成失败', icon: 'none' });
        }
      } catch (e) {
        uni.hideLoading();
        uni.showToast({ title: '网络错误', icon: 'none' });
      }
    },
    previewCard(species) {
      const imageUrl = species?.image_url || this.toImageUrl(species?.image_path || '');
      if (!imageUrl) {
        uni.showToast({ title: '还没有卡片，先点击“重新生成卡片”吧', icon: 'none' });
        return;
      }
      uni.previewImage({
        current: imageUrl,
        urls: [imageUrl]
      });
    }
  }
}
</script>

<style lang="scss">
page {
  background-color: #F3F4F6;
}
.container {
  padding-bottom: 40px;
}

/* Header */
.header {
  background: linear-gradient(135deg, #059669 0%, #10B981 100%);
  padding: 40px 20px 30px;
  border-bottom-left-radius: 30px;
  border-bottom-right-radius: 30px;
  color: white;
  box-shadow: 0 4px 15px rgba(5, 150, 105, 0.3);
}
.welcome {
  margin-bottom: 25px;
}
.title {
  font-size: 28px;
  font-weight: 800;
  display: block;
  margin-bottom: 5px;
}
.subtitle {
  font-size: 14px;
  opacity: 0.9;
}
.stats {
  display: flex;
  justify-content: space-between;
  gap: 15px;
}
.loading {
  opacity: 0.7;
  font-size: 14px;
}
.stat-card {
  background: rgba(255,255,255,0.15);
  padding: 15px 20px;
  border-radius: 16px;
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(255,255,255,0.2);
}
.stat-num {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 4px;
}
.stat-label {
  font-size: 12px;
  opacity: 0.8;
}

/* Search */
.search-section {
  padding: 0 20px;
  margin-top: -24px;
}
.search-box {
  background: white;
  border-radius: 16px;
  padding: 10px 15px;
  display: flex;
  align-items: center;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}
.icon-search {
  margin-right: 10px;
  font-size: 16px;
}
.search-input {
  flex: 1;
  font-size: 15px;
  height: 36px;
}
.search-btn {
  background: #Edfaf3;
  color: #059669;
  padding: 8px 16px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
}

/* Actions */
.action-grid {
  display: flex;
  padding: 24px 20px 10px;
  gap: 15px;
}
.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 14px;
  border-radius: 16px;
  font-weight: 600;
  font-size: 15px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.action-btn.primary {
  background: #059669;
  color: white;
}
.action-btn.secondary {
  background: white;
  color: #374151;
}
.btn-icon {
  margin-right: 8px;
  font-size: 18px;
}

/* List */
.list-container {
  padding: 15px 20px;
}
.section-title {
  font-size: 18px;
  font-weight: 700;
  color: #1F2937;
  margin-bottom: 16px;
}
.species-card {
  background: white;
  border-radius: 20px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.03);
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}
.name-box {
  display: flex;
  flex-direction: column;
}
.zh-name {
  font-size: 18px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 4px;
}
.en-name {
  font-size: 13px;
  color: #6B7280;
  font-style: italic;
}
.star {
  color: #FBBF24;
  font-size: 14px;
  margin-left: 2px;
}
.tags-box {
  display: flex;
  gap: 8px;
  margin-bottom: 15px;
  flex-wrap: wrap;
}
.tag {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 8px;
  font-weight: 500;
}
.category-tag {
  background: #Eef2ff;
  color: #4F46E5;
}
.protection-tag {
  background: #Fef2f2;
  color: #DC2626;
}
.features-box {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 15px;
}
.feature {
  font-size: 12px;
  color: #4B5563;
  background: #F3F4F6;
  padding: 4px 10px;
  border-radius: 20px;
}
.fact-box {
  background: #Fffbeb;
  padding: 12px;
  border-radius: 12px;
  display: flex;
  align-items: flex-start;
  margin-bottom: 15px;
}
.fact-icon {
  margin-right: 8px;
  font-size: 16px;
}
.fact-text {
  font-size: 13px;
  line-height: 1.5;
  color: #92400e;
}
.action-row {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  border-top: 1px solid #F3F4F6;
  padding-top: 12px;
}
.card-btn {
  font-size: 13px;
  color: #059669;
  font-weight: 600;
}
.card-btn.secondary-btn {
  color: #6B7280;
}
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  opacity: 0.5;
}
.empty-icon {
  font-size: 40px;
  margin-bottom: 10px;
}

/* Modal */
.modal-mask {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  z-index: 100;
  display: flex;
  align-items: flex-end;
}
.modal-content {
  background: white;
  border-top-left-radius: 24px;
  border-top-right-radius: 24px;
  width: 100%;
  height: 85vh;
  display: flex;
  flex-direction: column;
}
.modal-header {
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #F3F4F6;
}
.modal-title {
  font-size: 18px;
  font-weight: 700;
}
.close-icon {
  font-size: 20px;
  color: #9CA3AF;
  padding: 5px;
}
.form-container {
  flex: 1;
  padding: 20px;
}
.form-item {
  margin-bottom: 20px;
}
.label {
  display: block;
  font-size: 14px;
  color: #374151;
  margin-bottom: 8px;
  font-weight: 500;
}
.input, .picker, .textarea {
  background: #F9FAFB;
  border: 1px solid #E5E7EB;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 15px;
}
.textarea {
  width: 90%;
  min-height: 80px;
}
.modal-footer {
  padding: 20px;
  border-top: 1px solid #F3F4F6;
}
.submit-btn {
  background: #059669;
  color: white;
  text-align: center;
  padding: 16px;
  border-radius: 16px;
  font-size: 16px;
  font-weight: 600;
}
.submit-btn.disabled {
  opacity: 0.6;
}
</style>


